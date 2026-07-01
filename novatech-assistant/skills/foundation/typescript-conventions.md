---
name: typescript-conventions
layer: foundation
description: >-
  Convenções TypeScript transversais do NovaTech Assistant — sistema de módulos,
  strict mode, naming, tipos vs. interfaces e formatação. É a skill-base do
  projeto: carregada IMPLICITAMENTE por toda skill de `artifact` e disparada em
  QUALQUER geração ou edição de arquivo `.ts`/`.tsx`.
activation: "Vou gerar ou editar qualquer arquivo .ts/.tsx."
owners: [Tech Lead, Dev Sênior]
applies_to: ["src/**/*.ts", "src/**/*.tsx", "tests/**/*.ts"]
---

# Foundation · TypeScript Conventions

> **Posição na hierarquia.** Esta é a skill de fundação mais básica do projeto.
> Toda skill de `domain` e toda receita de `artifact` assume estas regras como
> base e **não as repete**. Quando uma receita gera código `.ts`/`.tsx`, estas
> convenções valem por padrão.
>
> **Princípio de não-vazamento.** Esta skill governa a *forma* do código
> TypeScript — nada além disso. Erros, logging e configuração têm donos
> próprios; aqui apenas os **referenciamos**, nunca os redefinimos:
> - taxonomia de erros → `foundation/error-handling`
> - log estruturado e correlation ID → `foundation/logging-observability`
> - leitura de config e segredos → `foundation/environment-config`
> - onde cada arquivo mora → `foundation/project-structure`

---

## 1. Contexto

O NovaTech Assistant é um monorepo TypeScript que cobre três superfícies —
backend (Azure Functions), bot (Bot Framework) e painel web (React) — mais o
pipeline de ingestão e o código compartilhado em `src/shared/`. Para que o
código gerado por agentes (Claude Code, Copilot) e por humanos seja
indistinguível e revisável, **toda escrita de TypeScript segue um único
conjunto de convenções**, refletido pelo código já existente em `src/shared/`
(`errors.ts`, `config.ts`, `logger.ts`, `types.ts`) e em `src/functions/`.

Restrições técnicas que moldam as regras abaixo (de `tsconfig.json` e
`package.json`):

- `"type": "module"` → o projeto é **ESM puro**.
- `"module": "ESNext"`, `"moduleResolution": "Bundler"`, `"target": "ES2022"`.
- `"strict": true` → todas as checagens estritas ligadas.
- Dependências de validação e log já decididas: **Zod** (validação de I/O) e
  **pino** (log estruturado). Não introduza alternativas.

Antes de criar um arquivo, consulte `foundation/project-structure` para saber
**onde** ele mora. Esta skill cuida de **como** ele é escrito.

---

## 2. Regras prescritivas

### 2.1 Sistema de módulos (ESM)

1. **Use somente `import`/`export`.** Nada de `require`, `module.exports` ou
   `import = require(...)`.
2. **Imports relativos terminam em `.js`** — mesmo apontando para um arquivo
   `.ts`. É exigência do ESM em runtime (o código já faz isso:
   `import { ValidationError } from "../../shared/errors.js"`).
3. **Apenas exports nomeados.** `export default` é proibido (ver anti-padrões).
4. **Imports só de tipo usam `import type`** (ou `import { type X }`), para que
   sejam apagados na transpilação e não criem dependência em runtime.

### 2.2 Strict mode — sem escapatórias

1. **Nunca use `any`.** Em fronteiras de entrada (body HTTP, JSON externo) o
   tipo é `unknown`; faça o *narrowing* com Zod ou type guard antes de usar.
2. **Não use `!` (non-null assertion)** para silenciar o compilador. Trate o
   caso `undefined`/`null` explicitamente.
3. **Não use `as` para forçar tipos** que o compilador rejeita. `as const` é
   permitido e encorajado para literais imutáveis; `as unknown as T` é proibido.
4. **Type guards** retornam `x is T` e ficam próximos do tipo que guardam
   (padrão de `isAppError` em `errors.ts`).

### 2.3 Naming

| Construto | Convenção | Exemplo no repo |
|---|---|---|
| Tipos, interfaces, classes | `PascalCase`, **sem prefixo `I`** | `QueryRequest`, `AppError`, `DocumentChunk` |
| Funções e variáveis | `camelCase` | `validateQueryRequest`, `childLogger` |
| Constantes de módulo | `UPPER_SNAKE_CASE` | `SYSTEM_PROMPT_TOKEN_BUDGET`, `REQUIRED_ENV_VARS` |
| **Campos de DTO de wire** (JSON da API) | `snake_case` | `session_id`, `source_document`, `vigencia` |

> **Regra de ouro do naming:** o código interno é `camelCase`; apenas os
> **campos que cruzam o fio** (request/response HTTP, documento do AI Search)
> usam `snake_case`, porque espelham o contrato JSON. Não converta esses campos
> para camelCase nos `interface` de wire (`QueryRequest`, `QueryResponse`,
> `DocumentChunk`).

### 2.4 Tipos vs. interfaces

- **`interface`** para a forma de objetos e DTOs (`QueryRequest`, `DocumentChunk`).
- **`type`** para uniões, aliases e tipos derivados
  (`type Config = typeof config`, `type RequiredEnvVar = (typeof REQUIRED_ENV_VARS)[number]`).
- **Sem `enum`.** Use uniões de string literais ou objetos `as const`.

### 2.5 Formatação e estilo

- Indentação de **2 espaços**; **aspas duplas**; **ponto e vírgula** sempre;
  **vírgula final** (trailing comma) em multilinha.
- Toda função/módulo exportado leva **JSDoc em PT-BR**; use `@throws` quando
  lançar erro de domínio e `@param` quando o nome não for autoexplicativo
  (padrão de `validateQueryRequest`).
- Cabeçalho de arquivo: um comentário curto dizendo o propósito e, quando
  houver, o ID da tarefa/ADR (`// ... (TSK-005).`, `// ... (ADR-0002)`).
- `src/shared/types.ts` é de **tipos puros**: não importa módulos externos nem
  de runtime. Mantenha-o assim.

### 2.6 Limites de responsabilidade (delegação, não redefinição)

- Vai logar? **Não use `console.log`** — use o `logger`/`childLogger` conforme
  `foundation/logging-observability`.
- Precisa de endpoint/segredo? **Não hardcode** — leia de `config` conforme
  `foundation/environment-config`.
- Vai falhar? **Lance um `AppError`** da hierarquia, conforme
  `foundation/error-handling`.

---

## 3. Exemplos concretos — FAÇA / NÃO FAÇA

### 3.1 Imports

✅ **FAÇA** — extensão `.js`, `import type` para tipos, exports nomeados:

```ts
import { z } from "zod";
import { ValidationError } from "../../shared/errors.js";
import type { QueryRequest } from "../../shared/types.js";

export function validateQueryRequest(body: unknown): QueryRequest {
  /* ... */
}
```

❌ **NÃO FAÇA** — sem extensão, `require`, default export, tipo importado como valor:

```ts
const { ValidationError } = require("../../shared/errors"); // CommonJS proibido
import QueryRequest from "../../shared/types";               // sem .js + default
export default function validate(body: any) { /* ... */ }     // default + any
```

### 3.2 Fronteira de entrada: `unknown` + narrowing

✅ **FAÇA** — o body chega como `unknown` e é estreitado por Zod antes do uso:

```ts
export function validateQueryRequest(body: unknown): QueryRequest {
  const result = queryRequestSchema.safeParse(body);
  if (!result.success) {
    throw new ValidationError(formatIssues(result.error), { cause: result.error });
  }
  return result.data; // tipado como QueryRequest
}
```

❌ **NÃO FAÇA** — `any` + acesso direto a campos não validados:

```ts
export function validateQueryRequest(body: any): QueryRequest {
  return { question: body.question, session_id: body.session_id }; // sem validação
}
```

### 3.3 Naming de wire vs. interno

✅ **FAÇA** — campos de wire em `snake_case`, código interno em `camelCase`:

```ts
export interface QueryResponse {
  answer: string;
  sources: Pick<DocumentChunk, "source_document" | "vigencia">[];
}

function buildResponse(chunks: DocumentChunk[]): QueryResponse {
  const sources = chunks.map((chunk) => ({
    source_document: chunk.source_document,
    vigencia: chunk.vigencia,
  }));
  return { answer: "...", sources };
}
```

❌ **NÃO FAÇA** — camelCase no contrato JSON (quebra o consumidor) ou `I`-prefix:

```ts
export interface IQueryResponse {        // prefixo I proibido
  answer: string;
  sources: { sourceDocument: string }[]; // muda o nome no fio → contrato quebrado
}
```

### 3.4 Constantes e tipos derivados (`as const`, sem `enum`)

✅ **FAÇA**:

```ts
const REQUIRED_ENV_VARS = ["AZURE_OPENAI_ENDPOINT", "AZURE_SEARCH_INDEX"] as const;
type RequiredEnvVar = (typeof REQUIRED_ENV_VARS)[number];

const STATUS = { ok: "ok", degraded: "degraded" } as const;
type Status = (typeof STATUS)[keyof typeof STATUS];
```

❌ **NÃO FAÇA** — `enum` e arrays mutáveis perdem a inferência literal:

```ts
enum Status { Ok, Degraded }                  // evite enum
const REQUIRED_ENV_VARS = ["AZURE_OPENAI_ENDPOINT"]; // string[], perde o literal
```

### 3.5 JSDoc, `@throws` e cabeçalho de arquivo

✅ **FAÇA**:

```ts
// Validador de input do query endpoint (TSK-005).
// Converte falhas de schema em ValidationError, mantendo o handler limpo.

/**
 * Parseia e valida o body recebido pelo endpoint.
 * @throws {ValidationError} quando o body não satisfaz o schema.
 */
export function validateQueryRequest(body: unknown): QueryRequest { /* ... */ }
```

❌ **NÃO FAÇA** — sem doc, sem contexto, e silenciando o tipo com `!`:

```ts
export function validateQueryRequest(body: unknown) {
  return queryRequestSchema.safeParse(body).data!; // ! mascara o caso de falha
}
```

---

## 4. Anti-padrões (rejeitar em review)

1. **`any` em qualquer forma** — incluindo `as any`, `(x as any).y`, `Array<any>`.
   Fronteira é `unknown` + narrowing.
2. **`export default`** — impede import nomeado consistente e auto-rename; todo
   símbolo é exportado por nome.
3. **Import relativo sem `.js`** — quebra em runtime ESM.
4. **Tipo importado como valor** (sem `import type`) — cria dependência de
   runtime desnecessária.
5. **`enum`** — preferir uniões de literais ou objetos `as const`.
6. **Interface com prefixo `I`** (`IQueryRequest`) — naming legado, não usado no repo.
7. **`!` (non-null) e `as unknown as T`** para calar o compilador — trate o caso real.
8. **`console.log`/`console.error`** — use o `logger` (ver `logging-observability`).
9. **Hardcode de endpoint, key ou connection string** — use `config` (ver `environment-config`).
10. **`try/catch` que engole o erro ou cria `new Error("...")` genérico** em vez
    de lançar um `AppError` da hierarquia (ver `error-handling`).
11. **Renomear campos de wire para camelCase** num `interface` de request/response
    — quebra o contrato com Bot/painel.
12. **Lógica de runtime em `src/shared/types.ts`** — esse arquivo é só de tipos puros.
