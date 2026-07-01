# DGS AI-First: Cenário-Âncora 2 — Fase de Estruturação do Trabalho

Repositório de exercícios práticos do programa **DGS AI-First**, referentes ao **Cenário-Âncora 2 (Fase de Estruturação do Trabalho)** no papel de **Desenvolvedor**, com foco na estruturação do ambiente, dos padrões e dos artefatos que governam o desenvolvimento assistido por IA do assistente de atendimento da NovaTech Logística.

## Estrutura do repositório

```
dgs-ai-first/
├── docs/                                          # Documentação de apoio e análises do projeto
│   ├── cenario-novatech.md                        # Cenário de negócio (NovaTech Logística)
│   ├── mcp-architecture.md                        # Arquitetura dos servidores MCP
│   ├── mcp-security-analysis.md                   # Análise de segurança da configuração MCP
│   ├── ex-2_2-analise-critica-pre-code-review.md  # Revisão crítica de código (pré-code review)
│   ├── ex-2_3-skills-taxonomy.md                  # Taxonomia de skills do projeto
│   └── ex-2_3-skills-triggers.md                  # Mapeamento de skills (ciclo de vida e aplicação)
├── evidencias/                                    # Evidências das atividades entregues
│   ├── ex-2_1-config-uso-real-mcp-servers.md
│   ├── ex-2_2-implementacao-spec-driven-development.md
│   ├── ex-2_3-definicao-estrategia-skills.md
│   └── prints/                                    # Capturas de tela que comprovam as execuções
└── novatech-assistant/                            # Starter repo do projeto (ver seção abaixo)
    ├── .mcp/                                       # Configuração dos servidores MCP
    ├── AGENTS.md                                   # Instruções para os agentes de IA
    ├── docs/novatech/                              # Documentos de negócio (fonte do filesystem MCP)
    ├── data/retrieval-corpus/                      # Chunks de referência para RAG
    ├── specs/                                      # Specs (Spec Driven Development)
    ├── skills/                                     # Skill tree (foundation, domain, artifact)
    ├── prompts/                                    # System prompt, changelog e evals
    ├── src/                                        # Código-fonte TypeScript (pipeline, functions, bot, web)
    └── infra/                                      # Infraestrutura como código (Bicep)
```

## Atividades

| # | Título | Evidências |
|---|--------|-----------|
| 2.1 | Configuração e uso real de MCP servers no projeto | [evidencias/ex-2_1-config-uso-real-mcp-servers.md](evidencias/ex-2_1-config-uso-real-mcp-servers.md) |
| 2.2 | Implementação de spec com Spec Driven Development | [evidencias/ex-2_2-implementacao-spec-driven-development.md](evidencias/ex-2_2-implementacao-spec-driven-development.md) |
| 2.3 | Definição de estratégia de skills do projeto | [evidencias/ex-2_3-definicao-estrategia-skills.md](evidencias/ex-2_3-definicao-estrategia-skills.md) |
