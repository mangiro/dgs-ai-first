// HTTP trigger do feedback endpoint (`POST /api/feedback`).
// Orquestra o tripé handler / validator / response-builder: valida o body com
// Zod, persiste no Cosmos DB e mapeia erros para respostas seguras.
// Segue o AGENTS.md — sem `any`, sem `console.*`, sem PII em log, imports
// estáticos e config centralizada com fail-fast.

import { app } from "@azure/functions";
import type {
  HttpRequest,
  HttpResponseInit,
  InvocationContext,
} from "@azure/functions";
import { randomUUID } from "node:crypto";
import { CosmosClient, type Container } from "@azure/cosmos";
import { getConfig } from "../../shared/config.js";
import { childLogger } from "../../shared/logger.js";
import { PersistenceError, ValidationError } from "../../shared/errors.js";
import type { FeedbackRequest } from "../../shared/types.js";
import { validateFeedbackRequest } from "./validator.js";
import { buildErrorResponse, buildSuccessResponse } from "./response-builder.js";

/** Documento de feedback persistido no Cosmos DB. `queryId` é a partition key. */
interface FeedbackDocument extends FeedbackRequest {
  id: string;
  timestamp: string;
}

// Cliente Cosmos como singleton de módulo: mantém pool de conexões e cache de
// metadados entre requisições. Inicializado de forma lazy para não acoplar a
// validação de env ao import do módulo (fail-fast ocorre no primeiro uso).
let container: Container | undefined;

function getFeedbackContainer(): Container {
  if (!container) {
    const config = getConfig();
    const client = new CosmosClient(config.cosmos.connectionString);
    container = client
      .database(config.cosmos.database)
      .container(config.cosmos.container);
  }
  return container;
}

/** Lê o body como JSON, convertendo JSON malformado em `ValidationError` (400). */
async function readJsonBody(request: HttpRequest): Promise<unknown> {
  try {
    return await request.json();
  } catch (err) {
    throw new ValidationError("Body inválido: JSON malformado.", { cause: err });
  }
}

/** Persiste o documento, convertendo falhas do Cosmos em `PersistenceError` (502). */
async function persist(document: FeedbackDocument): Promise<void> {
  try {
    await getFeedbackContainer().items.create(document);
  } catch (err) {
    throw new PersistenceError("Falha ao persistir o feedback.", { cause: err });
  }
}

export async function feedbackHandler(
  request: HttpRequest,
  context: InvocationContext,
): Promise<HttpResponseInit> {
  const log = childLogger({ requestId: context.invocationId });

  try {
    const body = await readJsonBody(request);
    const feedback = validateFeedbackRequest(body);

    const document: FeedbackDocument = {
      id: randomUUID(),
      queryId: feedback.queryId,
      rating: feedback.rating,
      comment: feedback.comment,
      attendantEmail: feedback.attendantEmail,
      timestamp: new Date().toISOString(),
    };

    await persist(document);

    // Só identificadores e métricas — nunca `attendantEmail` ou `comment` (PII).
    log.info(
      {
        feedbackId: document.id,
        queryId: document.queryId,
        rating: document.rating,
        hasComment: document.comment !== undefined,
      },
      "feedback persistido",
    );

    return buildSuccessResponse(document.id);
  } catch (err) {
    return buildErrorResponse(err, log);
  }
}

app.http("feedback", {
  methods: ["POST"],
  authLevel: "function",
  handler: feedbackHandler,
});
