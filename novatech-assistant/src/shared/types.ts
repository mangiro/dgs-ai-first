// Tipos compartilhados do domínio do query endpoint (TSK-001).
// Tipos puros: nenhum import de módulos externos.

/** Pergunta enviada pelo atendente ao endpoint `POST /api/query`. */
export interface QueryRequest {
  question: string;
  session_id?: string;
}

/**
 * Chunk de documento indexado no Azure AI Search.
 * `vigencia` é o metadado de rastreabilidade definido na ADR-0003,
 * representado como data ISO 8601 (`YYYY-MM-DD`) para permitir ordenação
 * por documento mais recente.
 */
export interface DocumentChunk {
  id: string;
  content: string;
  source_document: string;
  vigencia: string;
  score?: number;
}

/**
 * Resultado bruto de uma busca vetorial no Azure AI Search,
 * antes de ser normalizado para `DocumentChunk`.
 */
export interface SearchResult {
  chunk: DocumentChunk;
  score: number;
}

/** Resposta HTTP final do endpoint. */
export interface QueryResponse {
  answer: string;
  sources: Pick<DocumentChunk, "source_document" | "vigencia">[];
}

/**
 * Feedback do atendente sobre uma resposta, enviado a `POST /api/feedback`.
 * `attendantEmail` é PII (identificador direto) e nunca deve ser logado.
 */
export interface FeedbackRequest {
  queryId: string;
  rating: number;
  comment?: string;
  attendantEmail: string;
}
