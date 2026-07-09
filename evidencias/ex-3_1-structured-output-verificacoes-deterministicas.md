# Evidência exercício 3.1 — Structured output e verificações determinísticas (harness de código)

## O schema Zod e o código do response-validator

**Contexto adicionado a sessão:**
- [cenario-novatech.md](../docs/cenario-novatech.md)
- [POL-001-politica-devolucao.md](../novatech-assistant/docs/novatech/POL-001-politica-devolucao.md)

**Prompt utilizado:**
```
Você é um Desenvolvedor TypeScript Sênior especializado em sistemas de IA orientados a RAG e validação estruturada.

Sua tarefa é implementar o arquivo `response-validator.ts` utilizando a biblioteca Zod para validar e processar as respostas da IA.

Siga as instruções abaixo:

1. Defina e exporte um Zod schema para a saída estruturada com os seguintes campos:
    - `answer` (string)
	- `source_document` (string)
	- `confidence_score` (number)
2. Crie a função principal de validação (ex: `validateAiResponse(rawInput: unknown)`).

A função de validação deve aplicar rigorosamente as seguintes regras:

1. **Obrigatoriedade de Fonte:** Toda resposta DEVE incluir o campo `source_document` não vazio.
2. **Restrição de Carga Perigosa:** Se a `answer` mencionar os termos "carga perigosa" E "devolução" (independente de maiúsculas/minúsculas), ela DEVE ser inspecionada. Se a afirmação sugerir que a devolução é possível (ausência de negativa), a resposta deve ser bloqueada.

Em qualquer cenário de falha (erro de tipagem Zod, falta de `source_document`, ou violação da regra de carga perigosa):
    - Registre o motivo exato/detalhado da falha no log.
	- Ignore a resposta original da IA.
	- Retorne um objeto de resposta padrão de fallback e totalmente seguro (ex: afirmando que não é possível processar a solicitação no momento).

Gere o código completo e limpo de `response-validator.ts`. Inclua os tipos inferidos do Zod (`z.infer`) e adicione comentários explicando especialmente a lógica utilizada no Guardrail 2.
```
**Resultado:**
```typescript
// Validador de structured output do modelo LLM (harness — Cenário 3).
// O modelo é forçado a responder em JSON { answer, source_document, confidence_score }.
// Este módulo é a fronteira de confiança entre a saída do LLM e o restante do
// sistema: rejeita o que não bate com o schema (Guardrail de formato), aplica os
// guardrails de conteúdo, e — em QUALQUER falha — descarta a resposta original e
// devolve um fallback seguro. Nenhuma resposta fora do formato/regra segue adiante.

import { z } from "zod";
import { childLogger } from "../shared/logger.js";

const log = childLogger({ module: "response-validator" });

/**
 * Schema da saída estruturada do assistente.
 *
 * - `answer`: texto da resposta; não pode ser vazio.
 * - `source_document`: Guardrail 1 (Obrigatoriedade de Fonte) — toda resposta
 *   DEVE citar a fonte. `.min(1)` rejeita string vazia ou só com espaços após
 *   normalização (ver `.trim()` no schema).
 * - `confidence_score`: número em [0, 1]. Fora da faixa é formato inválido.
 *
 * `.strict()` rejeita campos inesperados — se o modelo "inventar" chaves extras,
 * a resposta é barrada antes de qualquer checagem de conteúdo.
 */
export const aiResponseSchema = z
  .object({
    answer: z
      .string({ required_error: "O campo 'answer' é obrigatório." })
      .trim()
      .min(1, "O campo 'answer' não pode ser vazio."),
    // Guardrail 1: fonte obrigatória e não-vazia.
    source_document: z
      .string({ required_error: "O campo 'source_document' é obrigatório." })
      .trim()
      .min(1, "O campo 'source_document' é obrigatório e não pode ser vazio."),
    confidence_score: z
      .number({ required_error: "O campo 'confidence_score' é obrigatório." })
      .min(0, "O campo 'confidence_score' deve ser >= 0.")
      .max(1, "O campo 'confidence_score' deve ser <= 1."),
  })
  .strict();

/** Tipo inferido do schema — fonte única de verdade da forma da resposta. */
export type AiResponse = z.infer<typeof aiResponseSchema>;

/**
 * Resposta padrão de fallback. Totalmente segura: fonte sinalizando origem no
 * próprio sistema (não um documento real) e confiança zero, de forma que qualquer
 * regra de human-in-the-loop a jusante trate o caso como "precisa de humano".
 * É retornada — em vez da saída do modelo — em todo cenário de falha.
 */
export const SAFE_FALLBACK_RESPONSE: AiResponse = Object.freeze({
  answer:
    "Não é possível processar esta solicitação com segurança no momento. " +
    "Por favor, encaminhe o caso a um atendente humano.",
  source_document: "SISTEMA::FALLBACK_SEGURO",
  confidence_score: 0,
});

// --- Guardrail 2: Restrição de Carga Perigosa ---------------------------------
//
// Contexto (POL-001, seção 3.2): cargas perigosas classes 1–6 da ANTT NÃO são
// elegíveis para devolução pelo processo padrão. Uma alucinação que afirme o
// contrário é de alto risco (o cliente/atendente agiria sobre informação errada).
//
// A lógica é intencionalmente conservadora ("fail-safe"): quando a resposta toca
// os DOIS temas sensíveis ao mesmo tempo — "carga perigosa" E "devolução" — ela
// só é liberada se contiver uma NEGATIVA explícita (ex.: "não é possível
// devolver"). Na AUSÊNCIA de negativa, presume-se que a resposta está afirmando
// que a devolução é possível e a bloqueamos. Ou seja: o ônus da prova é da
// resposta — ela precisa provar que nega a devolução; o silêncio é tratado como
// afirmação perigosa, não como benefício da dúvida.

/** Termos-gatilho que, juntos, ativam a inspeção do Guardrail 2. */
const CARGA_PERIGOSA_TERM = "carga perigosa";
const DEVOLUCAO_TERM = "devolu"; // cobre "devolução", "devolver", "devolvida", etc.

/**
 * Marcadores de negativa. A presença de qualquer um indica que a resposta está
 * negando a devolução (comportamento correto conforme POL-001). A lista é
 * propositalmente ampla para reduzir falsos negativos (deixar passar uma
 * afirmação perigosa é pior do que bloquear uma resposta correta por excesso de
 * zelo — esta última cai no fluxo human-in-the-loop).
 */
const NEGATION_MARKERS: readonly string[] = [
  "não é possível",
  "nao e possivel",
  "não é elegível",
  "não são elegíveis",
  "nao sao elegiveis",
  "não elegível",
  "inelegível",
  "não pode ser devolvid", // "não pode ser devolvida/o"
  "não podem ser devolvid",
  "não permite",
  "não é permitido",
  "não aceita",
  "exceção ao prazo",
  "gestão de riscos", // POL-001 encaminha esses casos à Gestão de Riscos
];

/**
 * Aplica o Guardrail 2 sobre o texto da resposta já validada pelo schema.
 * @returns `true` se a resposta deve ser BLOQUEADA.
 */
function violatesCargaPerigosaRule(answer: string): boolean {
  const normalized = answer.toLowerCase();

  const mentionsCargaPerigosa = normalized.includes(CARGA_PERIGOSA_TERM);
  const mentionsDevolucao = normalized.includes(DEVOLUCAO_TERM);

  // A inspeção só se aplica quando AMBOS os temas aparecem juntos.
  if (!mentionsCargaPerigosa || !mentionsDevolucao) {
    return false;
  }

  const hasNegation = NEGATION_MARKERS.some((marker) =>
    normalized.includes(marker),
  );

  // Bloqueia quando NÃO há negativa (a resposta sugere devolução possível).
  return !hasNegation;
}

/**
 * Valida e processa a resposta bruta do modelo LLM.
 *
 * Ordem das checagens (formato antes de conteúdo, conforme AGENTS.md):
 *   1. Parse/validação Zod (inclui Guardrail 1 — fonte obrigatória).
 *   2. Guardrail 2 — restrição de carga perigosa.
 *
 * Em QUALQUER falha: registra o motivo detalhado (sem PII — apenas o motivo/campo,
 * nunca o valor bruto), descarta a resposta do modelo e retorna o fallback seguro.
 *
 * @param rawInput Saída bruta e não-confiável do modelo (`unknown`).
 * @returns A resposta validada, ou `SAFE_FALLBACK_RESPONSE` em caso de falha.
 */
export function validateAiResponse(rawInput: unknown): AiResponse {
  // 1. Validação de formato + Guardrail 1 (fonte) via Zod.
  const parsed = aiResponseSchema.safeParse(rawInput);

  if (!parsed.success) {
    // Logamos apenas os motivos/campos que falharam — nunca o payload bruto,
    // que poderia carregar PII (regra 4 do AGENTS.md).
    log.warn(
      {
        guardrail: "schema",
        reasons: parsed.error.issues.map((issue) => ({
          path: issue.path.join(".") || "(root)",
          message: issue.message,
        })),
      },
      "Resposta do modelo rejeitada: falha de validação de formato/fonte. Retornando fallback seguro.",
    );
    return SAFE_FALLBACK_RESPONSE;
  }

  const response = parsed.data;

  // 2. Guardrail 2 — restrição de carga perigosa.
  if (violatesCargaPerigosaRule(response.answer)) {
    // Não logamos o texto da resposta (defesa em profundidade contra PII);
    // apenas o identificador do guardrail e a fonte citada (não-sensível).
    log.warn(
      {
        guardrail: "carga-perigosa",
        source_document: response.source_document,
        reason:
          "Resposta menciona 'carga perigosa' e 'devolução' sem negativa explícita — " +
          "sugere devolução possível, o que contraria a POL-001 (classes 1–6 ANTT não elegíveis).",
      },
      "Resposta do modelo bloqueada pelo Guardrail 2. Retornando fallback seguro.",
    );
    return SAFE_FALLBACK_RESPONSE;
  }

  return response;
}
```

## O code review do código do response-validator

**Contexto adicionado a sessão:**
- [cenario-novatech.md](../docs/cenario-novatech.md)
- [POL-001-politica-devolucao.md](../novatech-assistant/docs/novatech/POL-001-politica-devolucao.md)
- [response-validator.ts](#o-schema-zod-e-o-código-do-response-validator)

**Prompt utilizado:**
```
Atue como um Engenheiro de Software Sênior especialista em revisão de código e segurança. Sua tarefa é fazer um code review rigoroso no código do `response-validator.ts`.

Analise as lógicas de validação e identifique pelo menos **2 problemas estruturais ou falhas de borda**. Preste atenção especial aos seguintes pontos de falha comuns:

- O schema de validação está permitindo a injeção de campos extras não mapeados?
- A expressão regular que identifica "carga perigosa + devolução" é suficientemente robusta para cobrir caixa alta/baixa, erros de digitação comuns, acentuação e diferentes espaçamentos?

Para cada problema identificado, estruture sua resposta da seguinte forma:

1. **Problema Identificado:** Descrição clara da falha.
2. **Cenário de Risco:** Demonstre com um exemplo prático como isso pode causar comportamento indesejado.
3. **Correção Proposta:** Forneça o trecho de código refatorado que soluciona a falha, com comentários pontuais da mudança.
```

**Resultado:**
- [ex-3_1-code-review-response-validator.md](../docs/ex-3_1-code-review-response-validator.md)

## O código do response-validator com as correções do code review

**Resultado:**
- [response-validator.ts](../novatech-assistant/src/services/response-validator.ts)
