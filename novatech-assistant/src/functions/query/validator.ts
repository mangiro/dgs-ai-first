// Validador de input do query endpoint (TSK-005).
// Usa Zod para parsear o body HTTP e converte falhas em `ValidationError`,
// mantendo o handler livre de lógica de validação.

import { z } from "zod";
import { ValidationError } from "../../shared/errors.js";
import type { QueryRequest } from "../../shared/types.js";

/**
 * Schema do body aceito em `POST /api/query`.
 * - `question`: obrigatória, entre 1 e 500 caracteres.
 * - `session_id`: opcional, deve ser um UUID quando presente.
 */
const queryRequestSchema = z
  .object({
    question: z
      .string({ required_error: "O campo 'question' é obrigatório." })
      .min(1, "O campo 'question' não pode ser vazio.")
      .max(500, "O campo 'question' não pode exceder 500 caracteres."),
    session_id: z
      .string()
      .uuid("O campo 'session_id' deve ser um UUID válido.")
      .optional(),
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
 * Parseia e valida o body recebido pelo endpoint.
 * @throws {ValidationError} quando o body não satisfaz o schema.
 */
export function validateQueryRequest(body: unknown): QueryRequest {
  const result = queryRequestSchema.safeParse(body);

  if (!result.success) {
    throw new ValidationError(formatIssues(result.error), {
      cause: result.error,
    });
  }

  return result.data;
}
