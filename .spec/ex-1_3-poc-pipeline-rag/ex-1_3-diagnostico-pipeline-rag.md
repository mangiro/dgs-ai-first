# Relatório de Diagnóstico — Pipeline RAG NovaTech Logística

**Data:** 2026-06-08  
**Pipeline avaliado:** `ingest.py` → `search.py` → `build_prompt.py`  
**Modelo de embedding:** `all-MiniLM-L6-v2`  
**Base vetorial:** ChromaDB (distância L2)  
**Recall@5 observado:** 28,6% (2/7 chunks obrigatórios)

---

## 1. DIAGNÓSTICO DE PROBLEMAS DE CHUNKING

### 1.1 Mapeamento da Base de Chunks

A ingestão produziu **37 chunks** a partir de 5 documentos. Nenhuma seção excedeu 500 tokens (a maior tem 134 palavras — seção 3.2 de POL-001), portanto **a subdivisão por tamanho fixo nunca foi ativada** nesta base.

| Documento | Chunks | Maior seção (palavras) | Subdivisão ativada? |
|-----------|--------|------------------------|---------------------|
| FAQ-atendimento.md | 10 (idx 0–9) | 88 (Introdução) | Não |
| POL-001-politica-devolucao.md | 8 (idx 10–17) | 134 (3.2 Exceções) | Não |
| PROC-042-frete-especial-v1.md | 6 (idx 18–23) | 69 (2. Fórmula) | Não |
| PROC-042-v2-frete-especial-revisado.md | 7 (idx 24–30) | 79 (4. Condições) | Não |
| SLA-2024-tabela-sla-clientes.md | 6 (idx 31–36) | 122 (2. Tabela SLAs) | Não |

### 1.2 Problemas Identificados

#### P1 — Chunks excessivamente pequenos diluem o sinal semântico

A grande maioria dos chunks tem entre 19 e 69 palavras. Chunks tão curtos geram embeddings com pouca informação discriminante, o que causa dois efeitos:

- **Alta similaridade entre chunks não-relacionados:** um chunk de 19 palavras como `idx 19` ("Definir a fórmula e os parâmetros para cálculo de frete especial aplicável a cargas com peso acima de 500kg") se torna quase indistinguível de `idx 25` (mesmo texto no v2). O modelo de embedding não tem contexto suficiente para diferenciar versões.
- **"Objetivo" e "Introdução" ocupam slots no top-N:** os chunks de cabeçalho/metadados (idx 0, 10, 18, 24, 31) contêm apenas versão/data/responsável — sem conteúdo operacional — mas competem com chunks informativos no retrieval.

**Evidência do relatório de acurácia:** Na Pergunta 4, dois dos 5 slots foram ocupados por chunks de "Objetivo" (idx 19 e 25), que fornecem apenas descrição genérica.

#### P2 — Tabelas Markdown são preservadas, mas semanticamente opacas para o embedding

As tabelas nos documentos (SLA-2024 seção 2, multiplicadores regionais nas PROC-042) ficam intactas nos chunks (nenhuma excede 500 tokens). O problema não é de corte, mas de **representação**: o modelo `all-MiniLM-L6-v2` não entende bem estrutura tabular em Markdown. Uma consulta "Qual o SLA do cliente Gold?" precisa localizar a célula correta dentro de uma tabela de 7 linhas × 4 colunas, mas o embedding da tabela inteira dilui a relevância de qualquer consulta sobre uma célula específica.

**Evidência:** Pergunta 3 — o chunk `idx 33` (Tabela de SLAs) não foi recuperado no top-5, ranqueando abaixo de `idx 36` (Medição e reportes) que é textual.

#### P3 — Metadados de cabeçalho (título hierárquico) não são incluídos no texto do chunk

A função `dividir_por_secoes` armazena o título hierárquico em `secao` (metadado), mas **o texto do chunk não inclui esse título**. O embedding é gerado apenas sobre o corpo da seção. Isso significa que:

- O chunk `idx 13` (seção "3.1. Prazo geral") contém o texto sobre 7 dias úteis, mas a frase "Prazo geral" não faz parte do texto embedado.
- Uma busca por "prazo de devolução" deve fazer matching semântico apenas com o corpo, perdendo o sinal explícito do título.

**Impacto:** Contribui diretamente para a falha da Pergunta 1, onde o chunk de "Prazo geral" não foi recuperado.

#### P4 — FAQ fragmentada em itens isolados perde inter-referências

Cada item do FAQ vira um chunk independente (32–56 palavras). Itens que se referenciam mutuamente (ex: Item 41 menciona "veja a tabela SLA-2024", Item 8 menciona "PROC-042") perdem essa ligação contextual. O embedding de cada item reflete apenas seu conteúdo isolado, não sua relação com outros documentos.

---

## 2. DIAGNÓSTICO DE PROBLEMAS DE RETRIEVAL

### 2.1 Análise por Cenário do Gabarito

| # | Pergunta | Falha principal | Causa raiz |
|---|----------|-----------------|------------|
| 1 | "Qual o prazo de devolução?" | idx 13 (Prazo geral) e idx 14 (Exceções) não recuperados | **Confusão semântica:** "prazo" atrai idx 22 (prazo de frete) e idx 17 (custos de devolução, que menciona "Prazo expirado"). O embedding de idx 13 (35 palavras sobre "7 dias úteis") é genérico demais para competir |
| 2 | "Posso devolver carga perigosa?" | idx 14 (Exceções — contém regras de carga perigosa) não recuperado | **Confusão cross-domain:** "carga perigosa" existe em PROC-042 v1 (idx 23), PROC-042 v2 (idx 29), SLA-2024 (idx 34) e FAQ (idx 4). O embedding não discrimina "carga perigosa no contexto de devolução" vs. "carga perigosa no contexto de frete" |
| 3 | "Qual o SLA do cliente Gold?" | idx 33 (Tabela de SLAs) não recuperado | **Tabela opaca:** o embedding da tabela Markdown (122 palavras com pipes e headers) é semanticamente distante de "SLA do Gold". Chunks textuais periféricos (Medição, FAQ-41) têm embeddings mais próximos da query |
| 4 | "Frete para 600kg para Manaus?" | idx 27 (Multiplicadores v2) ausente, idx 19/25 (Objetivo) ocupam slots | **Chunks de baixo valor competem:** seções "Objetivo" são genéricas mas mencionam "frete especial" e "500kg", criando similaridade artificial |
| 5 | "Qual o multiplicador para o Sudeste?" | Sucesso, mas com ruído (POL-001 nos slots 1 e 5) | **Ruído cross-domain residual:** mesmo no caso de sucesso, 2/5 slots são desperdiçados com chunks de devolução |

### 2.2 Padrões Sistêmicos de Falha

#### F1 — Vocabulário compartilhado entre domínios causa contaminação cruzada

O corpus tem 5 documentos cobrindo 3 domínios (devolução, frete, SLA), mas termos-chave aparecem em múltiplos domínios:

| Termo | Documentos onde aparece | Efeito no retrieval |
|-------|------------------------|---------------------|
| "carga perigosa" | POL-001 (3.2), PROC-042 v1 (4.), PROC-042 v2 (4.), SLA-2024 (3.), FAQ (3, 32) | Qualquer pergunta com "carga perigosa" atrai 5+ chunks de domínios diferentes |
| "prazo" | POL-001 (3.1, 3.5), PROC-042 v1 (3.), PROC-042 v2 (3.) | "Prazo de devolução" e "prazo de frete" são indistinguíveis para o embedding |
| "frete" | PROC-042 v1 (todos), PROC-042 v2 (todos), POL-001 (3.5), FAQ (8, 27, 45) | Domina o retrieval em qualquer consulta sobre custos |
| "cliente" / "Gold" / "Silver" | SLA-2024 (1, 2), FAQ (15, 27, 41) | FAQ informal compete com documento contratual |

#### F2 — Modelo de embedding não diferencia negação e afirmação

A pergunta "Cliente diz que é Platinum. Existe esse tier?" exige recuperar `idx 32` (Classificação de clientes), que contém "Não existem outros tiers além dos três listados". Modelos de embedding baseados em similaridade cosseno/L2 tratam "Platinum tier" com alta similaridade a qualquer menção de "Platinum", independentemente do contexto ser de negação. O chunk `idx 3` (FAQ Item 15 — "Não existe tier Platinum") provavelmente rankeia bem, mas é uma fonte informal.

#### F3 — Perguntas multi-domínio excedem capacidade do top-5

A pergunta do gabarito "Prazo de devolução + carga perigosa + frete especial" requer **4 chunks obrigatórios** de **3 documentos diferentes** (POL-001-A, POL-001-B, PROC-042v2-A, PROC-042v2-B). Com top-5 e a taxa de ruído observada (64% de falsos positivos), a probabilidade de capturar todos os 4 é próxima de zero.

#### F4 — Distância L2 em vez de similaridade cosseno

O ChromaDB está usando a métrica padrão (L2). O modelo `all-MiniLM-L6-v2` foi treinado com **similaridade cosseno**. Usar L2 em embeddings normalizados é equivalente, mas se os embeddings não estiverem normalizados, o ranqueamento será distorcido. A Sentence Transformers normaliza por padrão, então o impacto é moderado, mas é uma configuração sub-ótima que pode introduzir distorções marginais no ranqueamento.

---

## 3. DIAGNÓSTICO DE PROBLEMAS DE CONFLITO DE FONTES

### 3.1 Pares de Chunks Contraditórios Identificados

| Par | Campo | Valor v1 (PROC-042) | Valor v2 (PROC-042-v2) | Impacto |
|-----|-------|---------------------|------------------------|---------|
| idx 20 vs. idx 26 | Fator de peso (1.001–3.000kg) | 1.2 | 1.15 | Cálculo de frete diverge |
| idx 20 vs. idx 26 | Fator de peso (>3.000kg) | 1.5 | 1.4 | Cálculo de frete diverge |
| idx 21 vs. idx 27 | Multiplicador Sul | 1.2 | 1.3 | Valor do frete diverge |
| idx 21 vs. idx 27 | Multiplicador Sudeste | 1.0 | 1.1 | Relevante para Pergunta 5 |
| idx 21 vs. idx 27 | Multiplicador Centro-Oeste | 1.3 | 1.4 | Valor do frete diverge |
| idx 21 vs. idx 27 | Multiplicador Nordeste | 1.4 | 1.5 | Valor do frete diverge |
| idx 21 vs. idx 27 | Multiplicador Norte | 1.6 | 1.8 | Relevante para Pergunta 4 |
| idx 22 vs. idx 28 | Prazo adicional frete especial | +2 dias úteis | +3 dias úteis | Prazo informado ao cliente diverge |
| idx 23 vs. idx 29 | Desconto de volume | >10 fretes/mês, negociar | >8 fretes 5%, >15 fretes 10% | Regra de desconto diverge |

### 3.2 Avaliação da Matriz de Resolução de Conflitos

A matriz no system prompt é **conceitualmente sólida** (Temporal > Autoridade > Escalonamento), mas tem **limitações práticas**:

#### Limitação 1 — O LLM precisa identificar a versão a partir dos metadados do chunk

Os chunks são entregues ao LLM em tags `<chunk>` com atributos `documento` e `secao`. O nome do arquivo (`PROC-042-frete-especial-v1.md` vs. `PROC-042-v2-frete-especial-revisado.md`) contém a indicação de versão, e a seção do v2 contém "(atualizados em novembro/2023)". Porém:

- Os **metadados de versão do cabeçalho do documento** (Versão 1.0, Data 03/03/2023 vs. Versão 2.0, Data 10/11/2023) **não são incluídos nos chunks**. Eles ficam no chunk de introdução (idx 18 e idx 24), que provavelmente não será recuperado junto com o chunk de multiplicadores.
- O LLM precisa inferir "v2 é mais recente que v1" apenas pelo nome do arquivo. Funciona neste caso, mas é frágil.

#### Limitação 2 — Status de vigência é ambíguo nos documentos

Ambos os documentos PROC-042 dizem explicitamente que **não possuem indicação formal de vigência**. O v2 tem disposições transitórias (seção 5, idx 30) que definem uma data de corte (01/12/2023), mas esse chunk também provavelmente não será recuperado junto com os multiplicadores.

#### Limitação 3 — FAQ como fonte de ruído não-controlável

O FAQ (idx 2, Item 8) menciona: "existem duas versões da PROC-042. A mais recente tem multiplicadores mais altos. Na dúvida, use a mais recente (v2)". Essa é uma orientação **informal** que pode ser recuperada pelo retrieval e interpretada pelo LLM como instrução autoritativa, **bypassando a hierarquia formal do system prompt**.

### 3.3 Cenários de Uso da Fonte Errada

| Cenário | Risco | Probabilidade |
|---------|-------|---------------|
| LLM recebe idx 20 (fórmula v1) sem idx 26 (fórmula v2) | Usa multiplicadores desatualizados sem perceber conflito | **Alta** — retrieval tende a retornar apenas uma versão |
| LLM recebe idx 21 e idx 27 (ambos multiplicadores) mas sem idx 30 (disposições transitórias) | Aplica v2 corretamente (nome sugere), mas não pode validar se o chamado é anterior a 01/12/2023 | **Média** — edge case temporal |
| LLM recebe idx 2 (FAQ Item 8) + idx 21 (multiplicadores v1) | FAQ diz "use v2" mas o chunk v2 pode não estar presente | **Média** — FAQ pode induzir resposta sem base documental |

---

## 4. PROPOSTAS DE CORREÇÃO

### Tabela-Resumo de Propostas

| # | Correção | Prioridade | Componente | Complexidade | Cenários corrigidos |
|---|----------|------------|------------|--------------|---------------------|
| C1 | Prepend do título da seção no texto do chunk | **Crítica** | Chunking | Simples | P1, P2, P4, P5 |
| C2 | Filtragem de chunks de baixo valor (metadados/objetivo) | **Alta** | Chunking | Simples | P4 |
| C3 | Usar similaridade cosseno no ChromaDB | **Alta** | Retrieval | Simples | Todos (melhoria marginal) |
| C4 | Trocar modelo de embedding para multilíngue | **Crítica** | Embedding | Moderada | P1, P2, P3, P5 |
| C5 | Incluir versão/data no texto do chunk | **Alta** | Chunking | Simples | Conflitos PROC-042 |
| C6 | Expandir top-N ou implementar re-ranking | **Alta** | Retrieval | Moderada | P1, P2, P3, P4 |
| C7 | Query expansion / HyDE | **Média** | Retrieval | Moderada | P1, P2 |
| C8 | Agrupar chunks de FAQ por domínio | **Média** | Chunking / Base | Moderada | P2 (ruído cross-domain) |

### Detalhamento

#### C1 — Prepend do título da seção no texto do chunk (Crítica / Simples)

**Problema que resolve:** P3 (título não embedado).

**Implementação:** Na função `dividir_por_secoes`, ao montar o dict do chunk, prefixar o texto com o título hierárquico:

```python
# Em vez de:
secoes.append({"texto": texto_acumulado, ...})

# Usar:
texto_com_titulo = f"{secao_atual_titulo}\n\n{texto_acumulado}"
secoes.append({"texto": texto_com_titulo, ...})
```

**Impacto:** O embedding do chunk `idx 13` passaria a incluir "3.1. Prazo geral" no texto, criando um sinal semântico direto para consultas sobre "prazo". Análogo para "2. Tabela de SLAs" (idx 33), "2.1. Multiplicadores regionais" (idx 21/27), etc. Estimativa: corrigiria ou melhoraria 4 das 5 perguntas do gabarito.

#### C2 — Filtragem de chunks de metadados/objetivo (Alta / Simples)

**Problema que resolve:** Chunks como idx 10 (metadados POL-001), idx 18/24 (metadados PROC-042), idx 19/25 ("Objetivo") competem por slots sem agregar valor.

**Implementação:** Excluir da indexação chunks que contenham apenas metadados (Versão/Data/Responsável/Classificação) ou cujo título seja "Objetivo" e o corpo tenha menos de 40 palavras. Alternativamente, fundir esses metadados no chunk da primeira seção substantiva do documento.

**Impacto:** Remove ~5 chunks de ruído da base, liberando slots no top-N para chunks relevantes.

#### C3 — Usar similaridade cosseno no ChromaDB (Alta / Simples)

**Implementação:** Em `persistir_no_chromadb`:

```python
collection = client.get_or_create_collection(
    name="atendimento_cliente",
    metadata={"hnsw:space": "cosine"}
)
```

**Impacto:** Alinha a métrica de distância com a função de treinamento do modelo. Melhoria incremental no ranqueamento.

#### C4 — Trocar para modelo de embedding multilíngue (Crítica / Moderada)

**Problema que resolve:** `all-MiniLM-L6-v2` foi treinado primariamente em inglês. O corpus é inteiramente em português. O modelo processa português via transferência cross-lingual, mas perde nuances semânticas (ex: "prazo de devolução" vs. "prazo de entrega" são semanticamente mais distantes em português do que "return deadline" vs. "delivery deadline" em inglês).

**Modelos recomendados:**

| Modelo | Dimensão | Línguas | Tamanho |
|--------|----------|---------|---------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 50+ (inclui PT) | 471 MB |
| `multilingual-e5-large` | 1024 | 100+ (inclui PT) | 2.24 GB |
| `intfloat/multilingual-e5-small` | 384 | 100+ (inclui PT) | 471 MB |

**Impacto:** Melhora a discriminação semântica em português. Os modelos `e5` suportam o prefixo `query:` e `passage:` que diferencia queries de documentos, o que melhora retrieval assimétrico.

#### C5 — Incluir versão/data como prefixo nos chunks (Alta / Simples)

**Problema que resolve:** Conflitos PROC-042 v1 vs. v2 sem metadados de versão disponíveis ao LLM.

**Implementação:** Ao criar chunks, extrair versão e data do cabeçalho do documento e incluir como prefixo:

```python
texto_com_meta = f"[Documento: {nome_arquivo} | Versão: {versao} | Data: {data}]\n\n{texto}"
```

**Impacto:** O LLM recebe explicitamente a informação temporal necessária para aplicar o Critério 1 da matriz de conflitos, sem depender de inferência a partir do nome do arquivo.

#### C6 — Expandir top-N + re-ranking (Alta / Moderada)

**Problema que resolve:** top-5 é insuficiente para perguntas multi-domínio; falsos positivos consomem slots.

**Implementação em 2 etapas:**
1. Recuperar top-20 do ChromaDB (retrieval rápido via embedding).
2. Aplicar re-ranking com cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2` ou equivalente multilíngue) para reordenar por relevância semântica fina, e selecionar top-5 do resultado.

**Impacto:** O cross-encoder avalia query-document pairs com atenção cruzada, superando a limitação de embeddings independentes. Corrigiria casos onde o chunk correto existe na posição 6–10 do retrieval bruto.

#### C7 — Query Expansion / HyDE (Média / Moderada)

**Problema que resolve:** Perguntas curtas ("Qual o prazo de devolução?") geram embeddings genéricos que não discriminam domínio.

**Implementação (HyDE — Hypothetical Document Embeddings):**
1. Usar o LLM para gerar uma resposta hipotética à pergunta (sem RAG).
2. Gerar embedding da resposta hipotética.
3. Usar esse embedding para buscar no ChromaDB.

A resposta hipotética conterá termos como "7 dias úteis", "data de recebimento", "devolução de mercadorias" — muito mais próximos semanticamente do chunk `idx 13` do que a pergunta original.

#### C8 — Agrupar FAQ por domínio ou excluir da indexação primária (Média / Moderada)

**Problema que resolve:** FAQ compete como fonte informal contra documentos formais, adicionando ruído sem valor normativo.

**Opções:**
- **Opção A:** Indexar FAQ em collection separada, consultada apenas quando a collection primária não retorna resultados com score acima de threshold.
- **Opção B:** Adicionar tag de domínio nos metadados (`dominio: "devolução"`, `dominio: "frete"`, `dominio: "sla"`) e usar filtro de metadados no ChromaDB após detecção de domínio na pergunta.
- **Opção C:** Remover FAQ da indexação. O system prompt já instrui o LLM a priorizar fontes formais; a presença de FAQ nos chunks pode induzir o LLM a usá-la quando fontes formais faltam.

---

## Conclusão Executiva

O pipeline tem **3 pontos de falha críticos** que, juntos, explicam o recall de 28,6%:

1. **Embedding em língua errada** — `all-MiniLM-L6-v2` não discrimina bem nuances semânticas em português (C4).
2. **Títulos de seção excluídos do embedding** — o sinal semântico mais forte (nome da seção) não é embedado (C1).
3. **Ranqueamento bruto sem re-ranking** — embedding-only retrieval com top-5 não filtra ruído cross-domain (C6).

A correção sequencial recomendada é **C1 → C4 → C3 → C5 → C6**, que são as de maior impacto com menor risco. C1, C3 e C5 podem ser implementadas em menos de 1 hora. C4 requer apenas trocar o nome do modelo. C6 adiciona uma dependência (cross-encoder) mas é a que mais impacta o recall em perguntas difíceis.
