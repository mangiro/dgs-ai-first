# DGS AI-First: Cenário-Âncora 3 — Fase de Governança e Validação

Repositório de exercícios práticos do programa **DGS AI-First**, referentes ao **Cenário-Âncora 3 (Fase de Governança e Validação)** no papel de **Desenvolvedor**, com foco na validação de saídas de IA, nos guardrails determinísticos e na revisão crítica (human-in-the-loop) de código gerado por IA para o assistente de atendimento da NovaTech Logística.

## Estrutura do repositório

```
dgs-ai-first/
├── docs/                                          # Documentação de apoio e análises do projeto
│   ├── cenario-novatech.md                        # Cenário de negócio (NovaTech Logística)
│   ├── mcp-architecture.md                        # Arquitetura dos servidores MCP
│   ├── mcp-security-analysis.md                   # Análise de segurança da configuração MCP
│   ├── skills-taxonomy.md                         # Taxonomia de skills do projeto
│   ├── skills-triggers.md                         # Mapeamento de skills (ciclo de vida e aplicação)
│   ├── ex-3_1-code-review-response-validator.md   # Code review do response-validator (structured output)
│   ├── ex-3_2-human-code-review-handler.md        # Revisão humana do feedback/handler.ts
│   ├── ex-3_2-ai-code-review-handler.md           # Revisão por IA do feedback/handler.ts
│   └── ex-3_2-analise-comparativa-code-reviews.md # Análise comparativa: revisão humana vs. IA
├── evidencias/                                    # Evidências das atividades entregues
│   ├── ex-3_1-structured-output-verificacoes-deterministicas.md
│   ├── ex-3_2-revisao-critica-codigo-ia.md
│   └── prints/                                    # Capturas de tela que comprovam as execuções
└── novatech-assistant/                            # Starter repo do projeto (ver seção abaixo)
    ├── .mcp/                                       # Configuração dos servidores MCP
    ├── AGENTS.md                                   # Constitution: regras para os agentes de IA
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
| 3.1 | Structured output e verificações determinísticas (harness de código) | [evidencias/ex-3_1-structured-output-verificacoes-deterministicas.md](evidencias/ex-3_1-structured-output-verificacoes-deterministicas.md) |
| 3.2 | Revisão crítica de código gerado por IA (human-in-the-loop) | [evidencias/ex-3_2-revisao-critica-codigo-ia.md](evidencias/ex-3_2-revisao-critica-codigo-ia.md) |

### 3.1 — Structured output e verificações determinísticas

Implementação do `src/services/response-validator.ts`: a fronteira de confiança entre a saída do LLM e o restante do sistema. O módulo valida a resposta estruturada do modelo (`{ answer, source_document, confidence_score }`) com **Zod** e aplica dois guardrails determinísticos — obrigatoriedade de fonte e restrição de "carga perigosa + devolução" (POL-001). Em qualquer falha (formato inválido, fonte ausente ou violação de guardrail), a resposta original é descartada e um *fallback* seguro é retornado. O exercício inclui um code review do próprio validador e a aplicação das correções.

### 3.2 — Revisão crítica de código gerado por IA

Revisão crítica (human-in-the-loop) de um módulo `src/functions/feedback/handler.ts` gerado por IA que violava o `AGENTS.md` (uso de `any`, `console.log`, log de PII, `require` dinâmico, ausência de validação com Zod). O exercício confronta uma **revisão feita por humano** com uma **revisão feita por IA** do mesmo código, produz uma **análise comparativa** das duas abordagens e culmina na reescrita do handler em conformidade com a *constitution* do projeto.

---

## novatech-assistant

Starter repo do assistente de atendimento da NovaTech Logística. Projeto **TypeScript (ESM)** para **Node.js 20 / Azure Functions**, com validação via **Zod**, logging via **pino**, testes com **Vitest** e build com `tsc`. As regras de engenharia (modo estrito, validação exclusiva com Zod, logging sem PII, imports estáticos) vivem no `novatech-assistant/AGENTS.md` e governam todo código — humano ou gerado por IA.

### Pré-requisitos

- Node.js 20 LTS

### Instalação

```bash
cd novatech-assistant
npm install
```

### Portão de qualidade

Antes de mesclar qualquer artefato (inclusive gerado por IA), `lint` + `build` + `test` devem passar:

| Ação   | Comando         | Descrição                                                    |
|--------|-----------------|-------------------------------------------------------------|
| Testar | `npm test`      | Executa a suíte com Vitest (`vitest run`).                  |
| Lint   | `npm run lint`  | Roda ESLint (barra `no-console` e imports proibidos).       |
| Build  | `npm run build` | Compila com `tsc -p .` para `dist/` (falha em erro de tipo).|

> Como o build usa `strict: true`, qualquer violação de tipo quebra a compilação — a checagem de tipos faz parte do gate, não é opcional. Nenhum artefato entra sem passar por este portão e por revisão humana (human-in-the-loop) das regras de Coding Standards do `AGENTS.md`.
