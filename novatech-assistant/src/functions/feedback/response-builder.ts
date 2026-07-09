// Monta a saída HTTP do feedback endpoint.
// Sucesso: 201 com o id gerado. Erro: mapeia `AppError` para o seu
// `statusCode`, registrando apenas o motivo (sem stack trace nem PII) e
// devolvendo uma mensagem segura ao cliente.

import type { HttpResponseInit } from "@azure/functions";
import type { Logger } from "pino";
import { isAppError } from "../../shared/errors.js";

/** Resposta de sucesso: feedback persistido. */
export function buildSuccessResponse(feedbackId: string): HttpResponseInit {
  return {
    status: 201,
    jsonBody: { status: "created", id: feedbackId },
  };
}

/**
 * Mapeia um erro capturado no handler para uma resposta HTTP segura.
 * Erros de domínio (`AppError`) usam seu `statusCode`; qualquer outro erro
 * vira 500 genérico. Nunca vaza stack trace nem PII ao cliente ou ao log.
 */
export function buildErrorResponse(
  error: unknown,
  log: Logger,
): HttpResponseInit {
  if (isAppError(error)) {
    const context = { err: error.name, statusCode: error.statusCode };
    if (error.statusCode >= 500) {
      log.error(context, error.message);
    } else {
      log.warn(context, error.message);
    }
    return {
      status: error.statusCode,
      jsonBody: { error: error.message },
    };
  }

  log.error({ err: "UnknownError" }, "erro não tratado no endpoint de feedback");
  return {
    status: 500,
    jsonBody: { error: "Erro interno ao processar o feedback." },
  };
}
