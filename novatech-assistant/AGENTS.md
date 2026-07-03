# AGENTS.md — NovaTech Assistant

> Constitution do projeto. Todo agente de IA (Copilot, Claude Code) lê este arquivo antes de gerar qualquer artefato.
> As seções abaixo são preenchidas por papéis diferentes nos exercícios do Cenário 2.

## Project Overview
<!-- TODO (Tech Lead — Ex. 2.1) -->

## Tech Stack & Architecture

| Camada             | Tecnologia                                             |
|--------------------|--------------------------------------------------------|
| Linguagem          | TypeScript 5.5+ (ESM, `"type": "module"`)              |
| Runtime alvo       | Node.js 20 LTS / Azure Functions                       |
| Validação          | **Zod** (única biblioteca de validação permitida)      |
| Logging            | **pino** (único logger permitido)                      |
| Testes             | Vitest                                                 |
| Lint               | ESLint                                                 |
| Build              | `tsc` (ver `tsconfig.json`)                            |

**Convenções de módulo:**

- ESM puro: imports com extensão `.js` no path relativo (ex.: `../../shared/errors.js`), pois o output é ESM.
- Todo endpoint segue o tripé **handler / validator / response-builder** (ver `src/functions/query/`): o `handler` orquestra, o `validator` valida com Zod, o `response-builder` monta a saída.
- Erros de domínio herdam de `AppError` (`src/shared/errors.ts`) e carregam o `statusCode` HTTP. O handler mapeia erros para respostas **sem vazar stack traces**.
- Configuração vem exclusivamente de variáveis de ambiente, lidas e validadas no startup com **fail-fast** (`src/shared/config.ts`). Segredos nunca são hardcoded.

**Gerenciamento de contexto (ADR-0002) — obrigatório:**

- O prompt final respeita o **orçamento de tokens**: `SYSTEM_PROMPT_TOKEN_BUDGET = 4096` (~4K system) + `CHUNKS_TOKEN_BUDGET = 8192` (~8K chunks) + histórico de **3 turnos**. Essas constantes vivem em `src/shared/config.ts` — não duplicar valores mágicos.
- O `prompt-builder` (`src/services/prompt-builder.ts`) descarta chunks que excedem o budget (logando um aviso) e lança `ContextBudgetError` se **um único chunk** já não couber.
- Em documentos contraditórios, **priorizar sempre a versão mais recente** (maior `vigencia`, metadado ISO 8601 definido na ADR-0003).
- Toda resposta cita as fontes usadas (`source_document` + `vigencia`).

## Coding Standards

> Estas cinco regras são **estritas e não-negociáveis**. Valem para todo código do repositório —
> escrito por humano ou gerado por IA (Copilot, Claude Code). Um artefato que viole qualquer uma
> delas está incompleto e **não deve ser mesclado**, mesmo que os testes passem.
> Já houve incidente: um módulo de feedback gerado por IA ignorou o AGENTS.md (não usou Zod e
> logou dados sensíveis do atendente). É exatamente isso que estas regras existem para impedir.

### 1. TypeScript em modo estrito

**DEVE:**

- Manter `"strict": true` no `tsconfig.json`. Nenhuma flag do modo estrito pode ser afrouxada (`noImplicitAny`, `strictNullChecks`, etc. permanecem ativas).
- Tipar explicitamente as fronteiras públicas (parâmetros e retorno de funções exportadas).
- Modelar ausência com `undefined`/tipos opcionais e tratá-la — não assumir que valores existem.

**NÃO DEVE:**

- Usar `any`. Para valores de origem desconhecida (input HTTP, JSON externo), use `unknown` e restrinja o tipo via Zod (ver regra 2).
- Silenciar o compilador com `@ts-ignore`, `@ts-expect-error` ou casts `as` que mascaram erros reais.
- Introduzir código que só compila por causa de uma flag relaxada.

### 2. Validação exclusivamente com Zod

Toda entrada que cruza uma fronteira de confiança (body HTTP, variáveis de ambiente, payload de tool, resposta do modelo LLM) **DEVE** ser parseada e validada com **Zod** antes de ser usada. Zod é a **única** biblioteca de validação permitida no projeto.

**DEVE:**

- Definir um schema Zod e derivar/mapear os dados a partir dele (`.parse` / `.safeParse`).
- Converter falhas de validação em `ValidationError` (`src/shared/errors.ts`) — nunca deixar o fluxo seguir com dado inválido. Padrão de referência: `src/functions/query/validator.ts`.
- Usar `.strict()` em schemas de objeto para rejeitar campos inesperados.
- Validar **structured outputs** do modelo (ex.: `{ answer, source_document, confidence_score }`) com Zod e **rejeitar** respostas fora do formato antes de checar o conteúdo.

**NÃO DEVE:**

- Escrever validação manual (`if (!body.question) ...`), usar `JSON.parse` cru sem schema, ou introduzir outra lib de validação (Joi, Yup, class-validator, ajv, etc.).
- Confiar em tipos do TypeScript como se fossem validação em runtime — tipos somem na compilação.

```ts
// ✅ Correto — schema Zod como única fonte de verdade do input
const schema = z.object({ question: z.string().min(1).max(500) }).strict();
const result = schema.safeParse(body);
if (!result.success) throw new ValidationError(formatIssues(result.error));

// ❌ Proibido — validação manual, sem Zod
if (typeof body.question !== "string" || !body.question) { /* ... */ }
```

### 3. Logging exclusivamente com pino

Todo registro **DEVE** usar a instância `pino` compartilhada em `src/shared/logger.ts` (`logger` ou `childLogger({...})`). É **expressamente proibido** usar `console.*`.

**DEVE:**

- Importar o `logger`/`childLogger` de `src/shared/logger.ts` e logar em formato estruturado (objeto de contexto + mensagem), ex.: `logger.info({ requestId }, "query recebida")`.
- Usar `childLogger({ requestId })` para propagar correlation ID em todas as linhas de uma requisição.
- Controlar verbosidade via `LOG_LEVEL` (variável de ambiente), não via código.

**NÃO DEVE:**

- Usar `console.log`, `console.error`, `console.warn`, `console.debug` ou `console.info` em qualquer arquivo de `src/`. O ESLint deve barrar `no-console`.
- Criar instâncias avulsas de logger espalhadas pelo código — reusar a instância única.

```ts
// ✅ Correto
import { childLogger } from "../shared/logger.js";
const log = childLogger({ requestId });
log.error({ err }, "falha ao consultar o índice");

// ❌ Proibido
console.error("falha ao consultar o índice", err);
```

### 4. Nunca logar PII (dados pessoais)

Dados pessoais do atendente ou de clientes — **e-mails, nomes, telefones, documentos, identificadores diretos** — **NÃO DEVEM** aparecer em log algum, em nenhum nível. Esta regra vale inclusive em `debug` e em mensagens de erro.

**DEVE:**

- Logar apenas identificadores não-sensíveis: `requestId`, `session_id`, códigos de fonte (`source_document`), métricas (`confidence_score`, latência, contagem de chunks).
- Redigir/omitir campos sensíveis antes de logar (ex.: logar `{ hasEmail: true }`, nunca o e-mail).
- Ao logar erros de validação, registrar o **motivo/campo** que falhou, não o **valor** enviado.

**NÃO DEVE:**

- Logar o body/payload cru de uma requisição, a pergunta livre do usuário quando puder conter PII, ou objetos inteiros de usuário (`log.info({ user })`).
- Incluir PII em mensagens de exceção que serão registradas.

```ts
// ✅ Correto — só identificadores e métricas
log.info({ requestId, sourceCount: sources.length, confidence }, "resposta gerada");

// ❌ Proibido — vaza PII no log
log.info({ email: user.email, name: user.name, question }, "resposta gerada");
```

### 5. Somente imports estáticos no topo do arquivo

Toda dependência **DEVE** ser importada via `import` estático, declarado no **topo do arquivo**.

**DEVE:**

- Declarar todos os imports no início do módulo, antes de qualquer código executável.
- Usar `import type { ... }` para imports usados apenas em posição de tipo.

**NÃO DEVE:**

- Usar `require(...)`, `require` dinâmico, ou `import(...)` dinâmico condicional no meio da lógica.
- Importar dentro de funções, `if`, `try/catch` ou blocos condicionais.
- Fazer side-effect imports escondidos no meio do arquivo.

```ts
// ✅ Correto — topo do arquivo
import { z } from "zod";
import { ValidationError } from "../../shared/errors.js";
import type { QueryRequest } from "../../shared/types.js";

// ❌ Proibido — require/import dinâmico no meio do código
function handle() {
  const { z } = require("zod");           // proibido
  if (flag) { const m = await import("./x.js"); } // proibido
}
```

## Product Rules & Guardrails (Product Specialist)
<!-- TODO (Product Specialist — Ex. 2.3) -->

## Testing Standards (QA)
<!-- TODO (QA — Ex. 2.1) -->

## Project Management Rules (Delivery Manager)
<!-- TODO (Delivery Manager — Ex. 2.3) -->

## Build & Deploy

Comandos padronizados (via `npm`, ver `package.json`):

| Ação          | Comando          | Descrição                                              |
|---------------|------------------|--------------------------------------------------------|
| Testar        | `npm test`       | Executa a suíte com Vitest (`vitest run`).             |
| Lint          | `npm run lint`   | Roda ESLint (deve barrar `no-console` e imports proibidos). |
| Build         | `npm run build`  | Compila com `tsc -p .` para `dist/` (falha em qualquer erro de tipo). |

**Portão de qualidade (antes de mesclar):** `lint` + `build` + `test` devem passar. Como o build usa `strict: true`, qualquer violação de tipo quebra a compilação — a checagem de tipos faz parte do gate, não é opcional. Nenhum artefato gerado por IA entra sem passar por este portão e por revisão humana (human-in-the-loop) das cinco regras de Coding Standards acima.
