# Taxonomia de Skills — NovaTech Assistant

> Documento de design que governa a hierarquia de skills do projeto.
> Hierarquia: **Foundation** (convenções globais) → **Domain** (padrões por camada) → **Artifact** (receitas de geração).
> Todo agente de IA (Copilot, Claude Code) deve consultar a skill pertinente antes de gerar o artefato correspondente.

---

## Análise de raciocínio: como a repetição dita as skills

A regra de ouro da hierarquia de skills é **"o que se repete, vira skill; a camada da skill = a camada da repetição"**. Olhando os artefatos de alta repetição do NovaTech:

1. **Endpoints Azure Functions RAG "vários ao longo do projeto"** → repetição em 3 níveis simultâneos. A *forma* de toda função (handler/validator/response-builder, tratamento de erro, logging com correlation ID) é **transversal** → empurra para `foundation`. O *padrão arquitetural* do endpoint (assinatura HTTP, integração com AI Search, orçamento de contexto da ADR-0002) é **por camada** → `domain`. A *sequência concreta de passos* para parir um endpoint novo é uma **receita** → `artifact`. Um único tipo de artefato repetido se decompõe nas três camadas — esse é o sinal mais forte da taxonomia.

2. **Testes de integração para os endpoints** → como todo endpoint nasce testado, o teste é tão repetitivo quanto o endpoint. Justifica um `domain/testing-patterns` (o que testar: contrato, retrieval, contradição) + um `artifact/create-integration-test` (como montar o arquivo, fixtures, mocks de AI Search).

3. **Componentes React (cards de resposta, formulários de feedback)** → dois sub-padrões recorrentes na mesma camada (apresentação). Compartilham convenções (`domain/react-components`) mas têm receitas distintas (`create-react-card` vs. `create-feedback-form`) porque feedback envolve estado/submissão à Feedback API e card é read-only.

4. **Documentação técnica (ADRs, README de módulo)** → repetição de *formato editorial*, não de código. São puras receitas de geração → vivem só em `artifact`, sem par em `domain`.

5. **Specs SDD (requirements/plan/tasks)** → a estrutura tríade se repete em cada bounded context (`specs/feedback-api`, `query-endpoint`, etc.). A *estrutura* é um padrão de domínio do processo (`domain/sdd-spec`); o *preenchimento* de um conjunto novo é receita (`artifact/create-spec`).

6. **Decisões transversais do cenário 1 que reaparecem em todo artefato** → tratamento de erro, **logging/observabilidade** (correlation ID em Teams + painel), **config de ambiente** (segredos do Azure, sem hardcode) e o **orçamento de contexto + regra de contradição (ADR-0002/0003)**. Por serem invariantes citados em quase toda peça, viram `foundation` (ou `domain/prompt-engineering` no caso do prompt, que é específico da camada de geração).

> **Princípio de não-vazamento:** `foundation` não conhece Azure AI Search; `domain` conhece a camada mas não a sequência manual de criação; `artifact` orquestra as duas anteriores e nunca redefine convenções — apenas as referencia. Isso evita duplicação e mantém uma única fonte de verdade por regra.

---

## Árvore de skills

```text
skills/
├── foundation/                      # Convenções globais transversais
│   ├── typescript-conventions.md
│   ├── error-handling.md
│   ├── logging-observability.md     # (novo)
│   ├── environment-config.md        # (novo)
│   └── project-structure.md
│
├── domain/                          # Padrões arquiteturais por camada/domínio
│   ├── azure-functions-endpoint.md
│   ├── azure-ai-search-integration.md
│   ├── prompt-engineering.md        # (novo)
│   ├── react-components.md
│   ├── testing-patterns.md
│   └── sdd-spec.md                  # (novo)
│
└── artifact/                        # Receitas de geração (playbooks)
    ├── create-rag-endpoint.md
    ├── create-integration-test.md
    ├── create-react-card.md
    ├── create-feedback-form.md      # (novo)
    ├── create-adr.md                # (novo)
    ├── create-module-readme.md      # (novo)
    └── create-spec.md               # (novo)
```

> Os 10 arquivos sem marcação já existem como stubs vazios no repo; os 6 marcados `(novo)` são adições que o cenário justifica.

---

## Tabela detalhada

### Camada Foundation — convenções globais transversais

| Caminho/Arquivo | Propósito (problema que resolve para a IA) | Gatilhos (quando usar) |
|---|---|---|
| `/skills/foundation/typescript-conventions.md` | Padroniza naming, `strict` mode, tipos vs. interfaces, imports e formatação para que todo código gerado seja idiomático e uniforme entre backend, bot e painel. | Em **qualquer** geração ou edição de arquivo `.ts`/`.tsx`. Carregada implicitamente por toda skill de `artifact`. |
| `/skills/foundation/error-handling.md` | Define a taxonomia de erros (`src/shared/errors.ts`), quando lançar vs. tratar, mapeamento erro→HTTP status e mensagens seguras (sem vazar segredo/PII). Evita `try/catch` ad-hoc inconsistente. | Ao criar handlers de Functions, chamadas a serviços Azure (OpenAI/AI Search), ou qualquer fronteira de I/O que possa falhar. |
| `/skills/foundation/logging-observability.md` | Uso correto de `src/shared/logger.ts`: log estruturado, **correlation ID** propagado entre Teams/painel/Functions, níveis de log e proibição de logar conteúdo sensível. Garante rastreabilidade exigida pelo dashboard de métricas. | Em todo handler, serviço e pipeline de ingestão; sempre que a IA for adicionar instrumentação ou diagnosticar comportamento. |
| `/skills/foundation/environment-config.md` | Como ler configuração via `src/shared/config.ts`: variáveis de ambiente, segredos do Azure (Key Vault), proibição de hardcode de endpoints/keys e validação na inicialização. | Ao introduzir qualquer nova dependência de config (endpoint AI Search, deployment OpenAI, connection strings) ou consumir credenciais. |
| `/skills/foundation/project-structure.md` | Mapa de onde cada coisa mora (`functions/`, `services/`, `pipeline/`, `bot/`, `web/`, `shared/`) e regras de dependência entre camadas. Impede que a IA crie arquivos no lugar errado ou crie acoplamento indevido. | Antes de criar qualquer arquivo novo; ao decidir onde colocar lógica compartilhada vs. específica de camada. |

### Camada Domain — padrões arquiteturais por camada

| Caminho/Arquivo | Propósito (problema que resolve para a IA) | Gatilhos (quando usar) |
|---|---|---|
| `/skills/domain/azure-functions-endpoint.md` | Padrão de endpoint HTTP em Azure Functions (TS): contrato de request/response, separação `handler`/`validator`/`response-builder`, binding e ciclo de vida. Define a "forma" de toda função. | Ao criar ou modificar qualquer endpoint sob `src/functions/` (query, feedback, health). |
| `/skills/domain/azure-ai-search-integration.md` | Padrões da camada de retrieval: query ao Azure AI Search, top-K=5 chunks, filtro por **metadado de vigência** (ADR-0003), tratamento de tabelas (ADR-0004) e formato dos chunks. | Ao implementar/ajustar `services/search.ts` ou qualquer recuperação de documentos para o RAG. |
| `/skills/domain/prompt-engineering.md` | Regras de construção de prompt e **gerência de contexto da ADR-0002**: budget ~4K system + ~8K chunks + histórico de 3 turnos, instrução de priorizar versão mais recente em contradições, formato de citação de fontes. Governa `services/prompt-builder.ts` e `prompts/`. | Ao montar prompts, alterar `system-prompt.md`, ajustar janela de contexto ou tratar documentos contraditórios. |
| `/skills/domain/react-components.md` | Arquitetura front-end do painel: estrutura de componentes, props/estado, organização em `components/`/`pages/`, acessibilidade e consumo das APIs internas. | Ao criar ou editar qualquer componente em `src/web/src/`. |
| `/skills/domain/testing-patterns.md` | O que e como testar por camada: pirâmide (unit/integration/e2e), uso de fixtures, mocks de AI Search/OpenAI, e os **cenários de falha mapeados pelo QA** (contradição, sem-resposta, alucinação). | Antes de escrever qualquer teste; ao decidir cobertura e estratégia de mock. |
| `/skills/domain/sdd-spec.md` | Estrutura do Spec-Driven Development: o tríade `requirements.md` / `plan.md` / `tasks.md`, linguagem ubíqua e fronteiras de bounded context. Garante specs consistentes entre módulos. | Ao iniciar a especificação de um novo bounded context ou revisar/estender specs existentes em `specs/`. |

### Camada Artifact — receitas de geração (playbooks)

| Caminho/Arquivo | Propósito (problema que resolve para a IA) | Gatilhos (quando usar) |
|---|---|---|
| `/skills/artifact/create-rag-endpoint.md` | Receita passo-a-passo para gerar um endpoint RAG completo: scaffold handler+validator+response-builder, fiar AI Search → prompt-builder → completion, aplicar erro/log/config e gerar o teste de integração par. Orquestra domain + foundation. | "Criar um novo endpoint RAG/de consulta", adicionar nova rota que consulta a base documental. |
| `/skills/artifact/create-integration-test.md` | Template para teste de integração de endpoint: arrange de fixtures, mocks de Azure, asserts de contrato + cenários de falha do QA, localização em `tests/integration/`. | Logo após criar/alterar um endpoint, ou quando pedido "escrever testes de integração". |
| `/skills/artifact/create-react-card.md` | Receita para card de resposta no painel (read-only): exibição de resposta + citações de fontes + metadados de confiança, seguindo `react-components`. | "Criar um card de resposta/exibir resultado" no painel web. |
| `/skills/artifact/create-feedback-form.md` | Receita para formulário de feedback: estado controlado, validação, submissão à Feedback API, estados de loading/erro/sucesso. Distinta do card por envolver mutação. | "Criar formulário de feedback / avaliação de resposta" no painel. |
| `/skills/artifact/create-adr.md` | Template de ADR (contexto, decisão, alternativas, consequências, status) consistente com ADR-0001..0004 do cenário 1. Padroniza o registro de decisões arquiteturais. | Ao tomar/documentar uma decisão arquitetural relevante ou quando pedido "registrar uma ADR". |
| `/skills/artifact/create-module-readme.md` | Template de README de módulo: propósito, contratos, como rodar/testar, dependências. Resolve documentação técnica heterogênea entre módulos. | Ao criar um módulo novo ou documentar um existente sem README. |
| `/skills/artifact/create-spec.md` | Receita para gerar o conjunto SDD completo (`requirements/plan/tasks`) de um bounded context novo, aplicando o padrão de `domain/sdd-spec`. | "Especificar uma nova feature/módulo via SDD", iniciar uma nova pasta em `specs/`. |

---

## Observações de fronteira (anti-duplicação)

- Os **Adaptive Cards do Teams** (`src/bot/cards/`) também são artefatos repetidos; se virarem foco, recomenda-se `domain/teams-adaptive-cards.md` + `artifact/create-teams-card.md` — deixados de fora por ora porque o cenário enfatiza o *painel web React*.
- Toda skill de `artifact` deve **referenciar** (não recopiar) as de `domain`/`foundation`, mantendo fonte única de verdade.
