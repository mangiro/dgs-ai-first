# Análise de QA — System Prompt V1 (NovaTech Assistente de Conhecimento Operacional)

**Escopo:** Avaliação crítica das respostas geradas pelo modelo durante o teste do System Prompt V1, verificando correção factual, citação de fontes, aderência aos guardrails e identificação de falhas.

**Critérios avaliados:**
1. **Correção Factual** — A resposta está factualmente correta com base nos chunks fornecidos?
2. **Citação de Fonte** — O modelo referenciou corretamente o documento e a seção que embasam sua resposta?
3. **Guardrails** — A linguagem está em português formal? Houve invenção (alucinação) de valores, cláusulas ou procedimentos?
4. **Diagnóstico do Erro** — Onde e por que o modelo falhou, e qual melhoria o system prompt deveria receber?

---

## Pergunta 1 — Carga Perigosa

> *"Qual o prazo de devolução para carga perigosa?"*

- **Correção Factual: Passou** — O modelo identificou corretamente que cargas perigosas (classes 1 a 6 da ANTT) são **exceção** à política de devolução e que não são elegíveis para retorno. Essa é exatamente a "pegadinha" do teste: a pergunta pressupõe que existe um prazo, mas a resposta correta é que o produto não pode ser devolvido. O modelo não caiu na armadilha.
- **Citação de Fonte: Passou** — Citou corretamente o tipo (`Política`), o nome (`Política de Devolução POL-001`) e a seção (`3.2`). O campo de versão/data está ausente, mas a REGRA 1 admite isso quando não está disponível no documento.
- **Guardrails: Passou** — Linguagem em português formal, sem alucinações, sem introdução genérica, sem repetição da pergunta. Formato `[RESPOSTA]` / `[FONTE(S)]` respeitado.
- **Diagnóstico do Erro:** N/A

---

## Pergunta 2 — SLA Cliente Gold

> *"Meu cliente é Gold, qual o SLA de resolução?"*

- **Correção Factual: Passou** — Os valores informados (resolução em até 24h, resposta inicial em até 2h) estão alinhados com o Chunk B. Não há indícios de invenção de dados.
- **Citação de Fonte: Passou parcialmente** — O formato exigido tem três campos: `[Tipo] – [Nome] – [Versão ou Data]`. O modelo produziu apenas dois: `Planilha de Referência – Tabela SLA-2024`. O ano "2024" está embutido no nome do documento, não declarado como campo de data explícito. Se o chunk não trazia versão/data separada, a omissão é aceitável pela cláusula *"quando disponível"*. Recomenda-se verificar se o chunk original possui esse metadado.
- **Guardrails: Passou** — Sem alucinações, tom formal, sem prefácio genérico.
- **Diagnóstico do Erro:** Falha potencial menor de formato. **Hipótese de melhoria:** O system prompt poderia instruir o modelo a inferir a data do nome do documento quando não houver campo separado — por exemplo: *"Se a data/versão não estiver explícita nos metadados, extraia-a do nome do documento quando identificável"*.

---

## Pergunta 3 — Frete 600 kg para Manaus

> *"Quanto custa o frete para 600kg para Manaus?"*

- **Correção Factual: Passou com ressalva** — A aplicação do multiplicador 1,8 para Região Norte e o threshold de 500 kg estão corretos com base no PROC-042-v2. A declaração de ausência do valor-base e o encaminhamento ao supervisor seguem exatamente a REGRA 3. A ressalva: a afirmação *"Manaus está na Região Norte"* pode ter origem no conhecimento de treinamento do modelo e **não necessariamente** no conteúdo do Chunk C. Se o chunk não mapeava explicitamente Manaus à Região Norte, o modelo violou a INSTRUÇÃO 1 (exclusividade das fontes).
- **Citação de Fonte: Passou** — Identificou corretamente `Procedimento – PROC-042-v2 – seção 2`.
- **Guardrails: Passou com ressalva** — O tom é formal e não há invenção de valores. Porém, o uso de formatação de código inline (`` `valor base × 1,8` ``) não está previsto no formato de resposta do system prompt — é uma adição não prescrita, embora inofensiva neste contexto.
- **Diagnóstico do Erro:** Risco de violação da INSTRUÇÃO 1 na classificação geográfica. **Hipótese de melhoria:** O system prompt deveria reforçar que mapeamentos geográficos (qual cidade pertence a qual região) também são dados factuais sujeitos à REGRA 2 — o modelo não deve inferir isso do próprio treinamento. Uma instrução adicional como *"Classificações regionais de cidades devem estar explicitamente mapeadas no documento; não utilize conhecimento geográfico externo"* tornaria o guardrail mais robusto.

---

## Resumo Executivo

| # | Correção Factual | Citação de Fonte | Guardrails | Diagnóstico |
|---|---|---|---|---|
| P1 — Carga perigosa | ✅ Passou | ✅ Passou | ✅ Passou | — |
| P2 — SLA Gold | ✅ Passou | ⚠️ Passou (formato incompleto) | ✅ Passou | Melhorar instrução de extração de data |
| P3 — Frete Manaus | ⚠️ Passou (risco latente) | ✅ Passou | ⚠️ Passou (formato não prescrito) | Cobrir classificações geográficas nos guardrails |

O system prompt performa bem no caso mais crítico (P1, a pegadinha central) e na aplicação da REGRA 3 (P3, ausência de valor-base). Os riscos identificados são sutis e não resultaram em falhas observáveis neste teste, mas representam vetores de alucinação em cenários mais complexos.
