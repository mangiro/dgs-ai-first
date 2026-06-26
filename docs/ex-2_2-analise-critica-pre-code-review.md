# Revisão Crítica de Código (Pré-Code Review) — Query Endpoint

> **Papel:** Engenheiro de Software Sênior / Especialista TypeScript-Node.js
> **Escopo:** diretório `src/` e `package.json` da `novatech-assistant`
> **Branch:** `cenario-2`
> **Data:** 2026-06-25

## Contexto

Os arquivos efetivamente implementados nesta branch são `shared/{config,types,errors,logger}.ts`, `functions/query/validator.ts` e o stub de `handler.ts`. Os demais módulos em `services/`, `pipeline/`, `bot/`, `functions/feedback` e `functions/health` estão vazios (tarefas pendentes TSK-006+, comportamento esperado pelo SDD). A revisão foca no código já existente e no `package.json`.

---

## 🔴 Ponto Crítico 1 — `zod` é dependência de *runtime*, mas está em `devDependencies` (+ dependências Azure ausentes)

**1. Problema:**
`validator.ts` importa `zod` em tempo de execução, porém `zod` está declarado em `devDependencies`. Em qualquer instalação de produção (`npm ci --omit=dev`, imagem Docker, deploy do Azure Functions), o pacote **não será instalado** e a aplicação quebra no primeiro request com `ERR_MODULE_NOT_FOUND`. Além disso, o `plan.md`/`tasks.md` definem o projeto como **Azure Functions v4 + Azure OpenAI + Azure AI Search**, mas nenhuma dessas dependências de runtime existe no `package.json` (`@azure/functions`, `@azure/openai`/`openai`, `@azure/search-documents`). A TSK-010 (`app.http(...)`) é literalmente impossível de compilar/rodar no estado atual.

**2. Localização:**
- `package.json` (blocos `dependencies` / `devDependencies`)
- Consumidor: `src/functions/query/validator.ts:5` (`import { z } from "zod"`)
- Bloqueio futuro: `src/services/{search,completion}.ts`, `src/functions/query/handler.ts`

**3. Impacto:**
- **Bug de produção (alta severidade):** crash em runtime que passa despercebido em dev (onde devDeps são instaladas). É o tipo de erro que só aparece no deploy.
- **Bloqueio de entrega:** sem `@azure/functions` as TSKs 006/007/010 não podem ser concluídas.

**4. Solução Proposta:**
Mover `zod` para `dependencies` e adicionar as dependências de runtime do domínio:

```jsonc
{
  "dependencies": {
    "@azure/functions": "^4.5.0",
    "@azure/openai": "^2.0.0",
    "@azure/search-documents": "^12.1.0",
    "pino": "^9.0.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@types/node": "^20.14.0",
    "eslint": "^9.0.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0"
  }
}
```

> Regra prática para o code review: **se um `import` é executado em produção, a lib pertence a `dependencies`.** Validar com `npm ci --omit=dev && npm run build` no CI para pegar esse erro cedo.

---

## 🔴 Ponto Crítico 2 — Segredos em texto puro + logger sem *redaction* (vazamento de credenciais/PII)

**1. Problema:**
`config.ts` carrega `AZURE_OPENAI_KEY` e `AZURE_SEARCH_KEY` para um objeto `config` exportado, e o `logger.ts` (pino) é instanciado **sem nenhuma configuração de `redact`**. Basta um `logger.info({ config })`, um `logger.error(err)` com a chave na `cause`, ou logar o corpo de uma request HTTP do Azure SDK (que costuma conter o header `api-key`) para que segredos e a `question` do usuário (PII) caiam nos logs em texto claro. As TSKs 006/007 já pedem para logar request/latência das chamadas Azure — ou seja, o risco é iminente.

**2. Localização:**
- `src/shared/logger.ts` (instância pino sem `redact`)
- `src/shared/config.ts:48-64` (chaves expostas no objeto `config`)

**3. Impacto:**
- **Segurança/compliance (alta):** credenciais Azure em logs são um vazamento de secret — qualquer pessoa com acesso ao Log Analytics/Application Insights obtém acesso aos serviços. `question` em claro é exposição de PII.
- Difícil de reverter: uma vez no agregador de logs, o segredo é considerado comprometido e exige rotação.

**4. Solução Proposta:**
Configurar `redact` no pino de forma centralizada (defesa em profundidade):

```ts
// src/shared/logger.ts
export const logger: Logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  redact: {
    paths: [
      "config.azureOpenAI.key",
      "config.azureSearch.key",
      "*.key",
      'req.headers["api-key"]',
      "req.headers.authorization",
      "question", // PII do atendente/cliente
    ],
    censor: "[REDACTED]",
  },
});
```

Complementarmente, evitar serializar o `config` inteiro em logs e, idealmente, marcar os campos de segredo no tipo para desencorajar o uso direto (ex.: `key: string` documentado como "nunca logar", ou encapsular em um getter). A correção no logger é a barreira mínima obrigatória antes do code review.

---

## 🟠 Ponto Crítico 3 — Validação de env como *side-effect* no import + script `lint` quebrado

**1. Problema:**
`config.ts` executa `const env = loadEnv()` **no topo do módulo** (linha 45). Importar o módulo — direta ou transitivamente (via `search.ts`, `completion.ts`, ou qualquer teste de integração da TSK-014) — dispara a validação e **lança erro só por importar** se as 7 variáveis não estiverem setadas. Isso acopla todo teste unitário que toque a cadeia de imports à presença de credenciais reais, contrariando os critérios das TSKs 012/013/014 ("rodam sem dependências externas"). Soma-se a isso o script `"lint": "eslint ."` sem `eslint` instalado nem config (`.eslintrc`/`eslint.config.js`) — o script falha imediatamente, então o gate de lint é ilusório.

**2. Localização:**
- `src/shared/config.ts:45` (top-level `loadEnv()`)
- `package.json` (`scripts.lint`, ausência de `eslint` e de config)

**3. Impacto:**
- **Testabilidade/manutenção:** força mocks de `process.env` ou variáveis reais em CI; torna os testes frágeis e o fail-fast difícil de isolar.
- **Qualidade:** `npm run lint` quebrado dá falsa sensação de cobertura de lint no PR/CI.

**4. Solução Proposta:**
Transformar a config em *lazy* (validação no primeiro uso, não no import), preservando o fail-fast no startup real via uma chamada explícita:

```ts
// src/shared/config.ts
let cached: Config | undefined;

export function getConfig(): Config {
  if (!cached) cached = buildConfig(loadEnv()); // valida só quando necessário
  return cached;
}
// chamar getConfig() uma vez no bootstrap (handler/registro da Function) mantém o fail-fast.
```

E adicionar o eslint que o script já pressupõe:

```jsonc
"devDependencies": { "eslint": "^9.0.0", "typescript-eslint": "^8.0.0" }
```

com um `eslint.config.js` mínimo. Alternativamente, se a validação eager no import for uma decisão de arquitetura (fail-fast estrito), isso precisa estar documentado e os testes devem usar um `setupFile` do Vitest injetando env dummy — mas a forma *lazy* é a mais usual e menos acoplada.

---

## Resumo para o code review real

| # | Severidade | Tema | Bloqueia merge? |
|---|-----------|------|-----------------|
| 1 | 🔴 Alta | `zod` em devDeps + deps Azure ausentes → crash em prod | **Sim** |
| 2 | 🔴 Alta | Logger sem redaction → vazamento de chaves/PII | **Sim** |
| 3 | 🟠 Média | Env validado no import (testabilidade) + `lint` quebrado | Recomendado |

Os pontos 1 e 2 são os de ajuste **imediato** antes de passar por um code review real.
