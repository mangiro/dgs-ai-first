// Validador de input do feedback endpoint.
// Usa Zod para parsear o body HTTP e converte falhas em `ValidationError`,
// mantendo o handler livre de lógica de validação. Espelha o padrão de
// referência em `src/functions/query/validator.ts`.

import { z } from "zod";
import { ValidationError } from "../../shared/errors.js";
import type { FeedbackRequest } from "../../shared/types.js";

/** Tamanho máximo do comentário livre — barra payloads gigantes (vetor de DoS). */
const MAX_COMMENT_LENGTH = 1000;

/**
 * Schema do body aceito em `POST /api/feedback`.
 * - `queryId`: obrigatório, UUID da consulta avaliada.
 * - `rating`: obrigatório, inteiro de 1 a 5.
 * - `comment`: opcional, texto livre limitado a 1000 caracteres.
 * - `attendantEmail`: obrigatório, e-mail válido (PII — nunca logado).
 */
const feedbackRequestSchema = z
  .object({
    queryId: z
      .string({ required_error: "O campo 'queryId' é obrigatório." })
      .uuid("O campo 'queryId' deve ser um UUID válido."),
    rating: z
      .number({ required_error: "O campo 'rating' é obrigatório." })
      .int("O campo 'rating' deve ser um número inteiro.")
      .min(1, "O campo 'rating' deve ser no mínimo 1.")
      .max(5, "O campo 'rating' deve ser no máximo 5."),
    comment: z
      .string()
      .max(
        MAX_COMMENT_LENGTH,
        `O campo 'comment' não pode exceder ${MAX_COMMENT_LENGTH} caracteres.`,
      )
      .optional(),
    attendantEmail: z
      .string({ required_error: "O campo 'attendantEmail' é obrigatório." })
      .email("O campo 'attendantEmail' deve ser um e-mail válido."),
  })
  .strict();

/** Formata os issues do Zod em uma mensagem única e legível. */
function formatIssues(error: z.ZodError): string {
  return error.issues
    .map((issue) => {
      const path = issue.path.join(".");
      return path ? `${path}: ${issue.message}` : issue.message;
    })
    .join("; ");
}

/**
 * Parseia e valida o body recebido pelo endpoint de feedback.
 * @throws {ValidationError} quando o body não satisfaz o schema.
 */
export function validateFeedbackRequest(body: unknown): FeedbackRequest {
  const result = feedbackRequestSchema.safeParse(body);

  if (!result.success) {
    throw new ValidationError(formatIssues(result.error), {
      cause: result.error,
    });
  }

  return result.data;
}
