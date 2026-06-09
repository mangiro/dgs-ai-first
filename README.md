# dgs-ai-first

Repositório de exercícios práticos do programa **DGS AI-First**, com foco em engenharia de IA aplicada a casos de atendimento ao cliente.

## Estrutura do repositório

```
dgs-ai-first/
├── docs/                        # Documentação de apoio e análises do projeto
│   ├── cenario-novatech.md      # Cenário de negócio (NovaTech Logística)
│   ├── mapa-cobertura-chunks.md # Gabarito de cobertura dos chunks por pergunta
│   └── prototipacao-de-prompt-engenharia-de-contexto.md
├── evidencias/                  # Evidências das atividades entregues
│   ├── ex-1_1-analise-viabilidade-tecnica.md
│   ├── ex-1_2-system-prompt.md
│   └── ex-1_3-poc-pipeline-rag.md
└── poc-pipeline-rag/            # POC do pipeline RAG (ver seção abaixo)
    ├── docs/                    # Base de documentos para ingestão
    ├── ingest.py                # Etapa 1: ingestão e indexação
    ├── search.py                # Etapa 2: busca semântica
    ├── build_prompt.py          # Etapa 3: montagem do prompt para o LLM
    └── requirements.txt
```

## Atividades

| # | Título | Evidências |
|---|--------|-----------|
| 1.1 | Análise de Viabilidade Técnica RAG NovaTech | [evidencias/ex-1_1-analise-viabilidade-tecnica.md](evidencias/ex-1_1-analise-viabilidade-tecnica.md) |
| 1.2 | Prototipação de Prompt e Engenharia de Contexto | [evidencias/ex-1_2-system-prompt.md](evidencias/ex-1_2-system-prompt.md) |
| 1.3 | Construção de Pipeline de RAG com ferramentas open-source | [evidencias/ex-1_3-poc-pipeline-rag.md](evidencias/ex-1_3-poc-pipeline-rag.md) |

---

## poc-pipeline-rag

POC de pipeline RAG para o sistema de atendimento ao cliente da NovaTech Logística. O pipeline processa documentos Markdown, gera embeddings e permite busca semântica + montagem de prompt estruturado para envio a um LLM.

### Arquitetura do pipeline

```
docs/*.md  →  ingest.py  →  ChromaDB
                               ↓
pergunta  →  search.py  →  chunks relevantes
                               ↓
                         build_prompt.py  →  prompt XML pronto para o LLM
```

### Pré-requisitos

- Python 3.12+

### Instalação

```bash
cd poc-pipeline-rag

# Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Etapa 1 — Ingestão (`ingest.py`)

Lê os documentos `.md` de `docs/`, aplica chunking híbrido (por cabeçalhos + subdivisão por tamanho), gera embeddings com `all-MiniLM-L6-v2` e persiste tudo no ChromaDB local.

```bash
python ingest.py
```

Saída esperada ao final:

```
============================================================
RESUMO DA INGESTÃO
============================================================
  Documentos processados:  5
  Chunks gerados:          42
  Tempo de execução:       8.34s
============================================================
```

> O banco vetorial é salvo em `chroma_db/`. Re-executar o script é seguro — o upsert atualiza os registros sem duplicar.

### Etapa 2 — Busca semântica (`search.py`)

Recebe uma pergunta em linguagem natural, gera o embedding e consulta o ChromaDB retornando os chunks mais similares.

```bash
python search.py "Qual é a política de devolução para produtos danificados?"
```

Parâmetros opcionais:

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--top-n` | `5` | Quantidade de chunks a retornar |
| `--db-path` | `./chroma_db` | Caminho do banco ChromaDB |

Exemplo com parâmetros:

```bash
python search.py "Qual o SLA para clientes Gold?" --top-n 3
```

> **Pré-requisito:** executar `ingest.py` antes. Se o banco não existir, o script exibe mensagem de erro orientando a executar a ingestão.

### Etapa 3 — Montagem do prompt (`build_prompt.py`)

Combina o system prompt estático (guardrails de citação de fonte, proibição de invenção de dados, matriz de resolução de conflitos) com os chunks recuperados e a pergunta do usuário, montando o prompt XML completo pronto para colar em um LLM.

```bash
python build_prompt.py "Como calcular o frete especial para cargas acima de 500 kg?"
```

Parâmetros opcionais:

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--top-n` | `5` | Quantidade de chunks a incluir no contexto |
| `--db-path` | `./chroma_db` | Caminho do banco ChromaDB |

A saída é o prompt completo no stdout, com três blocos XML:

- `<system>` — instruções e guardrails do assistente NovaTech
- `<contexto>` — chunks recuperados com metadados (documento, seção, índice, score)
- `<pergunta>` — a pergunta original

### Execução completa do pipeline

```bash
cd poc-pipeline-rag
source .venv/bin/activate

# 1. Indexar os documentos (necessário apenas na primeira vez ou após alterar docs/)
python ingest.py

# 2. Verificar quais chunks são recuperados para uma pergunta
python search.py "Qual o prazo de entrega para a região Sul?"

# 3. Montar o prompt completo para enviar ao LLM
python build_prompt.py "Qual o prazo de entrega para a região Sul?"
```

### Base de documentos (`docs/`)

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `POL-001-politica-devolucao.md` | Política | Regras de devolução e reembolso |
| `PROC-042-frete-especial-v1.md` | Procedimento v1 | Cálculo de frete especial (versão original) |
| `PROC-042-v2-frete-especial-revisado.md` | Procedimento v2 | Cálculo de frete especial (versão revisada) |
| `SLA-2024-tabela-sla-clientes.md` | Planilha | Tabela de SLAs por tier de cliente |
| `FAQ-atendimento.md` | FAQ | Perguntas frequentes de atendimento |
