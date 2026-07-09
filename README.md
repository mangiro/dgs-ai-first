# DGS AI-First

Repositório de trilha prática do programa **DGS AI-First**, iniciativa da DB1 para desenvolver competências aplicadas em Inteligência Artificial com foco em engenharia, produto e entrega de valor real.

A trilha é organizada em **Cenários** — projetos fictícios mas realistas que simulam demandas de clientes. Cada cenário atravessa fases progressivas de entendimento, construção e evolução de soluções com IA.

---

## Cenários

### Cenário-Âncora 1 — Fase de Entendimento e Contexto

A fase de entendimento cobre as etapas iniciais de um projeto de IA: análise de viabilidade, design de prompt e construção de um pipeline RAG funcional com ferramentas open-source.

| # | Atividade |
|---|-----------|
| 1.1 | Análise de Viabilidade Técnica — avaliação do cenário e justificativa da abordagem RAG |
| 1.2 | Prototipação de Prompt e Engenharia de Contexto — design e iteração do system prompt com guardrails |
| 1.3 | Construção de Pipeline RAG — ingestão, busca semântica e montagem de prompt com ChromaDB |

Acesse as atividades, evidências e o código da POC na branch [`cenario-1`](https://github.com/mangiro/dgs-ai-first/tree/cenario-1).

### Cenário-Âncora 2 — Fase de Estruturação do Trabalho

A fase de estruturação cobre a montagem do ambiente, dos padrões e dos artefatos que governam o desenvolvimento assistido por IA: configuração de servidores MCP, adoção de Spec Driven Development e definição de uma estratégia de skills para o projeto.

| # | Atividade |
|---|-----------|
| 2.1 | Configuração e uso real de MCP servers no projeto |
| 2.2 | Implementação de spec com Spec Driven Development |
| 2.3 | Definição de estratégia de skills do projeto |

Acesse as atividades, evidências e o código do projeto na branch [`cenario-2`](https://github.com/mangiro/dgs-ai-first/tree/cenario-2).

### Cenário-Âncora 3 — Fase de Governança e Validação

A fase de governança cobre a validação de saídas de IA e a revisão crítica de código gerado por modelos: guardrails determinísticos sobre respostas estruturadas (structured output) e um fluxo human-in-the-loop que confronta revisão humana e revisão por IA de código, garantindo conformidade com a *constitution* do projeto.

| # | Atividade |
|---|-----------|
| 3.1 | Structured output e verificações determinísticas — validação de resposta do LLM com Zod e guardrails determinísticos, com fallback seguro |
| 3.2 | Revisão crítica de código gerado por IA (human-in-the-loop) — revisão humana vs. IA e análise comparativa das abordagens |

Acesse as atividades, evidências e o código do projeto na branch [`cenario-3`](https://github.com/mangiro/dgs-ai-first/tree/cenario-3).
