# Análise Técnica de RAG — NovaTech

---

## 1. Desafios, Impactos e Estratégias por Tipo de Fonte

**Tabela A — Análise por tipo de fonte**

| Dimensão | PDFs com tabelas | PDFs escaneados | Wiki Confluence | Planilhas com fórmulas |
|---|---|---|---|---|
| **Principal desafio** | Tabelas com 15+ colunas perdem relação célula↔cabeçalho no parsing texto puro; fluxogramas embutidos como imagem são invisíveis ao LLM | OCR introduz ruído (caracteres trocados, hifenização falsa, layout quebrado em múltiplas colunas) | Links internos criam dependência de contexto entre páginas; macros customizadas (expand, status, panel) geram HTML não-semântico ou vazio | Fórmulas interdependentes perdem semântica ao exportar como CSV; célula calculada vs. valor bruto são indistinguíveis sem metadado explícito |
| **Impacto na qualidade** | Valores de frete trocados entre colunas → respostas incorretas com alta confiança; lacunas em processos cujos passos estão em fluxogramas | Tokens corrompidos reduzem score de similaridade vetorial; chunks ambíguos provocam alucinação com dados que "parecem certos" | Resposta incompleta quando a informação real está na página linkada, não na página recuperada; macros → lixo textual contamina o chunk | LLM responde com a fórmula `=VLOOKUP(...)` em vez do valor calculado; dado desatualizado se planilha não for re-ingerida no ciclo mensal |
| **Parsing** | PyMuPDF + pdfplumber para texto; tabelas → markdown com cabeçalhos explícitos em cada linha; Azure Document Intelligence para tabelas complexas e detecção de layout | Azure Document Intelligence (Form Recognizer) com modelo prebuilt-layout; threshold mínimo de confiança OCR: **0,85** por página | Confluence REST API `/wiki/rest/api/content` (não exportar HTML bruto); resolver links internos (`/pages/viewpage?pageId=`) e incluir título+resumo da página vinculada como contexto pai | Avaliar todas as fórmulas antes da exportação; exportar valores calculados (não fórmulas); preservar fórmula como metadado `formula_original` para auditoria |
| **Chunking** | Chunk por grupo lógico de tabela (ex.: todas as linhas de uma faixa de CEP + cabeçalho); texto narrativo: 400–500 tokens com overlap de 80 tokens; nunca quebrar dentro de uma linha de tabela | Após limpeza OCR: chunking idêntico ao PDF digital; adicionar passo de normalização (regex para valores monetários, datas, siglas) antes de embedar | Por cabeçalho H2/H3 com herança de breadcrumb (`Seção > Subseção > Página`) embutida no início de cada chunk; overlap de 1 parágrafo (~80 tokens) entre chunks contíguos | Serializar cada aba como markdown: `\| Col1 \| Col2 \| ... \|` com cabeçalho repetido a cada 20 linhas; 1 chunk por aba (planilhas raramente passam de 500 tokens serializadas) |
| **Metadados obrigatórios** | `fonte`, `nome_arquivo`, `pagina`, `tipo=tabela/texto/figura`, `area_responsavel`, `data_ingestao`, `data_vigencia_documento` | `fonte`, `nome_arquivo`, `pagina`, `ocr_confidence`, `data_escaneamento`, `revisado_manual=bool` | `fonte=confluence`, `pagina_id`, `titulo`, `breadcrumb`, `ultima_atualizacao`, `links_resolvidos[]` | `fonte=planilha`, `nome_arquivo`, `aba`, `data_exportacao`, `data_atualizacao_planilha`, `formula_original` |
| **Retrieval** | Hybrid BM25 + dense (Azure AI Search); para queries com números (ex.: "frete SP→RJ acima de 500kg"): filtro pré-retrieval `tipo=tabela` | Dense retrieval padrão; adicionar `ocr_confidence` como filtro de hard cutoff (< 0,80 → excluir do retrieval); priorizar `revisado_manual=true` no reranking | Retrieval por chunk; pós-retrieval: resolver links internos e injetar trecho da página vinculada como contexto adicional (parent retrieval automático) | Filtro `data_exportacao` no retrieval (sempre retornar chunk mais recente da mesma aba); incluir `data_atualizacao_planilha` na resposta gerada |
| **Validação** | Validar que valores numéricos na resposta existem literalmente no chunk recuperado (grounding check); alerta se chunk de tabela tiver < 3 colunas detectadas | Quarentena automática de páginas com `ocr_confidence < 0,85`: fila para revisão manual antes de ingestão; log de páginas não ingeridas | Testar resolução de links em ambiente de staging antes de go-live; monitorar chunks com `links_resolvidos=[]` (página linkada foi deletada ou movida) | Alertar se `data_exportacao` > 35 dias (planilha fora do ciclo mensal); validar que nenhum chunk contém string `=#REF!` ou `=#N/A` |

---

## 2. Estimativa da Base em Tokens

### Premissas declaradas (dados não fornecidos explicitamente)

| ID | Premissa | Justificativa |
|---|---|---|
| P1 | 70% dos 800 PDFs são digitais com tabelas = **560 PDFs**; 30% escaneados = **240 PDFs** | Cenário diz "alguns documentos escaneados" — conservador em 30% |
| P2 | PDFs digitais: **250–400 palavras/página** (central: 325) | Tabelas complexas reduzem densidade de texto; PDFs de logística têm ~300–350 palavras em páginas mistas |
| P3 | PDFs escaneados (pós-OCR): **200–300 palavras/página** (central: 250) | OCR produz tokens espúrios; páginas com formulários têm menor densidade textual útil |
| P4 | Planilhas serializadas: **800–2.500 palavras/planilha** (central: 1.500) | Aba de 50 linhas × 15 colunas ≈ 750 células × média 2 tokens/célula + cabeçalhos + notas |
| P5 | Wiki: ±20% em torno de 1.500 palavras/página (dado explícito) | Variância para páginas stub vs. páginas longas de política |

### Tabela B — Estimativa de tokens por fonte

| Fonte | Qtd docs | Páginas / unidade | Palavras/pág (min–central–max) | Palavras totais min | Palavras totais central | Palavras totais max | Tokens min | Tokens central | Tokens max |
|---|---|---|---|---|---|---|---|---|---|
| PDFs c/ tabelas (P1, P2) | 560 | 10 pág/PDF | 250 – 325 – 400 | 1.400.000 | 1.820.000 | 2.240.000 | **1.866.667** | **2.426.667** | **2.986.667** |
| PDFs escaneados (P1, P3) | 240 | 10 pág/PDF | 200 – 250 – 300 | 480.000 | 600.000 | 720.000 | **640.000** | **800.000** | **960.000** |
| Wiki Confluence (P5) | 400 | 1 pág/unidade | 1.200 – 1.500 – 1.800 | 480.000 | 600.000 | 720.000 | **640.000** | **800.000** | **960.000** |
| Planilhas (P4) | 50 | 1 planilha/unidade | 800 – 1.500 – 2.500 | 40.000 | 75.000 | 125.000 | **53.333** | **100.000** | **166.667** |
| **TOTAL** | | | | **2.400.000** | **3.095.000** | **3.805.000** | **3.200.000** | **4.126.667** | **5.073.334** |
| **Chunks (÷ 500 tokens)** | | | | | | | **6.400** | **8.253** | **10.147** |

> Conversão: `palavras ÷ 0,75 = tokens`. Chunk-alvo de 500 tokens sem overhead de metadado embutido.

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

O modelo distribui atenção de forma não uniforme: chunks nas posições centrais de contextos longos recebem atenção significativamente menor. A degradação observada começa a partir de ~10–12 itens no contexto (Liu et al., 2023).

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
| **Prático recomendado** | **10–15 chunks** | Threshold de qualidade; retrieve k=20, rerank → top-10 |

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
      │
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

---

## Recomendações acionáveis — próximos 30 dias

*(Priorizadas por impacto direto na viabilidade do MVP)*

1. **[Semana 1] Provisionar Azure Document Intelligence** e rodar extração em amostra de 50 PDFs representativos (10 com tabelas complexas, 10 escaneados, 10 com fluxogramas) — validar qualidade do parsing antes de escalar para os 800 documentos.

2. **[Semana 1] Definir threshold OCR = 0,85** e criar fila de quarentena: páginas abaixo do threshold não entram na base até revisão manual — evita contaminar o índice com ruído desde o início.

3. **[Semana 1–2] Mapear todas as macros Confluence** em uso: classificar em "renderizável como texto", "ignorar" ou "requer tratamento especial". Sem isso o parser da wiki gera chunks inúteis que degradam o retrieval.

4. **[Semana 2] Exportar as 50 planilhas com valores calculados** (não fórmulas) via script Python/openpyxl e validar que nenhum chunk contém `#REF!`, `#N/A` ou strings de fórmula crua.

5. **[Semana 2] Configurar Azure AI Search** com dois índices: `idx-chunks` (retrieval principal) e `idx-summaries` (queries de síntese). Definir schema de metadados obrigatórios conforme Tabela A antes de ingerir qualquer documento.

6. **[Semana 2–3] Implementar chunking híbrido** (estrutural por cabeçalho + semântico por fallback) com metadado `parent_id` em todos os chunks — habilita parent retrieval sem reprocessamento futuro.

7. **[Semana 3] Coletar 50–100 perguntas reais dos atendentes** com respostas esperadas e fonte correta: este dataset de avaliação (ground truth) é o único jeito de medir objetivamente se o sistema funciona antes do go-live.

8. **[Semana 3] Implementar e avaliar reranking** com Cohere Rerank v3 ou BGE-reranker-v2-m3 sobre o ground truth coletado — medir MRR@5 e NDCG@10 antes e depois do reranking para justificar o custo operacional.

9. **[Semana 3–4] Definir processo de re-ingestão mensal** alinhado ao ciclo de atualização da NovaTech (3 áreas: Operações, Compliance, Comercial) — incluir validação de diff para detectar documentos contraditórios entre versões e sinalizar para revisão antes de ingerir.

10. **[Semana 4] Implementar grounding check na geração**: validar que valores numéricos críticos na resposta (SLA, prazo, peso, CEP) existem literalmente no chunk recuperado — reduz alucinação em queries de frete e SLA, que são as de maior risco operacional para a NovaTech.
