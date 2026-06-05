# Revisão Crítica — Análise RAG NovaTech

---

## Seção 1 — Desafios por tipo de fonte

### Risco não considerado: openpyxl não executa fórmulas Excel

A recomendação de "exportar valores calculados via script Python/openpyxl" está tecnicamente errada. O openpyxl lê o valor *em cache* da última vez que o arquivo foi salvo no Excel — não recalcula fórmulas. Se a planilha contiver fórmulas com dependências externas (VLOOKUP em outra aba, Power Query, fórmulas voláteis como `AGORA()`), o valor em cache pode estar desatualizado ou ausente. A alternativa correta seria xlwings (requer Excel instalado) ou exportação via Microsoft 365 API. Esse gap pode comprometer todas as 50 planilhas.

### Risco não considerado: custo e prazo de aprovação do Azure Document Intelligence

O Azure Document Intelligence é citado como solução principal para PDFs complexos e OCR, mas a análise trata o provisionamento como trivial. Em empresas com processo de procurement/TI, a aprovação para contratar um serviço Azure pode levar 2–6 semanas. O plano da Semana 1 assume acesso imediato.

### Estimativa otimista: resolução de links Confluence

A estratégia diz "resolver links internos e incluir título+resumo da página vinculada como contexto pai". Isso pressupõe que todas as páginas vinculadas existem, são acessíveis pelo token de API usado, e têm conteúdo textual. Na prática:

- Páginas deletadas ou movidas retornam 404
- Restrições de permissão por espaço são comuns
- Macros como `{include:pageId=...}` criam dependências recursivas

A análise cita monitorar `links_resolvidos=[]`, mas não endereça o que fazer com os chunks que dependem criticamente dessas páginas.

---

## Seção 2 — Estimativa de tokens

### Premissa P1 — 30% de PDFs escaneados é provavelmente subestimado

A justificativa é "cenário diz 'alguns documentos escaneados' — conservador em 30%". Em empresas de logística com documentação de décadas, é comum que 50–70% do acervo sejam escaneados (apólices, contratos de frete, tabelas antigas digitalizadas). Se for 50%, a estimativa central de tokens passa de 4,1M para ~4,6M — um impacto de ~12% no tamanho do índice e custo de embedding.

### Premissa: 10 páginas por PDF (flat para todos os 800 documentos)

Essa é a premissa mais frágil da tabela. PDFs de logística incluem tabelas de frete por CEP (pode ter 100+ páginas), manuais operacionais, contratos. Sem uma amostragem real da distribuição de tamanhos, o intervalo min–max da Tabela B é pouco confiável. Uma única tabela de frete com 200 páginas desloca mais a estimativa do que toda a variância de P2.

### Omissão: custo de embedding não está estimado

A Tabela B estima tokens armazenados, mas não o custo de gerar os embeddings. Para ~4M de tokens com text-embedding-3-large (OpenAI) ou equivalente Azure, o custo seria da ordem de R$ 80–200 na ingestão inicial, mais o custo de re-ingestão mensal. Pequeno, mas deveria estar declarado para evitar surpresas no orçamento de cloud.

### Omissão: tokens de ruído OCR inflacionam a contagem

A premissa P3 usa 200–300 palavras/página pós-OCR como estimativa de *conteúdo útil*. Mas OCR ruidoso gera tokens extras (palavras fragmentadas, caracteres trocados, hifenização falsa). Na prática, o OCR pode produzir 20–40% mais tokens do que o conteúdo real, impactando custo de embedding e potencialmente poluindo o espaço vetorial.

---

## Seção 3 — Orçamento de contexto

### Risco não considerado: latência end-to-end da pipeline

A análise foca em tokens, mas ignora latência percebida pelo atendente. A pipeline recomendada na Seção 4.4 encadeia:

1. Query rewriting/HyDE → 1 chamada LLM
2. Retrieval híbrido BM25 + dense
3. Cross-encoder reranking (Cohere Rerank v3) → chamada de API externa
4. Parent retrieval (busca adicional por `parent_id`)
5. Geração com citações → 1 chamada LLM

Em condições normais, essa sequência pode levar 4–8 segundos por query. Para um atendente com cliente ao telefone, isso é crítico. A análise não define nenhum SLA de latência nem identifica onde otimizar se o tempo for inaceitável.

### Referência desatualizada para *lost in the middle*

O documento cita "Liu et al., 2023" para justificar o limite de 10–15 chunks. Modelos mais recentes (Claude 3 em diante, GPT-4o) demonstram atenção mais uniforme ao longo do contexto. O threshold de 10–15 pode ser excessivamente conservador para os modelos atuais, ou pode não ser conservador o suficiente dependendo do modelo escolhido — que a análise em nenhum momento especifica.

### Omissão: qual LLM de geração?

A análise inteira não nomeia o modelo de geração. A janela de 128k tokens (usada para calcular os 252 chunks teóricos) é compatível com Claude 3 Sonnet, GPT-4 Turbo e outros, mas incompatível com modelos menores. A escolha do modelo afeta: custo por query, latência, qualidade de citação, e suporte a português brasileiro.

---

## Seção 4 — Estratégia de chunking

### Ponto fraco: detecção de fluxogramas em imagens embutidas

A análise menciona "descrição textual gerada por Vision" para fluxogramas, mas não endereça:

- Como detectar automaticamente que uma imagem embutida *é* um fluxograma (vs. logo, foto, gráfico de barras)
- Qual modelo Vision, com que custo por imagem
- Se o PDF tem 50 imagens decorativas para cada fluxograma relevante, o custo e tempo de processamento escalam mal

Sem uma estratégia de detecção, ou se torna manual (inviável em 800 PDFs) ou processa todas as imagens (caro).

### Risco subestimado: parent retrieval em queries paralelas de múltiplos documentos

O parent retrieval injeta 800–1.200 tokens por chunk relevante. Se uma query comparativa recuperar 8 chunks de documentos diferentes, cada um disparando um parent lookup, o contexto pode explodir para 6.400–9.600 tokens só de parents — potencialmente acima do orçamento prático calculado na Seção 3. A análise não define um limite de parents simultâneos.

### Omissão: modelo de embedding para português

Nenhuma menção ao modelo de embedding. Para documentação de logística em português brasileiro (com termos como "nota fiscal eletrônica", "CNPJ", siglas regionais), modelos treinados predominantemente em inglês têm desempenho inferior. Isso impacta diretamente a qualidade do retrieval denso — o componente mais crítico da pipeline.

---

## Seção 5 — Recomendações dos próximos 30 dias

### Cronograma otimista demais

| Semana | Problema |
|---|---|
| 1 | Provisionar Azure Document Intelligence assume aprovação de cloud instantânea |
| 1–2 | "Mapear todas as macros Confluence" pode ser um projeto de semanas por si só |
| 3 | "50–100 perguntas reais de atendentes" requer disponibilidade e cooperação dos times de negócio — frequentemente o maior gargalo em projetos RAG |
| 4 | Grounding check numérico implementado e validado em uma semana é agressivo |

O plano assume que uma pessoa (ou equipe) está 100% dedicada ao projeto. Se for trabalho paralelo às atividades rotineiras, o cronograma dobra ou triplica.

### Métricas de sucesso indefinidas

A ação 8 menciona medir MRR@5 e NDCG@10, mas não define o que é "bom o suficiente". Sem um critério mínimo de aceitação antes do go-live, o projeto pode ser lançado com qualidade insuficiente por pressão de prazo.

---

## Riscos sistêmicos ausentes na análise

### LGPD e dados pessoais

Documentos de logística frequentemente contêm endereços de entrega, CPF/CNPJ de clientes e dados de destinatários. A análise não menciona LGPD em nenhum momento. Armazenar esses documentos em Azure (nuvem externa) e torná-los recuperáveis por qualquer atendente pode exigir DPA (Data Processing Agreement) com a Microsoft, mapeamento de dados pessoais, e possivelmente anonimização antes da ingestão.

### Controle de acesso por perfil de atendente

A análise trata o RAG como um sistema único sem camadas de permissão. Em operações de logística, é comum que documentos de Compliance não sejam acessíveis a atendentes operacionais, ou que tabelas de preço negociado só sejam visíveis a atendentes de contas específicas. Azure AI Search suporta filtros por metadado no retrieval, mas a estratégia de ACL (Access Control List) precisa ser definida antes de modelar os metadados — não como afterthought.

### Conflito entre versões de documentos

A ação 9 menciona "detectar documentos contraditórios entre versões", mas sem um mecanismo concreto. Se a versão antiga de uma tabela de frete não for deletada do índice antes da nova ser ingerida, o retrieval pode retornar chunks das duas versões simultaneamente, gerando respostas inconsistentes. Soft delete por `data_vigencia_documento` funciona apenas se esse metadado for preenchido corretamente — o que exige disciplina no processo de ingestão.

### Alucinação em conteúdo não-numérico

O grounding check da ação 10 valida apenas valores numéricos. Mas alucinação em RAG frequentemente ocorre em afirmações procedimentais ("o prazo é contado a partir da data de emissão" vs. "a partir da data de entrega") onde nenhum número está errado. Um grounding check de entidades textuais críticas (prazos, condições, exceções) seria igualmente importante.

---

## Resumo dos principais gaps

| Categoria | Gap |
|---|---|
| Técnico | openpyxl não executa fórmulas; detecção de fluxogramas não definida; modelo de embedding para PT-BR ignorado |
| Estimativa | 10 pág/PDF assumido flat; % PDFs escaneados pode ser 2× maior; latência da pipeline não modelada |
| Risco operacional | Procurement Azure; cooperação das áreas de negócio para ground truth; LGPD; ACL por perfil |
| Critério de sucesso | MRR@5 / NDCG@10 sem threshold mínimo definido; modelo de geração não especificado |
| Processo | Conflito entre versões sem mecanismo de soft delete confiável |
