// Logger estruturado compartilhado (TSK-003).
// Instância pino única, reutilizada em services/ e functions/.
// Nenhum console.log deve existir no codebase.

import pino, { type Logger } from "pino";

/**
 * Instância pino pré-configurada; nível controlado via `LOG_LEVEL`.
 *
 * `redact` é a barreira central (defesa em profundidade) contra vazamento de
 * segredos (chaves Azure) e PII (`question` do atendente/cliente). Cobre tanto
 * o objeto `config` quanto headers de request do SDK Azure (`api-key`,
 * `authorization`). Nunca serialize o `config` inteiro em logs mesmo assim.
 */
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

/**
 * Cria um child logger com campos de contexto adicionais
 * (ex.: `{ requestId }`) propagados em todas as linhas de log.
 */
export function childLogger(context: Record<string, unknown>): Logger {
  return logger.child(context);
}
