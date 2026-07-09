// Hierarquia de erros de domínio (TSK-004).
// Cada erro carrega o `statusCode` HTTP apropriado e a causa original,
// permitindo ao handler mapear falhas para respostas sem vazar stack traces.

/** Base de todos os erros de domínio. Estende `Error` nativo. */
export abstract class AppError extends Error {
  abstract readonly statusCode: number;

  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options);
    this.name = new.target.name;
    // Preserva a cadeia de protótipos ao transpilar para ES5/ES2022.
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** Input inválido do usuário (falha de validação). */
export class ValidationError extends AppError {
  readonly statusCode = 400;
}

/** Falha na chamada ao Azure AI Search. */
export class SearchError extends AppError {
  readonly statusCode = 502;
}

/** Falha na chamada de completion ao Azure OpenAI. */
export class CompletionError extends AppError {
  readonly statusCode = 502;
}

/** Prompt montado excede o limite máximo de contexto configurado. */
export class ContextBudgetError extends AppError {
  readonly statusCode = 500;
}

/** Falha ao persistir um documento no Cosmos DB. */
export class PersistenceError extends AppError {
  readonly statusCode = 502;
}

/** Type guard para identificar erros de domínio conhecidos. */
export function isAppError(error: unknown): error is AppError {
  return error instanceof AppError;
}
