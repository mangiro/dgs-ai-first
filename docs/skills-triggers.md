# Mapeamento de Skills — Ciclo de Vida e Aplicação

> Extração estruturada da [Taxonomia de Skills do NovaTech Assistant](./ex-2_3-skills-taxonomy.md).
> Para cada skill: frase de ativação que o agente reconhece, papel responsável pela criação, consumidores (humanos + agentes de IA) e frequência de uso estimada.
> Hierarquia: **Foundation** (convenções globais) → **Domain** (padrões por camada) → **Artifact** (receitas de geração).

---

## Tabela de mapeamento

| Nome da Skill | Descrição / Frase de Ativação | Quem Cria | Quem Consome | Frequência de Uso |
|---|---|---|---|---|
| `typescript-conventions` (Foundation) | "Vou gerar/editar qualquer arquivo `.ts`/`.tsx`" — disparada implicitamente em toda escrita de código. | Tech Lead + Dev Sênior | Devs (pleno/sênior); **Claude Code**, **Copilot** (carregada implicitamente por toda skill `artifact`) | **Alta** (diária — quase todo turno de código) |
| `error-handling` (Foundation) | "Criar handler de Function / chamar serviço Azure / cruzar fronteira de I/O que pode falhar." | Dev Sênior + Tech Lead | Devs backend; QA (validação); **Claude Code**, **Copilot** | **Alta** (diária) |
| `logging-observability` (Foundation) | "Adicionar instrumentação / propagar correlation ID / diagnosticar comportamento em handler ou pipeline." | Tech Lead | Devs; QA; Delivery Manager (métricas); **Claude Code**, **Copilot** | **Média-Alta** (quase diária em código novo) |
| `environment-config` (Foundation) | "Introduzir nova dependência de config / consumir segredo do Azure (Key Vault) / endpoint / connection string." | Tech Lead | Devs; **Claude Code**, **Copilot** | **Média** (semanal — a cada nova integração) |
| `project-structure` (Foundation) | "Onde colocar este arquivo? / onde mora lógica compartilhada vs. específica de camada?" | Tech Lead | Devs; **Claude Code**, **Copilot** | **Alta** (consultada antes de criar qualquer arquivo) |
| `azure-functions-endpoint` (Domain) | "Criar ou modificar endpoint HTTP sob `src/functions/` (query, feedback, health)." | Dev Sênior + Tech Lead | Devs backend; **Claude Code**, **Copilot** | **Alta** (núcleo da fase de desenvolvimento) |
| `azure-ai-search-integration` (Domain) | "Implementar/ajustar `services/search.ts` ou recuperação de documentos para o RAG (top-K=5, filtro de vigência)." | Dev Sênior (especialista RAG/retrieval) | Devs backend; QA (cenários de retrieval); **Claude Code**, **Copilot** | **Média-Alta** (semanal) |
| `prompt-engineering` (Domain) | "Montar prompt / alterar `system-prompt.md` / ajustar janela de contexto / tratar documentos contraditórios (ADR-0002/0003)." | Engenheiro de Prompt + Product Specialist (domínio) | Devs backend; Product Specialist; **Claude Code**, **Copilot** | **Média** (semanal; picos em tuning) |
| `react-components` (Domain) | "Criar ou editar componente em `src/web/src/` (painel interno)." | Dev (front-end) | Devs front; **Claude Code**, **Copilot** | **Média** (semanal) |
| `testing-patterns` (Domain) | "Antes de escrever qualquer teste / decidir cobertura, mocks de AI Search/OpenAI e cenários de falha do QA." | QA | QA; Devs; **Claude Code**, **Copilot** | **Alta** (todo endpoint nasce testado) |
| `sdd-spec` (Domain) | "Iniciar especificação de novo bounded context / estender specs em `specs/` (tríade requirements/plan/tasks)." | Product Specialist + Tech Lead | Product Specialist; Tech Lead; Devs; **Claude Code** | **Baixa** (sob demanda — por novo módulo/contexto) |
| `create-rag-endpoint` (Artifact) | **"Criar um novo endpoint RAG / de consulta"**; "adicionar rota que consulta a base documental." | Dev Sênior | Devs backend; **Claude Code**, **Copilot** | **Alta** (artefato de maior repetição do projeto) |
| `create-integration-test` (Artifact) | **"Escrever testes de integração"** — disparada logo após criar/alterar um endpoint. | QA | QA; Devs; **Claude Code**, **Copilot** | **Alta** (pareada a cada endpoint) |
| `create-react-card` (Artifact) | **"Criar um card de resposta / exibir resultado"** no painel web (read-only, com citações). | Dev (front-end) | Devs front; **Claude Code**, **Copilot** | **Média** (semanal) |
| `create-feedback-form` (Artifact) | **"Criar formulário de feedback / avaliação de resposta"** (estado controlado + submissão à Feedback API). | Dev (front-end) | Devs front; **Claude Code**, **Copilot** | **Baixa-Média** (poucas instâncias no painel) |
| `create-adr` (Artifact) | **"Registrar uma ADR"** / "documentar decisão arquitetural relevante." | Tech Lead | Tech Lead; Product Specialist; Devs Sênior; **Claude Code** | **Baixa** (sob demanda — por decisão) |
| `create-module-readme` (Artifact) | **"Documentar este módulo / criar README"** para módulo novo ou sem documentação. | Dev (autor do módulo) | Devs; Delivery Manager; **Claude Code**, **Copilot** | **Baixa** (mensal / por módulo novo) |
| `create-spec` (Artifact) | **"Especificar nova feature/módulo via SDD"** / "iniciar nova pasta em `specs/`" (gera tríade completa). | Product Specialist | Product Specialist; Tech Lead; Devs; **Claude Code** | **Baixa** (sob demanda — por bounded context) |

---

## Notas de leitura da tabela

- **Consumo dual (humano + agente):** toda skill é consumida por agentes de IA (Claude Code/Copilot) *e* pelo papel humano que revisa/dispara o artefato — o agente gera, o humano valida. As skills `foundation` são consumidas de forma majoritariamente implícita pelos agentes (carregadas por toda receita `artifact`).
- **Padrão de frequência por camada:** `foundation` tende a **Alta** (transversal, quase todo turno); `domain` varia **Média-Alta** conforme a camada está em foco; `artifact` espelha a frequência do artefato que geram — endpoints/testes em **Alta**, documentação (ADR/README/spec) em **Baixa/sob demanda**.
- **Criação concentrada em papéis sênior:** Tech Lead e Dev Sênior criam o núcleo `foundation`/`domain` arquitetural; QA detém as skills de teste; Product Specialist + Engenheiro de Prompt detêm o domínio de prompt e SDD.
