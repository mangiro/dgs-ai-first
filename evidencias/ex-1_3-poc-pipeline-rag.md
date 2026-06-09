# Evidência exercício 1.3 — Construção de pipeline de RAG com ferramentas open-source

## Script de ingestão

**Prompt utilizado:**
```
**Papel:** Você é um engenheiro de dados sênior especializado em pipelines RAG (Retrieval-Augmented Generation) para aplicações de atendimento ao cliente.

**Contexto:** Estou construindo uma POC de pipeline RAG para um sistema de atendimento ao cliente. Tenho documentos `.md` na pasta ./poc-pipeline-rag/docs/ que incluem políticas de devolução, procedimentos de frete, tabelas de SLA, FAQs e cenários de atendimento. O objetivo é permitir que um LLM responda perguntas de clientes com base nesses documentos.

**Tarefa:** Escreva um script Python (`ingest.py`) em ./poc-pipeline-rag, completo e executável que implemente as seguintes etapas:

1. **Leitura:** Percorra todos os arquivos `.md` do diretório ./poc-pipeline-rag/docs/ e leia seu conteúdo como texto.
2. **Chunking:** Divida cada documento em chunks utilizando uma estratégia híbrida:**Primária:** Divisão por seções/cabeçalhos do markdown (`#`, `##`, `###`), preservando a hierarquia semântica do documento.
3. **Secundária:** Se uma seção exceder 500 tokens, aplique divisão por tamanho fixo com overlap de 50 tokens dentro dessa seção.
4. **Justifique no código (via comentários)** por que essa estratégia é superior para perguntas de atendimento ao cliente em comparação com chunking puramente por tamanho fixo.
5. **Embeddings:** Gere embeddings para cada chunk usando a biblioteca `sentence-transformers` (modelo: `all-MiniLM-L6-v2`).
6. **Armazenamento:** Persista no ChromaDB os seguintes dados por chunk:Texto do chunk
7. Embedding gerado
8. Metadados: `nome_documento`, `secao` (título da seção/cabeçalho), `indice_chunk`, `documento_completo` (nome do arquivo original)

**Requisitos técnicos:**

- Use tipagem (type hints) nas funções
- Inclua tratamento de erros para arquivos não encontrados ou vazios
- O script deve ser modular (funções separadas para cada etapa)
- Imprima um resumo ao final: total de documentos processados, total de chunks gerados, tempo de execução

**Formato de saída:** Código Python completo com comentários explicativos nas decisões de design, especialmente na justificativa da estratégia de chunking.
```

**Resultado:**
> Disponível em [ingest.py](../poc-pipeline-rag/ingest.py)

## Script de busca

**Contexto adicionado a sessão:**
> Disponível em [ingest.py](../poc-pipeline-rag/ingest.py)

**Prompt utilizado:**
```
Você é um engenheiro de IA sênior especializado em Python, embeddings e RAG com ChromaDB.

Crie um script Python completo dentro de `./poc-pipeline-rag/` com foco em busca semântica, que faça exatamente o seguinte:

1. Receba uma pergunta em texto via argumento de linha de comando.
2. Gere o embedding da pergunta usando o mesmo modelo/configuração já compatível com a base vetorial existente.
3. Consulte o ChromaDB local já presente no projeto e recupere os N chunks mais similares (N deve ser configurável, padrão 5).
4. Retorne os resultados com:
    - conteúdo do chunk
    - identificador/metadados relevantes
    - score de similaridade de cada chunk
    - ordenação do mais similar para o menos similar

Requisitos técnicos:

- Reaproveite a estrutura existente do projeto em `./poc-pipeline-rag/` sempre que possível.
- Exiba saída legível no terminal.
- Inclua tratamento de erros para:
    - coleção inexistente
    - banco não encontrado
    - pergunta vazia
    - falha na geração de embedding
```

**Resultado:**
> Disponível em [search.py](../poc-pipeline-rag/search.py)

## Script de construção do system prompt

**Contexto adicionado a sessão:**
> Disponível em [ingest.py](../poc-pipeline-rag/ingest.py), [search.py](../poc-pipeline-rag/search.py) e [ex-1_2-system-prompt-v2.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-system-prompt-v2.md)

**Prompt utilizado:**
```
Você é um engenheiro de IA sênior especializado em pipelines RAG e engenharia de contexto para LLMs.

**Tarefa:** Crie um script Python (`build_prompt.py`) em `./poc-pipeline-rag/` que funcione como a etapa final do pipeline: receber a pergunta do usuário + os chunks recuperados pelo `search.py` e montar o prompt completo pronto para envio a um LLM.

**Requisitos funcionais:**

1. **Entrada:** O script deve receber:
   - A pergunta do usuário (string)
   - Uma lista de chunks recuperados, cada um contendo: texto do chunk, metadados (nome_documento, secao, indice_chunk) e score de similaridade

2. **Constante de System Prompt:** Armazene a parte estática do system prompt em uma constante (string multilinha) no topo do script. O system prompt deve ser estruturado em XML + Markdown e incluir obrigatoriamente os seguintes guardrails:
   - Obrigatoriedade de citação de fonte (nome do documento, tipo, versão/data)
   - Proibição absoluta de inventar dados, valores, prazos ou informações não presentes nos chunks
   - Declaração explícita de ausência de informação quando os chunks não responderem à pergunta, com instrução para escalar ao supervisor
   - Resposta em português brasileiro formal e acessível
   - Instrução de basear-se EXCLUSIVAMENTE nos chunks fornecidos como contexto
   - Matriz de resolução de conflitos entre fontes (critério temporal > critério de autoridade > escalonamento)
   - Formato de resposta estruturado em seções: [RESPOSTA], [FONTE(S)], [OBSERVAÇÕES]

3. **Montagem do prompt:** Monte o prompt final combinando três blocos em XML:
   - `<system>` — o system prompt estático (da constante)
   - `<contexto>` — os chunks recuperados, cada um envolto em `<chunk>` com seus metadados como atributos XML e o texto como conteúdo
   - `<pergunta>` — a pergunta original do usuário

4. **Saída:** Imprima o prompt completo montado (XML + Markdown interno) no stdout, pronto para copiar e enviar ao LLM. Inclua separadores visuais para legibilidade.

5. **Integração com search.py:** O script deve poder ser usado de duas formas:
   - **Standalone via CLI:** recebe a pergunta como argumento e internamente chama a lógica de busca do `search.py` para obter os chunks (reutilize as funções existentes)
   - **Como módulo:** exporte uma função `montar_prompt(pergunta: str, chunks: list[dict]) -> str` que possa ser importada por outros scripts

**Requisitos técnicos:**
- Reutilize constantes e funções do `search.py` quando aplicável (MODELO_EMBEDDING, COLLECTION_NAME, etc.)
- Use type hints em todas as funções
- Inclua tratamento de erros para pergunta vazia e lista de chunks vazia
- O system prompt na constante deve estar em XML + Markdown válido e bem indentado
```

**Resultado:**
> Disponível em [build_prompt.py](../poc-pipeline-rag/build_prompt.py)

## Teste do pipeline RAG com mapa de cobertura de chunks

**Contexto adicionado a sessão:**
> Disponível em [build_prompt.py](../poc-pipeline-rag/build_prompt.py) e [mapa-cobertura-chunks.md](../docs/mapa-cobertura-chunks.md)

**Prompt utilizado:**
```
Você é um engenheiro de QA especializado em avaliação de pipelines RAG. Sua tarefa é testar o script `build_prompt.py` de um pipeline RAG de atendimento ao cliente, executando-o com 5 perguntas extraídas do gabarito oficial e produzindo um relatório de acurácia do retrieval.

## CONTEXTO DO PIPELINE
- `build_prompt.py` recebe uma pergunta em linguagem natural via CLI, busca chunks relevantes no ChromaDB usando embeddings, e monta um prompt XML completo (system + contexto + pergunta).
- Uso CLI: `python build_prompt.py "<pergunta>" --top-n 5`
- O script imprime o prompt montado no stdout, incluindo os chunks recuperados com metadados (documento, seção, índice, score de relevância/distância).

## INSTRUÇÕES DE EXECUÇÃO
Para cada uma das perguntas selecionadas:
1. Execute o comando CLI do `build_prompt.py` com a pergunta.
2. Extraia da saída: os chunks recuperados (identificados pelo atributo `documento` da tag `<chunk>`) e o score de similaridade (atributo `relevancia`).
3. Compare os chunks do gabarito.

## FORMATO DO RELATÓRIO
Para cada pergunta, documente no seguinte formato:

### Pergunta [N]: "[texto da pergunta]"

| Chunk Recuperado | Score (distância) | Presente no Gabarito? | Classificação |
|------------------|--------------------|-----------------------|---------------|
| [ID do chunk]    | [valor]            | Sim/Não               | Obrigatório / Opcional / Irrelevante |

- **Chunks obrigatórios recuperados:** X de Y
- **Chunks irrelevantes (falso positivo):** X
- **Chunks obrigatórios ausentes (falso negativo):** [lista]
- **Veredicto:** ✅ PASSOU / ⚠️ PARCIAL / ❌ FALHOU

## ANÁLISE CONSOLIDADA (ao final)
Produza uma tabela-resumo com:

| Pergunta | Recall (obrigatórios) | Falsos Positivos | Veredicto |
|----------|-----------------------|-------------------|-----------|

Seguida de:
- **Taxa de acerto global** (% de chunks obrigatórios recuperados sobre o total esperado)
```

**Resultado:**
> Disponível em [ex-1_3-analise-acuracia-retrieval.md](../.spec/ex-1_3-poc-pipeline-rag/ex-1_3-analise-acuracia-retrieval.md)

## Análise de melhorias pipeline RAG

**Contexto adicionado a sessão:**
> Disponível em [ex-1_3-analise-acuracia-retrieval.md](../.spec/ex-1_3-poc-pipeline-rag/ex-1_3-analise-acuracia-retrieval.md), [ex-1_3-teste-system-prompt-gerado.md](../.spec/ex-1_3-poc-pipeline-rag/ex-1_3-teste-system-prompt-gerado.md), [mapa-cobertura-chunks.md](../docs/mapa-cobertura-chunks.md), [ingest.py](../poc-pipeline-rag/ingest.py), [search.py](../poc-pipeline-rag/search.py) e [build_prompt.py](../poc-pipeline-rag/build_prompt.py)

**Prompt utilizado:**
```
Você é um engenheiro de IA sênior especialista em avaliação e depuração de pipelines RAG (Retrieval-Augmented Generation), com profundo conhecimento em estratégias de chunking, modelos de embedding e métricas de retrieval.

## CONTEXTO DO PROJETO

Estou avaliando uma POC de pipeline RAG para atendimento ao cliente. A arquitetura é:

- **Ingestão (`ingest.py`):** Lê 5 documentos Markdown (POL-001, PROC-042-v1, PROC-042-v2, SLA-2024, FAQ-atendimento), aplica chunking híbrido (primário por cabeçalhos Markdown `#`/`##`/`###` preservando hierarquia; secundário por tamanho fixo de 500 tokens com overlap de 50, ativado apenas em seções longas). Gera embeddings com `all-MiniLM-L6-v2` e persiste no ChromaDB.
- **Busca (`search.py`):** Recebe pergunta em texto, gera embedding com o mesmo modelo, consulta ChromaDB via distância L2, retorna top-N chunks (padrão 5).
- **Montagem de prompt (`build_prompt.py`):** Combina system prompt (XML+Markdown com guardrails de citação de fonte, proibição de invenção de dados, matriz de conflitos temporal>autoridade>escalonamento) + chunks recuperados em tags `<chunk>` com metadados + pergunta do usuário.

## TAREFA

Analise esta pipeline RAG criticamente e produza um relatório estruturado cobrindo:

### 1. DIAGNÓSTICO DE PROBLEMAS DE CHUNKING
Para cada documento da base, avalie se a estratégia de chunking híbrido (cabeçalhos + subdivisão por tamanho) preserva a integridade semântica. Identifique especificamente:
- Tabelas que podem ser cortadas no meio pela subdivisão de 500 tokens (ex: tabela SLA com 7 linhas × 4 colunas, tabela de multiplicadores regionais)
- Seções onde o overlap de 50 tokens é insuficiente para manter contexto
- Perda de metadados de cabeçalho ao subdividir seções longas (ex: FAQ com 47 itens)
- Chunks que misturam contextos de seções diferentes

### 2. DIAGNÓSTICO DE PROBLEMAS DE RETRIEVAL
Usando o gabarito, identifique cenários onde o pipeline provavelmente falhará:
- Perguntas onde o chunk errado tende a rankear acima do correto
- Documentos irrelevantes ou desatualizados que contaminam os resultados
- Perguntas de negação ("não existe tier Platinum") onde o retrieval semântico é notoriamente fraco
- Perguntas multi-domínio onde o top-5 pode não capturar todos os chunks necessários

### 3. DIAGNÓSTICO DE PROBLEMAS DE CONFLITO DE FONTES
- Identifique pares de chunks que contêm informações contraditórias
- Avalie se a matriz de resolução de conflitos no system prompt é suficiente para orientar o LLM
- Identifique cenários onde o LLM pode usar a fonte errada mesmo com os guardrails

### 4. PROPOSTAS DE CORREÇÃO
Para cada problema identificado, proponha uma correção concreta e implementável, classificada por:
- **Prioridade:** Crítica / Alta / Média / Baixa
- **Componente afetado:** Chunking / Embedding / Retrieval / Prompt / Base de documentos
- **Complexidade de implementação:** Simples / Moderada / Complexa
- **Impacto esperado:** Descreva qual cenário do gabarito será corrigido

## FORMATO DE SAÍDA
Organize o relatório com headers Markdown claros. Use tabelas para comparações. Inclua exemplos concretos referenciando os documentos e perguntas do gabarito. Priorize profundidade sobre extensão — cada problema deve ter evidência e justificativa técnica.
```

**Resultado:**
> Disponível em [ex-1_3-diagnostico-pipeline-rag.md](../.spec/ex-1_3-poc-pipeline-rag/ex-1_3-diagnostico-pipeline-rag.md)
