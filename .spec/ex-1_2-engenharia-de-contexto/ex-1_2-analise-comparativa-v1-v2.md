# Análise Comparativa — System Prompt V1 × V2

**Escopo:** Avaliação comparativa estruturada entre os testes do System Prompt V1 e V2, verificando evolução de qualidade, correção das falhas identificadas no QA e introdução de regressões.

**Dimensões avaliadas:**
1. Qualidade e precisão da resposta
2. Aderência ao formato exigido (`[RESPOSTA]`, `[FONTE(S)]`, `[OBSERVAÇÕES]`)
3. Tratamento de lacunas informacionais
4. Clareza das instruções de escalonamento ao supervisor

---

## Tabela 1 — Comparativo por Pergunta

| Pergunta | Dimensão | V1 | V2 | Resultado |
|---|---|---|---|---|
| **P1 — Carga Perigosa** | Correção factual | Identificou corretamente a exclusão; não caiu na armadilha de "prazo" | Idêntico | = |
| | Aderência ao formato | `[RESPOSTA]` + `[FONTE(S)]` apenas — `[OBSERVAÇÕES]` ausente | `[RESPOSTA]` + `[FONTE(S)]` + `[OBSERVAÇÕES]` com orientação de escalonamento | ✅ Melhorou |
| | Clareza do escalonamento | Ausente — nenhuma orientação ao atendente | Presente e explícita: "suspender a tratativa e escalar ao supervisor" | ✅ Melhorou |
| **P2 — SLA Gold** | Correção factual | Valores corretos (24h resolução / 2h resposta inicial) | Idêntico | = |
| | Citação de fonte / data | `Tabela SLA-2024` sem extração explícita do campo data | `Tabela SLA-2024` sem extração explícita do campo data | ⚠️ Não corrigido |
| | Aderência ao formato | Compliant | Compliant | = |
| **P3 — Frete 600 kg Manaus** | Uso de conhecimento geográfico externo | Afirmou "Manaus está na Região Norte" sem respaldo documental — risco de violação da INSTRUÇÃO 1 | Recusou classificar Manaus: *"a documentação disponível não mapeia cidades às suas respectivas regiões"* | ✅ Corrigido |
| | Formatação inline (backticks) | Usou `` `valor base × 1,8` `` — não previsto no formato | Eliminado; fórmula expressa em linguagem corrente | ✅ Corrigido |
| | Completude da declaração de ausência | Parcial — declarou ausência do valor-base, mas forneceu o multiplicador como se a classificação regional fosse certa | Completa — declarou ausência de dois dados: região de Manaus e valor-base | ✅ Melhorou |
| | Clareza do escalonamento | Presente mas genérica ("escalar ao supervisor") | Específica: lista os dois itens que o supervisor precisa fornecer antes de retornar ao cliente | ✅ Melhorou |

---

## Tabela 2 — Falhas do QA V1: corrigidas no V2?

| Falha identificada no QA V1 | System Prompt V2 | Resposta V2 | Status |
|---|---|---|---|
| Modelo inferiu classificação geográfica do treinamento (P3) | REGRA 2 ampliada: *"Classificações geográficas... também são dados factuais sujeitos a esta regra"* | Recusou corretamente a classificação | ✅ Corrigida |
| Uso de backtick para fórmula (P3) | Nova restrição de formato: *"Não utilize formatação de código inline para fórmulas ou valores"* | Fórmula expressa em prosa | ✅ Corrigida |
| Data não extraída explicitamente do nome do documento (P2) | REGRA 1 ampliada: instrução para inferir data do nome quando ausente dos metadados | Resposta ainda exibe `Tabela SLA-2024` sem campo de data separado | ⚠️ Instrução adicionada, execução não observada |

---

## Tabela 3 — Regressões introduzidas no V2

| Aspecto | Observação | Severidade |
|---|---|---|
| **[OBSERVAÇÕES] em P1** | A V1 não gerou `[OBSERVAÇÕES]` para P1 — o que é defensável, pois a resposta era completa. A V2 adicionou o campo com orientação de escalonamento. Isso é funcionalmente correto (uso (b) do campo), mas representa um nível de verbosidade maior para um caso que a V1 resolvia em duas seções. | Neutra / leve melhoria |
| **Extração de data em P2** | A instrução foi adicionada ao prompt mas não se materializou na resposta. Indica que a diretiva pode precisar de reformulação mais imperativa — por exemplo: *"DEVE incluir no campo de fonte: [Nome] – data inferida: [ano]"*. | Baixa |

---

## Parecer Final

**O V2 representa uma evolução efetiva sobre o V1** — especialmente para o caso de maior risco: P3.

A falha crítica da V1 (classificar Manaus como Região Norte a partir de conhecimento de treinamento) foi **eliminada**: a V2 recusou corretamente a classificação e declarou a ausência do dado, fechando o principal vetor de alucinação identificado no QA.

As demais correções — adição explícita do escalonamento em P1 — são menores mas coerentes com os problemas diagnosticados.

**O único ponto residual** é a extração de data em P2 (REGRA 1 ampliada): a instrução foi adicionada ao prompt, mas a resposta não a aplicou visivelmente. O campo `Tabela SLA-2024` ainda aparece sem `data inferida: 2024` como campo separado. A instrução pode precisar ser reformulada com linguagem mais imperativa ou com um exemplo de saída esperada diretamente na seção de formato.

### Resumo Executivo

| | P1 | P2 | P3 |
|---|---|---|---|
| **V1** | ✅ | ⚠️ | ⚠️ |
| **V2** | ✅+ | ⚠️ | ✅ |
| **Evolução** | Melhorou | Estacionou | Corrigido |
