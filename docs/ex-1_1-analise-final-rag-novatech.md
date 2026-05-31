# Análise Final de RAG — NovaTech

> Documento consolidado a partir da análise técnica inicial e da revisão crítica independente. Onde a revisão identificou imprecisões, omissões ou riscos, este documento os incorpora diretamente na seção correspondente.

---

## 1. Desafios, Impactos e Estratégias por Tipo de Fonte

**Tabela A — Análise por tipo de fonte**

| Dimensão | PDFs com tabelas | PDFs escaneados | Wiki Confluence | Planilhas com fórmulas |
|---|---|---|---|---|
| **Principal desafio** | Tabelas com 15+ colunas perdem relação célula↔cabeçalho no parsing texto puro; fluxogramas embutidos como imagem são invisíveis ao LLM | OCR introduz ruído (caracteres trocados, hifenização falsa, layout quebrado em múltiplas colunas) | Links internos criam dependência de contexto entre páginas; macros customizadas (expand, status, panel) geram HTML não-semântico ou vazio | Fórmulas interdependentes perdem semântica ao exportar como CSV; célula calculada vs. valor bruto são indistinguíveis sem metadado explícito |
| **Impacto na qualidade** | Valores de frete trocados entre colunas → respostas incorretas com alta confiança; lacunas em processos cujos passos estão em fluxogramas | Tokens corrompidos reduzem score de similaridade vetorial; chunks ambíguos provocam alucinação com dados que "parecem certos" | Resposta incompleta quando a informação real está na página linkada, não na página recuperada; macros → lixo textual contamina o chunk | LLM responde com a fórmula `=VLOOKUP(...)` em vez do valor calculado; dado desatualizado se planilha não for re-ingerida no ciclo mensal |
| **Parsing** | PyMuPDF + pdfplumber para texto; tabelas → markdown com cabeçalhos explícitos em cada linha; Azure Document Intelligence para tabelas complexas e detecção de layout | Azure Document Intelligence (Form Recognizer) com modelo prebuilt-layout; threshold mínimo de confiança OCR: **0,85** por página | Confluence REST API `/wiki/rest/api/content` (não exportar HTML bruto); resolver links internos (`/pages/viewpage?pageId=`) e incluir título+resumo da página vinculada como contexto pai — ver nota sobre riscos de resolução abaixo | Avaliar todas as fórmulas **antes** da exportação via xlwings (requer Excel instalado) ou Microsoft 365 API — **não usar openpyxl**, que lê o cache do último save e não recalcula fórmulas com dependências externas; preservar fórmula como metadado `formula_original` para auditoria |
| **Chunking** | Chunk por grupo lógico de tabela (ex.: todas as linhas de uma faixa de CEP + cabeçalho); texto narrativo: 400–500 tokens com overlap de 80 tokens; nunca quebrar dentro de uma linha de tabela | Após limpeza OCR: chunking idêntico ao PDF digital; adicionar passo de normalização (regex para valores monetários, datas, siglas) antes de embedar | Por cabeçalho H2/H3 com herança de breadcrumb (`Seção > Subseção > Página`) embutida no início de cada chunk; overlap de 1 parágrafo (~80 tokens) entre chunks contíguos | Serializar cada aba como markdown: `\| Col1 \| Col2 \| ... \|` com cabeçalho repetido a cada 20 linhas; 1 chunk por aba (planilhas raramente passam de 500 tokens serializadas) |
| **Metadados obrigatórios** | `fonte`, `nome_arquivo`, `pagina`, `tipo=tabela/texto/figura`, `area_responsavel`, `data_ingestao`, `data_vigencia_documento` | `fonte`, `nome_arquivo`, `pagina`, `ocr_confidence`, `data_escaneamento`, `revisado_manual=bool` | `fonte=confluence`, `pagina_id`, `titulo`, `breadcrumb`, `ultima_atualizacao`, `links_resolvidos[]`, `links_nao_resolvidos[]` | `fonte=planilha`, `nome_arquivo`, `aba`, `data_exportacao`, `data_atualizacao_planilha`, `formula_original` |
| **Retrieval** | Hybrid BM25 + dense (Azure AI Search); para queries com números (ex.: "frete SP→RJ acima de 500kg"): filtro pré-retrieval `tipo=tabela` | Dense retrieval padrão; adicionar `ocr_confidence` como filtro de hard cutoff (< 0,80 → excluir do retrieval); priorizar `revisado_manual=true` no reranking | Retrieval por chunk; pós-retrieval: resolver links internos e injetar trecho da página vinculada como contexto adicional (parent retrieval automático); chunks com `links_nao_resolvidos[]` não vazio devem exibir aviso ao atendente | Filtro `data_exportacao` no retrieval (sempre retornar chunk mais recente da mesma aba); incluir `data_atualizacao_planilha` na resposta gerada |
| **Validação** | Validar que valores numéricos na resposta existem literalmente no chunk recuperado (grounding check); alerta se chunk de tabela tiver < 3 colunas detectadas | Quarentena automática de páginas com `ocr_confidence < 0,85`: fila para revisão manual antes de ingestão; log de páginas não ingeridas | Testar resolução de links em ambiente de staging antes de go-live; chunks com `links_resolvidos=[]` e que **dependem criticamente** da página vinculada devem ser marcados `qualidade=degradada` e excluídos do retrieval padrão até reprocessamento | Alertar se `data_exportacao` > 35 dias (planilha fora do ciclo mensal); validar que nenhum chunk contém string `=#REF!`, `=#N/A` ou string de fórmula crua |

### 1.1 Nota: riscos na resolução de links Confluence

A estratégia de resolver links internos pressupõe condições que podem não se verificar:

- **Páginas deletadas ou movidas** retornam 404 — o chunk-pai existe mas o contexto de suporte some
- **Restrições de permissão por espaço** são comuns; o token de API pode não ter acesso a todos os espaços vinculados
- **Macros `{include:pageId=...}`** criam dependências recursivas que podem formar ciclos ou chains longas

**Mitigação:** implementar resolução com retry limitado (máximo 2 níveis de profundidade), registrar falhas no metadado `links_nao_resolvidos[]`, e definir política explícita: chunks com dependências críticas não resolvidas vão para quarentena em vez de serem ingeridos com contexto incompleto.

### 1.2 Nota: detecção de fluxogramas em imagens embutidas

A estratégia de "descrição textual gerada por Vision" para fluxogramas precisa de uma etapa de detecção antes de chamar o modelo Vision, pois processar todas as imagens é caro e inviável em 800 PDFs:

1. **Filtro heurístico inicial**: imagens com dimensões > 300×300px e aspect ratio entre 0,5–2,0 são candidatas (logos tendem a ser pequenos ou muito estreitos; fotos tendem a ser quadradas em alta resolução)
2. **Classificador leve** (CLIP zero-shot ou regra baseada em análise de cores): distingue diagrama/fluxograma de foto/gráfico de barras
3. **Vision apenas para candidatos confirmados**: GPT-4o Vision ou Claude com suporte a imagem — estimar custo por imagem e definir budget máximo antes de escalar

Sem essa pipeline, o custo e tempo de processamento escalam linearmente com o número de imagens decorativas.

---

## 2. Estimativa da Base em Tokens

### 2.1 Premissas e riscos associados

| ID | Premissa | Justificativa | Risco |
|---|---|---|---|
| P1 | 70% dos 800 PDFs são digitais com tabelas = **560 PDFs**; 30% escaneados = **240 PDFs** | Cenário diz "alguns documentos escaneados" — conservador em 30% | **Subestimado**: em empresas de logística com documentação de décadas, 50–70% do acervo costuma ser escaneado (apólices, contratos antigos, tabelas digitalizadas). A 50%, a estimativa central sobe ~12% |
| P2 | PDFs digitais: **250–400 palavras/página** (central: 325) | Tabelas complexas reduzem densidade de texto; PDFs de logística têm ~300–350 palavras em páginas mistas | Válida, mas dependente de P3 |
| P3 | PDFs escaneados (pós-OCR): **200–300 palavras/página** (central: 250) de *conteúdo útil* | OCR produz tokens espúrios; páginas com formulários têm menor densidade textual útil | OCR ruidoso gera 20–40% **mais tokens** do que o conteúdo real (palavras fragmentadas, hifenização falsa) — custo de embedding e espaço vetorial impactados |
| P4 | Planilhas serializadas: **800–2.500 palavras/planilha** (central: 1.500) | Aba de 50 linhas × 15 colunas ≈ 750 células × média 2 tokens/célula + cabeçalhos + notas | Válida |
| P5 | Wiki: ±20% em torno de 1.500 palavras/página (dado explícito) | Variância para páginas stub vs. páginas longas de política | Válida |
| **P6** | **10 páginas por PDF** (flat para todos os 800 documentos) | Estimativa central sem dados reais | **Premissa mais frágil**: PDFs de logística variam enormemente — tabelas de frete por CEP podem ter 100+ páginas; manuais operacionais, 200+. Uma única tabela de frete com 200 páginas desloca mais a estimativa do que toda a variância de P2. **Ação obrigatória**: amostrar 50 PDFs reais antes de fixar essa premissa |

### 2.2 Tabela B — Estimativa de tokens por fonte

| Fonte | Qtd docs | Páginas / unidade | Palavras/pág (min–central–max) | Palavras totais min | Palavras totais central | Palavras totais max | Tokens min | Tokens central | Tokens max |
|---|---|---|---|---|---|---|---|---|---|
| PDFs c/ tabelas (P1, P2) | 560 | 10 pág/PDF | 250 – 325 – 400 | 1.400.000 | 1.820.000 | 2.240.000 | **1.866.667** | **2.426.667** | **2.986.667** |
| PDFs escaneados (P1, P3) | 240 | 10 pág/PDF | 200 – 250 – 300 | 480.000 | 600.000 | 720.000 | **640.000** | **800.000** | **960.000** |
| Wiki Confluence (P5) | 400 | 1 pág/unidade | 1.200 – 1.500 – 1.800 | 480.000 | 600.000 | 720.000 | **640.000** | **800.000** | **960.000** |
| Planilhas (P4) | 50 | 1 planilha/unidade | 800 – 1.500 – 2.500 | 40.000 | 75.000 | 125.000 | **53.333** | **100.000** | **166.667** |
| **TOTAL** | | | | **2.400.000** | **3.095.000** | **3.805.000** | **3.200.000** | **4.126.667** | **5.073.334** |
| **Chunks (÷ 500 tokens)** | | | | | | | **6.400** | **8.253** | **10.147** |

> Conversão: `palavras ÷ 0,75 = tokens`. Chunk-alvo de 500 tokens sem overhead de metadado embutido.

**Cenário alternativo (P1 revisada para 50% escaneados):** estimativa central passa de ~4,1M para ~4,6M tokens — impacto de ~12% no tamanho do índice e custo de embedding.

### 2.3 Custo de embedding (omissão corrigida)

A Tabela B estima tokens armazenados, mas não o custo de geração dos embeddings. Para ~4,1M tokens centrais:

| Modelo | Custo estimado (ingestão inicial) | Custo re-ingestão mensal (20% renovação) |
|---|---|---|
| text-embedding-3-large (OpenAI / Azure) | ~R$ 80–200 | ~R$ 16–40 |
| text-embedding-3-small | ~R$ 10–25 | ~R$ 2–5 |

Valores pequenos mas devem estar declarados no orçamento de cloud para evitar surpresas. Incluir no planejamento junto aos custos de Azure Document Intelligence e de inferência do LLM de geração.

---

## 3. Análise de Orçamento de Contexto

### 3.1 Orçamento teórico máximo

```
Janela total:                     128.000 tokens
(-) System prompt fixo:            -2.000 tokens
                                  ─────────────
Disponível para conteúdo:         126.000 tokens
÷ chunk-alvo (500 tokens):
Chunks teóricos máximos:              252 chunks
```

> **Nota sobre o modelo de geração:** a janela de 128k tokens é compatível com Claude 3.5 Sonnet / Claude 3 Opus, GPT-4 Turbo e GPT-4o. O modelo de geração **precisa ser definido antes do go-live**, pois afeta custo por query, latência, qualidade de citação e suporte a português brasileiro. Modelos com janela menor (ex.: GPT-3.5, versões mais antigas) invalidam os cálculos desta seção.

### 3.2 Cenário realista de uma consulta de atendimento

| Componente do contexto | Tokens estimados | Notas |
|---|---|---|
| System prompt (fixo) | 2.000 | Dado pelo enunciado |
| Mensagem do usuário (query atual) | 150 | Ex.: "Qual o prazo de entrega para cliente Gold no Nordeste?" |
| Reformulação/HyDE da query | 300 | Expansão da query para melhorar retrieval |
| Histórico de conversa (3 turnos anteriores) | 1.500 | 3 × média de 500 tokens por turno (pergunta + resposta) |
| Reserva para geração da resposta | 1.000 | Resposta com 2–3 parágrafos + citações |
| Formatação de citações (fonte, página, data) | 200 | 3–5 citações × ~50 tokens cada |
| **Total overhead de runtime** | **3.150** | |

```
Janela total:                     128.000 tokens
(-) System prompt fixo:            -2.000 tokens
(-) Overhead de runtime:           -3.150 tokens
                                  ─────────────
Disponível para chunks:           122.850 tokens
÷ 500 tokens/chunk:
Chunks teóricos (cenário realista):   245 chunks
```

### 3.3 Limite prático por qualidade (efeito *lost in the middle*)

O modelo distribui atenção de forma não uniforme: chunks nas posições centrais de contextos longos recebem atenção significativamente menor. Estudos iniciais (Liu et al., 2023) observaram degradação a partir de ~10–12 itens.

> **Atualização:** modelos mais recentes (Claude 3+ e GPT-4o) demonstram atenção mais uniforme ao longo do contexto. O threshold de 10–15 chunks pode ser conservador para modelos modernos — ou insuficiente dependendo do modelo escolhido. **O limite prático deve ser validado empiricamente com o modelo de geração selecionado**, usando o dataset de ground truth (ação 7 do plano de 30 dias).

| Tipo de query | Chunks recomendados | Justificativa |
|---|---|---|
| Factual ("Qual o SLA tipo X?") | 3–5 | Alta precisão; 1–2 chunks geralmente suficientes + contexto de suporte |
| Procedural ("Quais os passos para reclamação?") | 5–8 | Sequência pode estar em chunks contíguos de 1–2 documentos |
| Comparativa ("Diferença entre política A e B?") | 8–12 | Requer chunks de documentos distintos + contexto de cada |
| Síntese ("Resuma regras de frete para região Sul") | 10–15 | Múltiplos documentos; acima de 15 o ganho marginal cai |

**Conclusão de orçamento:**

| Limite | Valor | Interpretação |
|---|---|---|
| Teórico absoluto | 252 chunks | Matematicamente possível; qualidade degradada |
| Teórico (overhead real) | 245 chunks | Após descontar runtime overhead |
| **Prático recomendado** | **10–15 chunks** | Threshold de qualidade a ser validado com o modelo escolhido; retrieve k=20, rerank → top-10 |

### 3.4 Latência end-to-end (omissão corrigida)

A pipeline recomendada encadeia etapas que acumulam latência perceptível pelo atendente:

| Etapa | Latência estimada |
|---|---|
| Query rewriting / HyDE | 0,5–1,5 s (1 chamada LLM) |
| Retrieval híbrido BM25 + dense | 0,2–0,5 s (Azure AI Search) |
| Cross-encoder reranking (Cohere Rerank v3) | 0,5–1,5 s (chamada API externa) |
| Parent retrieval adicional | 0,1–0,3 s (busca por `parent_id`) |
| Geração com citações | 1,5–4,0 s (1 chamada LLM, depende do tamanho da resposta) |
| **Total estimado** | **2,8–7,8 s** |

Para um atendente com cliente ao telefone, latência > 5s é crítica. **Definir SLA de latência antes do design final** (ex.: p95 < 4s). Se o target não for atingido, as alavancas de otimização são, em ordem de impacto: (1) remover HyDE em queries simples, (2) usar reranker local (BGE-reranker) em vez de API externa, (3) reduzir k de 20 para 10 antes do reranking.

---

## 4. Estratégia de Chunking

### 4.1 Tamanho e overlap por tipo de conteúdo

| Tipo de conteúdo | Chunk-alvo | Overlap | Tipo de chunking | Razão |
|---|---|---|---|---|
| Texto narrativo (política, procedimento) | 400–500 tokens | 80–100 tokens | Semântico com corte em limite de parágrafo | Perguntas procedimentais exigem contexto completo de cada passo |
| Tabelas de frete/SLA | 200–400 tokens | 1–2 linhas da tabela | Estrutural: 1 chunk = grupo de linhas + cabeçalho repetido | Queries numéricas precisam da linha inteira + cabeçalho para não perder a relação coluna↔valor |
| Fluxograma (descrição textual gerada por Vision) | 300–500 tokens | 50 tokens | Estrutural por etapa do fluxo | Cada nó deve ser recuperável individualmente |
| Wiki (páginas longas de política) | 500 tokens | 80 tokens | Estrutural por H2/H3 com breadcrumb herdado | Herança de breadcrumb no início garante contexto hierárquico |
| Planilha serializada | 300–500 tokens | 0 (por aba) | Estrutural por aba | Cada aba é uma unidade semântica independente |

### 4.2 Semântico vs. Estrutural — quando usar cada um

**Chunking estrutural** (prioridade): use quando o documento tem hierarquia explícita (cabeçalhos, linhas de tabela, numeração de passos). Preserva a semântica intencional do autor e produz chunks mais coerentes.

**Chunking semântico** (complementar): aplique dentro de seções longas sem subdivisão estrutural (blocos de texto > 600 tokens sem cabeçalho interno). Use sliding window com detecção de mudança de tópico por cosine similarity entre sentenças consecutivas.

**Regra prática**: estrutural primeiro, semântico como fallback.

### 4.3 Mitigação do *Lost in the Middle*

Três estratégias combinadas:

1. **Reordenação posicional pós-rerank**: coloque o chunk com maior score na posição 1 (início) e o segundo maior na posição N (fim). Chunks de suporte ficam no meio. O modelo presta mais atenção ao início e ao fim.

2. **Limite hard de k=10 no prompt de resposta**: mesmo que 20 chunks sejam recuperados, o prompt de resposta recebe apenas os 10 mais relevantes após reranking.

3. **Chunking menor + parent retrieval**: chunks menores (300 tokens) têm maior precisão no retrieval; o parent (seção completa, 800–1.200 tokens) é injetado no contexto, concentrando a informação crítica em menos posições.

### 4.4 Pipeline de retrieval recomendado

```
Query do atendente
      │
      ▼
[Query rewriting / expansão] ── HyDE ou step-back prompting
      │                          (opcional: desativar para queries simples → reduz latência 0,5–1,5s)
      ▼
[Retrieval híbrido] ── BM25 (sparse) + dense vector (Azure AI Search)
      │              ── top-k = 20 candidatos
      ▼
[Reranking] ── Cross-encoder (Cohere Rerank v3 ou BGE-reranker-v2-m3)
      │      ── Filtra para top-10
      ▼
[Reordenação lost-in-the-middle] ── Melhor no topo, segundo melhor no fim
      │
      ▼
[Geração com citações] ── LLM responde com referência explícita ao chunk
```

### 4.5 Parent-Child Retrieval — quando usar

**Use parent-child quando:**
- O chunk recuperado é relevante mas incompleto sem o parágrafo anterior/seguinte (ex.: um passo de procedimento que referencia "conforme definido acima")
- A query é procedural e a resposta está distribuída em 2–3 chunks contíguos
- Documentos de política têm definições na seção anterior ao artigo recuperado

**Configuração:** child = 300–400 tokens (alta precisão no retrieval); parent = 800–1.200 tokens (H2 completa). Armazene o `parent_id` como metadado do child. Ao recuperar, substitua o child pelo parent no contexto final.

**Atenção — risco de explosão de contexto em queries comparativas:** se uma query recuperar 8 chunks de documentos diferentes, cada um disparando um parent lookup de 800–1.200 tokens, o contexto pode atingir 6.400–9.600 tokens só de parents — potencialmente acima do orçamento prático. **Definir limite máximo de 4 parents simultâneos por query.** Quando o limite é atingido, priorizar os parents dos chunks com maior score de reranking.

**Não use** para tabelas (o parent seria uma tabela inteira → muito genérico) ou para planilhas.

### 4.6 Summary Index — quando usar

**Use summary index quando:**
- Query de síntese envolve múltiplos documentos ("quais são todas as exceções à política de devolução?")
- O volume de chunks candidatos antes do reranking é > 50

**Implementação:** no momento da ingestão, gere um resumo de 200–400 tokens por documento. Mantenha dois índices: `index_summaries` e `index_chunks`.

Na query de síntese:
1. Retrieval em `index_summaries` → identifica os 5–8 documentos mais relevantes
2. Retrieval em `index_chunks` filtrado por `nome_arquivo IN [documentos identificados]` → recupera chunks precisos

Custo adicional de ingestão: ~800 chamadas LLM (1 por PDF + 1 por página wiki). Justificável para queries de síntese que hoje consomem 12 minutos do atendente.

### 4.7 Modelo de embedding para português brasileiro (omissão corrigida)

A documentação da NovaTech usa vocabulário especializado em logística brasileira: "nota fiscal eletrônica", "CNPJ", "DANFE", siglas regionais, nomes de cidades e estados. Modelos de embedding treinados predominantemente em inglês têm desempenho inferior para esse domínio, impactando diretamente a qualidade do retrieval denso.

**Opções avaliadas:**

| Modelo | Pontos fortes | Limitações |
|---|---|---|
| `text-embedding-3-large` (OpenAI/Azure) | Melhor desempenho geral em benchmarks multilíngues; integração nativa com Azure AI Search | Custo maior; dataset de treino predominantemente em inglês |
| `multilingual-e5-large` (Microsoft) | Treinado explicitamente em multilíngue incluindo PT-BR; open-source | Requer hospedagem própria ou via Azure ML |
| `paraphrase-multilingual-mpnet-base-v2` (SBERT) | Leve; boa performance em PT-BR | Dimensão menor → menor capacidade para domínios especializados |

**Recomendação:** avaliar `multilingual-e5-large` vs. `text-embedding-3-large` no dataset de ground truth (ação 7) antes de fixar a escolha. Mensurar MRR@5 em queries com terminologia específica de logística brasileira.

---

## 5. Riscos Sistêmicos

### 5.1 LGPD e dados pessoais

Documentos de logística frequentemente contêm endereços de entrega, CPF/CNPJ de clientes e dados de destinatários. A análise original não contemplou LGPD.

**Riscos concretos:**
- Armazenamento em Azure (nuvem externa) pode exigir **DPA (Data Processing Agreement)** com a Microsoft
- Tornar esses dados recuperáveis por qualquer atendente pode violar o princípio de minimização de dados da LGPD
- Chunks com dados pessoais podem ser retornados em queries não relacionadas à pessoa específica

**Ações obrigatórias antes da ingestão:**
1. Mapeamento de dados pessoais nos documentos (PII scanning)
2. Definir política de anonimização: mascarar CPF, endereço completo, nome de destinatário nos chunks antes de ingerir
3. Revisar e assinar DPA com Microsoft Azure
4. Documentar a base legal de tratamento de dados no sistema RAG

### 5.2 Controle de acesso por perfil de atendente

O sistema RAG não pode ser tratado como camada única sem permissões. Em operações de logística, é comum que:
- Documentos de Compliance não sejam acessíveis a atendentes operacionais
- Tabelas de preço negociado só sejam visíveis a atendentes de contas específicas
- Informações de auditoria interna sejam restritas a lideranças

**Implementação:** Azure AI Search suporta filtros por metadado no retrieval (security trimming). A estratégia de ACL (Access Control List) precisa ser definida **antes de modelar os metadados** — o campo `perfil_acesso[]` ou equivalente deve estar no schema desde a primeira ingestão. Implementar como afterthought exige reprocessamento de todos os documentos.

### 5.3 Conflito entre versões de documentos

A análise menciona detectar documentos contraditórios, mas sem mecanismo concreto. Se a versão antiga de uma tabela de frete não for deletada do índice antes da nova ser ingerida, o retrieval pode retornar chunks das duas versões simultaneamente.

**Mecanismo de soft delete confiável:**
1. Todo documento recebe `data_vigencia_documento` e `versao` nos metadados no momento da ingestão
2. Na re-ingestão de um documento atualizado: primeiro marcar todos os chunks da versão anterior com `ativo=false` (soft delete), depois ingerir a nova versão com `ativo=true`
3. Todos os filtros de retrieval incluem `ativo=true` por padrão
4. O processo de re-ingestão mensal inclui etapa de diff automático para identificar documentos com alterações e sinalizar para revisão antes de publicar

Este mecanismo funciona **somente se** `data_vigencia_documento` for preenchido corretamente. Incluir validação desse campo como bloqueador no pipeline de ingestão.

### 5.4 Alucinação em conteúdo não-numérico

O grounding check da ação 10 valida apenas valores numéricos. Mas alucinação em RAG frequentemente ocorre em afirmações procedimentais sem erro numérico:
- "o prazo é contado a partir da **data de emissão**" vs. "a partir da **data de entrega**"
- "válido para clientes **Gold e Platinum**" vs. "válido para clientes **Gold**"

**Extensão recomendada do grounding check:** validar também entidades textuais críticas — prazos condicionais, segmentos de cliente, exceções geográficas, condições de aplicação. Implementar como extração de triplas (entidade, atributo, valor) do chunk e verificação se a tripla está presente na resposta gerada.

---

## 6. Recomendações Acionáveis — Próximos 30 Dias

*(Priorizadas por impacto direto na viabilidade do MVP; cronograma assume equipe dedicada — se paralelo às atividades rotineiras, estimar 2–3× mais tempo)*

1. **[Semana 1] Iniciar aprovação de procurement para Azure Document Intelligence** — em empresas com processo de TI/cloud, aprovação pode levar 2–6 semanas. Iniciar imediatamente; usar período de aprovação para as demais ações da Semana 1–2.

2. **[Semana 1] Amostrar distribuição real de tamanhos de PDF** — selecionar 50 PDFs representativos e medir páginas/documento. Refinar premissa P6 antes de escalar a estimativa de tokens para os 800 documentos.

3. **[Semana 1] Definir threshold OCR = 0,85** e criar fila de quarentena: páginas abaixo do threshold não entram na base até revisão manual — evita contaminar o índice com ruído desde o início.

4. **[Semana 1–2] Mapear todas as macros Confluence** em uso: classificar em "renderizável como texto", "ignorar" ou "requer tratamento especial". Considerar que esse mapeamento pode ser um projeto de semanas por si só; iniciar com os espaços de maior volume de consultas.

5. **[Semana 1–2] Mapeamento LGPD + definição de ACL** — identificar campos com dados pessoais nos documentos, definir política de anonimização e schema de controle de acesso antes de qualquer ingestão.

6. **[Semana 2] Exportar as 50 planilhas com valores calculados** via xlwings ou Microsoft 365 API (não openpyxl) e validar que nenhum chunk contém `#REF!`, `#N/A` ou strings de fórmula crua.

7. **[Semana 2] Configurar Azure AI Search** com dois índices: `idx-chunks` (retrieval principal) e `idx-summaries` (queries de síntese). Definir schema de metadados obrigatórios — incluindo `ativo`, `perfil_acesso[]` e `data_vigencia_documento` — antes de ingerir qualquer documento.

8. **[Semana 2–3] Implementar chunking híbrido** (estrutural por cabeçalho + semântico por fallback) com metadados `parent_id` e `ativo=true` em todos os chunks.

9. **[Semana 3] Coletar 50–100 perguntas reais dos atendentes** com respostas esperadas e fonte correta. Este é frequentemente o maior gargalo de projetos RAG — requer disponibilidade e cooperação dos times de negócio. Iniciar o agendamento dessas sessões na Semana 1.

10. **[Semana 3] Avaliar modelos de embedding para PT-BR** — comparar `multilingual-e5-large` vs. `text-embedding-3-large` usando as primeiras queries do ground truth. Fixar a escolha antes da ingestão em larga escala.

11. **[Semana 3] Implementar e avaliar reranking** com Cohere Rerank v3 ou BGE-reranker-v2-m3 sobre o ground truth. Medir MRR@5 e NDCG@10 antes e depois. **Definir threshold mínimo de aceitação antes de começar** (ex.: MRR@5 ≥ 0,75) para evitar go-live por pressão de prazo com qualidade insuficiente.

12. **[Semana 3–4] Definir processo de re-ingestão mensal** com mecanismo de soft delete (`ativo=false` antes de ingerir nova versão) e validação de diff para detectar documentos contraditórios.

13. **[Semana 4] Implementar grounding check estendido na geração**: validar valores numéricos críticos (SLA, prazo, peso, CEP) **e** entidades textuais críticas (condições, segmentos, exceções) contra os chunks recuperados.

14. **[Semana 4] Medir latência end-to-end da pipeline completa** em ambiente de staging com o modelo de geração escolhido. Se p95 > 4s, aplicar otimizações: desativar HyDE em queries simples, avaliar reranker local, reduzir k.

---

## 7. Resumo dos Principais Gaps Resolvidos

| Categoria | Gap original | Resolução neste documento |
|---|---|---|
| Técnico | openpyxl não executa fórmulas | Substituído por xlwings / Microsoft 365 API (Seção 1) |
| Técnico | Detecção de fluxogramas não definida | Pipeline de filtro heurístico + classificador + Vision (Seção 1.2) |
| Técnico | Modelo de embedding para PT-BR ignorado | Seção 4.7 com avaliação comparativa |
| Técnico | Parent retrieval pode explodir contexto | Limite de 4 parents simultâneos (Seção 4.5) |
| Estimativa | 10 pág/PDF assumido flat | Marcado como premissa mais frágil; amostragem obrigatória (Seção 2.1, P6) |
| Estimativa | % PDFs escaneados pode ser 2× maior | Cenário alternativo P1 calculado (Seção 2.2) |
| Estimativa | Custo de embedding não estimado | Seção 2.3 com faixas de custo por modelo |
| Estimativa | Latência da pipeline não modelada | Seção 3.4 com breakdown por etapa e alavancas de otimização |
| Risco operacional | Procurement Azure ignorado | Ação 1 do plano de 30 dias com antecipação obrigatória |
| Risco operacional | Conflito entre versões sem mecanismo confiável | Mecanismo de soft delete com `ativo` (Seção 5.3) |
| Risco operacional | LGPD não mencionada | Seção 5.1 com ações obrigatórias pré-ingestão |
| Risco operacional | ACL por perfil de atendente ausente | Seção 5.2 com estratégia de metadado desde o schema inicial |
| Critério de sucesso | MRR@5 / NDCG@10 sem threshold mínimo | Ação 11: definir threshold antes de iniciar avaliação |
| Critério de sucesso | Modelo de geração não especificado | Seção 3.1 com critérios de seleção e impactos |
| Processo | Grounding check apenas numérico | Seção 5.4 + Ação 13: extensão para entidades textuais críticas |
| Processo | Resolução de links Confluence otimista | Seção 1.1 com política de quarentena para links não resolvidos |
