# Relatório de Acurácia do Retrieval — Pipeline RAG

**Data:** 2026-06-08  
**Script testado:** `build_prompt.py` (CLI: `python build_prompt.py "<pergunta>" --top-n 5`)  
**Base de referência:** [mapa-cobertura-chunks.md](../docs/mapa-cobertura-chunks.md)

## Mapeamento de Chunk IDs do Gabarito → ChromaDB

| Chunk ID (Gabarito) | Documento no ChromaDB | Seção | Índice |
|----------------------|-----------------------|-------|--------|
| POL-001-A | POL-001-politica-devolucao.md | 3.1. Prazo geral | 13 |
| POL-001-B | POL-001-politica-devolucao.md | 3.2. Exceções ao prazo geral | 14 |
| POL-001-C | POL-001-politica-devolucao.md | 3.3. Procedimento de devolução | 15 |
| SLA-2024-A | SLA-2024-tabela-sla-clientes.md | 1. Classificação de clientes | 32 |
| SLA-2024-B | SLA-2024-tabela-sla-clientes.md | 2. Tabela de SLAs | 33 |
| SLA-2024-C | SLA-2024-tabela-sla-clientes.md | 3. Definição de incidente crítico | 34 |
| PROC-042v2-A | PROC-042-v2-frete-especial-revisado.md | 2. Fórmula de cálculo | 26 |
| PROC-042v2-B | PROC-042-v2-frete-especial-revisado.md | 2.1. Multiplicadores regionais | 27 |
| PROC-042-B | PROC-042-frete-especial-v1.md | 2.1. Multiplicadores regionais | 21 |

---

## Resultados por Pergunta

### Pergunta 1: "Qual o prazo de devolução?"

**Gabarito:** Obrigatórios → POL-001-A, POL-001-B | Opcionais → POL-001-C

| # | Chunk Recuperado | Seção | Score (distância) | Presente no Gabarito? | Classificação |
|---|------------------|-------|--------------------|-----------------------|---------------|
| 1 | POL-001-politica-devolucao.md (idx 17) | 3.5. Custos de devolução | 0.870416 | Não | Irrelevante |
| 2 | POL-001-politica-devolucao.md (idx 15) | 3.3. Procedimento de devolução | 0.938981 | Sim | Opcional (POL-001-C) |
| 3 | PROC-042-frete-especial-v1.md (idx 22) | 3. Prazo de entrega para frete especial | 0.949223 | Não | Irrelevante |
| 4 | SLA-2024-tabela-sla-clientes.md (idx 34) | 3. Definição de incidente crítico | 0.988235 | Não | Irrelevante |
| 5 | FAQ-atendimento.md (idx 0) | Introdução FAQ | 1.048753 | Não | Irrelevante |

- **Chunks obrigatórios recuperados:** 0 de 2
- **Chunks irrelevantes (falso positivo):** 3
- **Chunks obrigatórios ausentes (falso negativo):** POL-001-A (3.1. Prazo geral), POL-001-B (3.2. Exceções ao prazo geral)
- **Veredicto:** ❌ FALHOU

**Observação:** O retrieval priorizou "Custos de devolução" (seção 3.5) sobre "Prazo geral" (seção 3.1), que é a seção diretamente responsiva à pergunta. O chunk sobre prazo de frete (PROC-042) foi atraído pela palavra "prazo", criando confusão semântica inter-documental.

---

### Pergunta 2: "Posso devolver carga perigosa?"

**Gabarito:** Obrigatórios → POL-001-B | Opcionais → FAQ-03, POL-001-A

| # | Chunk Recuperado | Seção | Score (distância) | Presente no Gabarito? | Classificação |
|---|------------------|-------|--------------------|-----------------------|---------------|
| 1 | PROC-042-frete-especial-v1.md (idx 23) | 4. Condições especiais | 0.867998 | Não | Irrelevante |
| 2 | FAQ-atendimento.md (idx 4) | Item 22 — Seguro de carga | 0.910285 | Não | Irrelevante |
| 3 | SLA-2024-tabela-sla-clientes.md (idx 34) | 3. Definição de incidente crítico | 0.930997 | Não | Irrelevante |
| 4 | PROC-042-v2-frete-especial-revisado.md (idx 29) | 4. Condições especiais | 0.979535 | Não | Irrelevante |
| 5 | POL-001-politica-devolucao.md (idx 17) | 3.5. Custos de devolução | 1.011082 | Não | Irrelevante |

- **Chunks obrigatórios recuperados:** 0 de 1
- **Chunks irrelevantes (falso positivo):** 5
- **Chunks obrigatórios ausentes (falso negativo):** POL-001-B (3.2. Exceções ao prazo geral — contém regras sobre carga perigosa)
- **Veredicto:** ❌ FALHOU

**Observação:** O termo "carga perigosa" atraiu chunks de "condições especiais" dos documentos de frete (PROC-042 v1 e v2), que tratam de restrições de frete — não de política de devolução. O chunk correto (POL-001, seção 3.2 — Exceções) não foi recuperado em nenhuma das 5 posições.

---

### Pergunta 3: "Qual o SLA do cliente Gold?"

**Gabarito:** Obrigatórios → SLA-2024-B | Opcionais → SLA-2024-A, SLA-2024-C

| # | Chunk Recuperado | Seção | Score (distância) | Presente no Gabarito? | Classificação |
|---|------------------|-------|--------------------|-----------------------|---------------|
| 1 | SLA-2024-tabela-sla-clientes.md (idx 36) | 5. Medição e reportes | 0.879903 | Não | Irrelevante |
| 2 | FAQ-atendimento.md (idx 5) | Item 27 — Tracking em trânsito | 0.937881 | Não | Irrelevante |
| 3 | SLA-2024-tabela-sla-clientes.md (idx 32) | 1. Classificação de clientes | 0.948318 | Sim | Opcional (SLA-2024-A) |
| 4 | FAQ-atendimento.md (idx 8) | Item 41 — Diferença SLA resposta vs resolução | 0.953952 | Não | Irrelevante |
| 5 | FAQ-atendimento.md (idx 3) | Item 15 — Platinum tier | 0.973756 | Não | Irrelevante |

- **Chunks obrigatórios recuperados:** 0 de 1
- **Chunks irrelevantes (falso positivo):** 3
- **Chunks obrigatórios ausentes (falso negativo):** SLA-2024-B (2. Tabela de SLAs — contém os valores de SLA por tier)
- **Veredicto:** ❌ FALHOU

**Observação:** O chunk com a tabela de SLAs propriamente dita (SLA-2024-B, seção 2) — que contém os valores concretos de SLA do tier Gold — não foi recuperado. O retrieval trouxe seções periféricas do mesmo documento (Medição, Classificação) e FAQs sobre SLA genérico.

---

### Pergunta 4: "Frete para 600kg para Manaus?"

**Gabarito:** Obrigatórios → PROC-042v2-A, PROC-042v2-B | Opcionais → PROC-042-B (versão antiga)

| # | Chunk Recuperado | Seção | Score (distância) | Presente no Gabarito? | Classificação |
|---|------------------|-------|--------------------|-----------------------|---------------|
| 1 | PROC-042-frete-especial-v1.md (idx 19) | 1. Objetivo (v1) | 0.911188 | Não | Irrelevante |
| 2 | PROC-042-v2-frete-especial-revisado.md (idx 25) | 1. Objetivo (v2) | 0.999817 | Não | Irrelevante |
| 3 | PROC-042-v2-frete-especial-revisado.md (idx 26) | 2. Fórmula de cálculo (v2) | 1.008311 | Sim | Obrigatório (PROC-042v2-A) ✅ |
| 4 | PROC-042-frete-especial-v1.md (idx 20) | 2. Fórmula de cálculo (v1) | 1.011914 | Não | Irrelevante |
| 5 | FAQ-atendimento.md (idx 5) | Item 27 — Tracking em trânsito | 1.053236 | Não | Irrelevante |

- **Chunks obrigatórios recuperados:** 1 de 2
- **Chunks irrelevantes (falso positivo):** 3
- **Chunks obrigatórios ausentes (falso negativo):** PROC-042v2-B (2.1. Multiplicadores regionais — necessário para determinar o multiplicador da região Norte/Manaus)
- **Veredicto:** ⚠️ PARCIAL

**Observação:** A fórmula de cálculo (v2) foi recuperada, mas os multiplicadores regionais — indispensáveis para calcular o frete para Manaus — ficaram de fora do top-5. Dois slots foram ocupados por chunks de "Objetivo" (v1 e v2), que fornecem apenas descrição genérica do procedimento.

---

### Pergunta 5: "Qual o multiplicador para o Sudeste?"

**Gabarito:** Obrigatórios → PROC-042v2-B | Opcionais → PROC-042-B (versão antiga)

| # | Chunk Recuperado | Seção | Score (distância) | Presente no Gabarito? | Classificação |
|---|------------------|-------|--------------------|-----------------------|---------------|
| 1 | POL-001-politica-devolucao.md (idx 16) | 3.4. Devoluções parciais | 0.953223 | Não | Irrelevante |
| 2 | FAQ-atendimento.md (idx 2) | Item 8 — Como funciona o frete especial? | 0.980068 | Não | Irrelevante |
| 3 | PROC-042-v2-frete-especial-revisado.md (idx 27) | 2.1. Multiplicadores regionais (v2) | 1.008213 | Sim | Obrigatório (PROC-042v2-B) ✅ |
| 4 | PROC-042-frete-especial-v1.md (idx 21) | 2.1. Multiplicadores regionais (v1) | 1.011213 | Sim | Opcional (PROC-042-B) ✅ |
| 5 | POL-001-politica-devolucao.md (idx 15) | 3.3. Procedimento de devolução | 1.021266 | Não | Irrelevante |

- **Chunks obrigatórios recuperados:** 1 de 1
- **Chunks opcionais recuperados:** 1 (PROC-042-B)
- **Chunks irrelevantes (falso positivo):** 2
- **Veredicto:** ✅ PASSOU

**Observação:** Único caso de sucesso completo. Ambas as versões dos multiplicadores (v2 e v1) foram recuperadas. Porém, 2 dos 5 slots foram ocupados por chunks de Política de Devolução, completamente fora do domínio da pergunta — indicando ruído no embedding.

---

## Análise Consolidada

### Tabela-Resumo

| Pergunta | Recall (obrigatórios) | Falsos Positivos | Veredicto |
|----------|-----------------------|-------------------|-----------|
| 1. "Qual o prazo de devolução?" | 0/2 (0%) | 3 | ❌ FALHOU |
| 2. "Posso devolver carga perigosa?" | 0/1 (0%) | 5 | ❌ FALHOU |
| 3. "Qual o SLA do cliente Gold?" | 0/1 (0%) | 3 | ❌ FALHOU |
| 4. "Frete para 600kg para Manaus?" | 1/2 (50%) | 3 | ⚠️ PARCIAL |
| 5. "Qual o multiplicador para o Sudeste?" | 1/1 (100%) | 2 | ✅ PASSOU |

### Métricas Globais

- **Total de chunks obrigatórios esperados:** 7
- **Total de chunks obrigatórios recuperados:** 2
- **Taxa de acerto global (Recall@5 obrigatórios):** **28,6%** (2/7)
- **Total de falsos positivos:** 16 (de 25 slots totais)
- **Taxa de precisão sobre gabarito:** 12% (3 hits em 25 slots, contando opcionais)

### Padrões de Falha Identificados

1. **Confusão semântica inter-documental:** Termos compartilhados entre documentos (ex: "prazo", "carga perigosa", "condições especiais") direcionam o retrieval para documentos do domínio errado (frete em vez de devolução, e vice-versa).

2. **Priorização de seções periféricas:** Dentro do mesmo documento, seções genéricas ou de suporte (Custos, Medição, Objetivo) são frequentemente ranqueadas acima das seções com o conteúdo central da resposta (Prazo geral, Tabela de SLAs, Multiplicadores).

3. **Ruído cross-domain persistente:** Em 4 das 5 perguntas, pelo menos um chunk de documento completamente fora do domínio da pergunta ocupou um slot no top-5 (ex: POL-001 aparecendo em perguntas sobre frete).

### Conclusão

O pipeline de retrieval apresenta recall insuficiente (**28,6%**) para uso em produção. As 3 falhas completas indicam que o modelo de embedding atual não discrimina adequadamente entre seções semanticamente próximas mas funcionalmente distintas dentro do corpus NovaTech.
