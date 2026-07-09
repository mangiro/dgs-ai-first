# Code review de segurança do `response-validator.ts`

---

## Resultado do code review

Review completo do `response-validator.ts` cruzando a lógica com a POL-001 (fonte
normativa que o Guardrail 2 tenta proteger). Foram encontradas **3 falhas** — duas de
borda com impacto direto de segurança, e uma correção honesta sobre um dos pontos
levantados no prompt.

> **Nota sobre injeção de campos extras:** o ponto levantado no prompt **já está
> corretamente tratado**. O `.strict()` (linha 41) rejeita qualquer chave não mapeada e
> cai no fallback. Não há vulnerabilidade de campo extra — o risco real de schema está na
> falha #3.

---

### Problema 1 — O gatilho "carga perigosa" é evadido por plural, espaçamento e acento (falso-negativo crítico)

**1. Problema Identificado:**
O `violatesCargaPerigosaRule` (linhas 106–123) detecta o tema com
`normalized.includes("carga perigosa")` — um *substring match* sobre texto apenas em
`toLowerCase()`. Isso quebra em três eixos:

- **Plural:** `"cargas perigosas".includes("carga perigosa")` → **`false`**. O `s` de
  "cargas" e o `s` de "perigosas" impedem o casamento contíguo.
- **Espaçamento:** `"carga  perigosa"` (espaço duplo) ou quebra de linha entre as
  palavras → não casa.
- **Acento/typo:** o `.trim()`/`toLowerCase()` não normaliza diacríticos, então a lógica
  é frágil (a lista de negações tenta compensar isso à mão, o que é sintoma do problema —
  ver #2).

**2. Cenário de Risco:**
A própria POL-001 (seção 3.2) escreve no **plural**: *"Cargas perigosas classificadas nas
classes 1 a 6…"*. Uma resposta fiel do modelo tende a reproduzir esse fraseado. Pior
caso, uma alucinação bem plausível:

> *"Sim, cargas perigosas classes 1 a 6 podem ser devolvidas normalmente pelo processo
> padrão em até 7 dias."*

Como `"carga perigosa"` (singular) **não** é substring de `"cargas perigosas"`,
`mentionsCargaPerigosa` é `false`, a inspeção nem roda, e a **afirmação perigosa passa
direto** com o `confidence_score` do modelo. O guardrail que existe justamente para esse
caso é cego para a forma mais natural do texto.

**3. Correção Proposta:**

```ts
/**
 * Normaliza para comparação: remove acentos (NFD), baixa a caixa e colapsa
 * espaços/quebras de linha. Ponto único de normalização — triggers E negações
 * passam por aqui, eliminando a lista de variantes acentuadas escrita à mão.
 */
function normalize(text: string): string {
  return text
    .normalize("NFD")                 // separa base + diacrítico
    .replace(/[̀-ͯ]/g, "")  // remove os diacríticos
    .toLowerCase()
    .replace(/\s+/g, " ")             // colapsa espaço duplo / quebra de linha
    .trim();
}

// Regex tolerante a plural e a espaçamento variável (após normalize já sem acento):
//   cargas? perigosas?  →  "carga perigosa", "cargas perigosas"
const CARGA_PERIGOSA_RE = /cargas?\s+perigosas?/;
//   devolu... →  devolucao, devolver, devolvida, devolvidas...
const DEVOLUCAO_RE = /devolu\w*/;
```

---

### Problema 2 — A negação é buscada no texto inteiro: um marcador solto libera a afirmação perigosa

**1. Problema Identificado:**
`hasNegation` (linhas 117–119) faz `NEGATION_MARKERS.some(marker => normalized.includes(marker))`
sobre **o texto todo**. Não há vínculo entre a negativa e a frase que associa "carga
perigosa" a "devolução". Basta **qualquer** marcador aparecer em **qualquer** lugar da
resposta para o bloqueio ser desligado. Isso inverte a filosofia fail-safe descrita no
cabeçalho (linhas 66–72): o silêncio deveria bloquear, mas um "não é possível" fora de
contexto abre a porta.

**2. Cenário de Risco:**
Marcadores como `"gestão de riscos"` e `"não é possível"` são frases que uma resposta
sobre esse tema quase sempre menciona por outros motivos:

> *"Você pode devolver sua carga perigosa pelo portal. Não é possível anexar mais de 5
> fotos, e a gestão de riscos não precisa ser acionada nesse caso."*

A frase de ação (**"pode devolver sua carga perigosa"**) é uma alucinação de alto risco.
Mas o texto contém `"não é possível"` (referindo-se às fotos) **e** `"gestão de riscos"` →
`hasNegation = true` → a resposta é **liberada**. O guardrail foi contornado por menções
colaterais.

**3. Correção Proposta:** escopar a negativa à **mesma sentença** que junta os dois temas.

```ts
function violatesCargaPerigosaRule(answer: string): boolean {
  const normalized = normalize(answer);

  // Só inspeciona quando os DOIS temas aparecem no texto.
  if (!CARGA_PERIGOSA_RE.test(normalized) || !DEVOLUCAO_RE.test(normalized)) {
    return false;
  }

  // Isola as sentenças que associam "carga perigosa" E "devolução" na MESMA frase.
  const sentences = normalized.split(/[.!?;\n]+/);
  const riskSentences = sentences.filter(
    (s) => CARGA_PERIGOSA_RE.test(s) && DEVOLUCAO_RE.test(s),
  );

  // Se os temas nunca coincidem numa mesma frase, mantém o bloqueio conservador
  // (fail-safe): coocorrência distante ainda merece revisão humana.
  if (riskSentences.length === 0) return true;

  // A negativa precisa estar NA frase de risco — não solta em outro ponto do texto.
  const everyRiskSentenceNegated = riskSentences.every((s) =>
    NEGATION_MARKERS.some((marker) => s.includes(marker)),
  );

  return !everyRiskSentenceNegated; // bloqueia se QUALQUER frase de risco não negar
}
```

E a lista de marcadores encolhe e fica consistente, já que `normalize` remove acento:

```ts
// Sem variantes acentuadas duplicadas — normalize() já removeu diacríticos.
const NEGATION_MARKERS: readonly string[] = [
  "nao e possivel",
  "nao e elegivel",
  "nao sao elegiveis",
  "nao elegivel",
  "inelegivel",
  "nao pode ser devolvid",
  "nao podem ser devolvid",
  "nao permite",
  "nao e permitido",
  "nao aceita",
  "excecao ao prazo",
  "gestao de riscos",
];
```

---

### Problema 3 — `source_document` aceita qualquer string: Guardrail 1 valida presença, não veracidade

**1. Problema Identificado:**
O schema (linhas 32–35) exige que `source_document` seja não-vazio, e o comentário chama
isso de "Guardrail 1 (Obrigatoriedade de Fonte)". Mas não há **allowlist** dos documentos
que existem de fato. `min(1)` só garante que *algo* foi escrito.

**2. Cenário de Risco:**
Dado o contexto do cenário (12% de alucinação, chunk incorreto recuperado), o modelo pode
citar uma fonte inexistente:

```json
{ "answer": "Devoluções têm prazo de 30 dias.", "source_document": "POL-042-devolucao-estendida", "confidence_score": 0.95 }
```

Isso passa por Zod e por Guardrail 2 (não menciona carga perigosa) e chega ao atendente
com uma **citação fabricada** e confiança alta — exatamente o tipo de alucinação com
aparência de credibilidade que o harness deveria conter.

**3. Correção Proposta:** validar contra o conjunto de fontes conhecidas.

```ts
// Fonte única de verdade dos documentos indexados (idealmente derivada do índice).
const KNOWN_SOURCES = new Set(["POL-001", "PROC-088", /* ... */]);

source_document: z
  .string({ required_error: "O campo 'source_document' é obrigatório." })
  .trim()
  .min(1, "O campo 'source_document' é obrigatório e não pode ser vazio.")
  // Guardrail 1 reforçado: a fonte precisa existir no acervo indexado.
  .refine((doc) => KNOWN_SOURCES.has(doc.split("::")[0].split("-").slice(0, 2).join("-")),
    "Fonte citada não corresponde a um documento conhecido."),
```

*(O parsing exato do ID depende do formato real das fontes no índice — vale confirmar como
o pipeline de RAG rotula os chunks antes de fixar o `refine`.)*

---

## Resumo

| # | Falha | Impacto | Direção |
|---|-------|---------|---------|
| 1 | Trigger por substring quebra em plural/espaço/acento | Alucinação perigosa **passa** | Falso-negativo (crítico) |
| 2 | Negação buscada no texto inteiro | Menção colateral **desliga** o guardrail | Falso-negativo (crítico) |
| 3 | `source_document` sem allowlist | Citação fabricada com alta confiança | Alucinação não contida |

As duas primeiras são as mais graves porque **derrotam silenciosamente** o Guardrail 2 na
direção insegura (deixam passar), o oposto da filosofia fail-safe declarada no próprio
arquivo.
