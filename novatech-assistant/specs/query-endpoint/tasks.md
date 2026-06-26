# Tasks — Query Endpoint

> Gerado a partir de `specs/query-endpoint/plan.md`.
> Granularidade atômica: cada tarefa pode ser desenvolvida, testada e integrada de forma independente.

---

## TSK-001 — Definir tipos compartilhados do domínio

**Descrição:** Implementar `src/shared/types.ts` com as interfaces e tipos que percorrem todas as camadas do endpoint: `QueryRequest`, `QueryResponse`, `DocumentChunk`, `SearchResult`.

**Critérios de Aceite:**
- `QueryRequest` contém `question: string` e `session_id?: string`
- `DocumentChunk` contém `id`, `content`, `source_document`, `vigencia` (metadado ADR-0003) e `score?: number`
- `QueryResponse` contém `answer: string` e `sources: Pick<DocumentChunk, 'source_document' | 'vigencia'>[]`
- Arquivo compila sem erros com `tsc --noEmit`
- Nenhum import de módulos externos (tipos puros)

**Dependências:** Nenhuma

**Estimativa:** P

---

## TSK-002 — Implementar módulo de configuração por variáveis de ambiente

**Descrição:** Implementar `src/shared/config.ts` que lê e valida todas as variáveis de ambiente necessárias na inicialização, expondo um objeto `config` tipado.

**Critérios de Aceite:**
- Lê: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`, `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_KEY`, `AZURE_SEARCH_INDEX`
- Lança erro descritivo no startup se qualquer variável obrigatória estiver ausente
- Expõe constantes de budget: `SYSTEM_PROMPT_TOKEN_BUDGET = 4096`, `CHUNKS_TOKEN_BUDGET = 8192`
- Arquivo compila sem erros com `tsc --noEmit`

**Dependências:** Nenhuma

**Estimativa:** P

---

## TSK-003 — Configurar instância de logger estruturado (pino)

**Descrição:** Implementar `src/shared/logger.ts` exportando instância pino pré-configurada para uso em todo o projeto. Nenhum `console.log` deve existir no codebase após esta tarefa.

**Critérios de Aceite:**
- Exporta `logger` (instância pino) com `level` configurável via `LOG_LEVEL` (default: `info`)
- Exporta helper `childLogger(context: Record<string, unknown>)` para criar child loggers com campos extras
- Importável e utilizável em `services/` e `functions/` sem configuração adicional
- Arquivo compila sem erros

**Dependências:** Nenhuma

**Estimativa:** P

---

## TSK-004 — Definir hierarquia de erros de domínio

**Descrição:** Implementar `src/shared/errors.ts` com classes de erro tipadas que distinguem falhas de validação, busca, completude e orçamento de contexto.

**Critérios de Aceite:**
- `ValidationError` (statusCode 400): input inválido do usuário
- `SearchError` (statusCode 502): falha na chamada ao Azure AI Search
- `CompletionError` (statusCode 502): falha na chamada ao Azure OpenAI
- `ContextBudgetError` (statusCode 500): prompt montado excede o limite máximo configurado
- Todas estendem `Error` e expõem `statusCode: number` e `cause?: unknown`
- Arquivo compila sem erros

**Dependências:** Nenhuma

**Estimativa:** P

---

## TSK-005 — Implementar validador Zod para input do endpoint

**Descrição:** Implementar `src/functions/query/validator.ts` com schema Zod e função `validateQueryRequest` que parseia e valida o body HTTP, lançando `ValidationError` em caso de falha.

**Critérios de Aceite:**
- Schema Zod: `question` (string, min 1, max 500), `session_id` (string uuid, opcional)
- `validateQueryRequest(body: unknown): QueryRequest` lança `ValidationError` com mensagem legível se inválido
- Nenhum tipo `any` no arquivo
- Arquivo compila com `strict: true`

**Dependências:** TSK-001, TSK-004

**Estimativa:** P

---

## TSK-006 — Implementar serviço de busca semântica no Azure AI Search

**Descrição:** Implementar `src/services/search.ts` com duas funções: geração de embedding da pergunta via Azure OpenAI Embeddings API e busca dos top-K chunks via Azure AI Search (vector search).

**Critérios de Aceite:**
- `embedQuestion(question: string): Promise<number[]>` chama Azure OpenAI Embeddings com o deployment configurado em `config`
- `searchChunks(embedding: number[], topK = 5): Promise<DocumentChunk[]>` chama Azure AI Search com vector query
- Ambas as funções implementam retry com exponential backoff (3 tentativas, delays: 500ms → 1000ms → 2000ms)
- Erros de rede/timeout lançam `SearchError`
- Todas as chamadas logadas via `logger` (request id, latência)
- Nenhum `console.log`; tipos retornados são `DocumentChunk[]` conforme `types.ts`

**Dependências:** TSK-001, TSK-002, TSK-003, TSK-004

**Estimativa:** M

---

## TSK-007 — Implementar serviço de completion via Azure OpenAI (GPT-4o)

**Descrição:** Implementar `src/services/completion.ts` com função `completeWithPrompt` que envia o prompt montado ao GPT-4o e retorna a resposta em texto.

**Critérios de Aceite:**
- `completeWithPrompt(prompt: string): Promise<string>` chama `chat/completions` no deployment configurado em `config`
- Implementa retry com exponential backoff (3 tentativas, mesma estratégia de TSK-006)
- Erros de rede/timeout lançam `CompletionError`
- Resposta `null` ou vazia do modelo lança `CompletionError` com mensagem descritiva
- Chamada logada com latência e tokens consumidos (se disponível no response)

**Dependências:** TSK-001, TSK-002, TSK-003, TSK-004

**Estimativa:** M

---

## TSK-008 — Implementar prompt builder com controle de context budget

**Descrição:** Implementar `src/services/prompt-builder.ts` com função `buildPrompt` que monta o prompt final respeitando o budget de tokens definido na ADR-0002 (~4K system + ~8K chunks).

**Critérios de Aceite:**
- `buildPrompt(question: string, chunks: DocumentChunk[]): string` retorna prompt no formato: system prompt + chunks ordenados por score + pergunta do usuário
- Lê o system prompt de `prompts/system-prompt.md` em runtime
- Estima tokens por aproximação (1 token ≈ 4 chars) e trunca chunks excedentes ao `CHUNKS_TOKEN_BUDGET`
- Se mesmo um único chunk não couber no budget, lança `ContextBudgetError`
- Cada chunk incluído referencia `source_document` e `vigencia` para rastreabilidade (ADR-0003)
- Loga aviso quando chunks são descartados por limite de budget

**Dependências:** TSK-001, TSK-002, TSK-003, TSK-004

**Estimativa:** M

---

## TSK-009 — Implementar response builder para saída HTTP do endpoint

**Descrição:** Implementar `src/functions/query/response-builder.ts` com função `buildQueryResponse` que formata a resposta HTTP final com `answer` e lista de `sources`.

**Critérios de Aceite:**
- `buildQueryResponse(answer: string, chunks: DocumentChunk[]): QueryResponse` retorna objeto conforme `types.ts`
- `sources` deduplica por `source_document` (mesmo doc pode aparecer em múltiplos chunks)
- Ordenação de `sources` por `vigencia` decrescente (documento mais recente primeiro, alinhado ADR-0003)
- Arquivo compila sem erros; sem lógica de chamada HTTP diretamente aqui

**Dependências:** TSK-001

**Estimativa:** P

---

## TSK-010 — Implementar handler principal do query endpoint

**Descrição:** Substituir o stub em `src/functions/query/handler.ts` pela implementação completa da Azure Function v4 HTTP trigger, orquestrando todas as camadas.

**Critérios de Aceite:**
- Function registrada como `app.http('query', { methods: ['POST'], route: 'query', handler: queryHandler })`
- Fluxo: `validateQueryRequest` → `embedQuestion` → `searchChunks` → `buildPrompt` → `completeWithPrompt` → `buildQueryResponse`
- HTTP 200 com `QueryResponse` em caso de sucesso
- HTTP 400 para `ValidationError` com mensagem de erro legível
- HTTP 502 para `SearchError` ou `CompletionError`
- HTTP 500 para erros inesperados (sem vazar stack trace ao cliente)
- Cada etapa logada com `requestId` (gerado via `crypto.randomUUID()`) e duração

**Dependências:** TSK-005, TSK-006, TSK-007, TSK-008, TSK-009

**Estimativa:** M

---

## TSK-011 — Criar fixtures de teste para chunks e queries

**Descrição:** Implementar `tests/fixtures/chunks.ts` e `tests/fixtures/queries.ts` com dados mock estáticos reutilizáveis nos testes unitários e de integração.

**Critérios de Aceite:**
- `tests/fixtures/chunks.ts`: exporta array de 5 `DocumentChunk` com `score`, `source_document` e `vigencia` variados (incluindo 1 chunk de documento obsoleto para testar ADR-0003)
- `tests/fixtures/queries.ts`: exporta `validQuery` (QueryRequest bem formado) e `invalidQuery` (sem `question`)
- Fixtures tipadas com os tipos de `src/shared/types.ts`
- Nenhuma dependência de biblioteca de mock — dados literais

**Dependências:** TSK-001

**Estimativa:** P

---

## TSK-012 — Testes unitários para o validador de input

**Descrição:** Criar `tests/unit/validator.test.ts` cobrindo o happy path e os casos de falha do validador Zod.

**Critérios de Aceite:**
- Passa: `question` válida com e sem `session_id`
- Falha com `ValidationError`: `question` vazia, `question` com 501+ chars, body nulo, body sem `question`
- `session_id` inválido (não-UUID) lança `ValidationError`
- Todos os testes rodam com `vitest run` sem dependências externas
- Cobertura das branches do validator: 100%

**Dependências:** TSK-005, TSK-011

**Estimativa:** P

---

## TSK-013 — Testes unitários para o prompt builder (budget de contexto)

**Descrição:** Criar `tests/unit/prompt-builder.test.ts` cobrindo a montagem do prompt e a aplicação do context budget da ADR-0002.

**Critérios de Aceite:**
- Prompt montado contém system prompt + chunks + question na ordem correta
- Com 5 chunks dentro do budget: todos incluídos
- Com chunks que excedem `CHUNKS_TOKEN_BUDGET`: chunks excedentes omitidos, log de aviso emitido
- Chunk único que excede budget sozinho: lança `ContextBudgetError`
- `source_document` e `vigencia` presentes em cada chunk incluído no prompt
- Todos os testes rodam com `vitest run`

**Dependências:** TSK-008, TSK-011

**Estimativa:** M

---

## TSK-014 — Testes de integração para o query handler (mocks de serviços Azure)

**Descrição:** Criar `tests/integration/query-handler.test.ts` cobrindo o fluxo completo do handler com mocks dos serviços Azure via `vi.mock`.

**Critérios de Aceite:**
- Happy path: POST válido → HTTP 200 com `answer` e `sources` preenchidos
- `SearchError` propagado pelo `search.ts` → handler retorna HTTP 502
- `CompletionError` propagado pelo `completion.ts` → handler retorna HTTP 502
- Input inválido → HTTP 400 com mensagem de erro (sem stack trace)
- Erro inesperado (não tipado) → HTTP 500 sem vazar detalhes internos
- `vi.mock` cobre `src/services/search` e `src/services/completion`
- Todos os testes rodam com `vitest run`

**Dependências:** TSK-010, TSK-011

**Estimativa:** M
