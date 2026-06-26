// Logger estruturado compartilhado (TSK-003).
// Instância pino única, reutilizada em services/ e functions/.
// Nenhum console.log deve existir no codebase.

import pino, { type Logger } from "pino";

/** Instância pino pré-configurada; nível controlado via `LOG_LEVEL`. */
export const logger: Logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
});

/**
 * Cria um child logger com campos de contexto adicionais
 * (ex.: `{ requestId }`) propagados em todas as linhas de log.
 */
export function childLogger(context: Record<string, unknown>): Logger {
  return logger.child(context);
}
