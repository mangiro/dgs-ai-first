## Mapa de cobertura: pergunta → chunks recuperados

A tabela abaixo mostra quais chunks o pipeline de RAG deveria recuperar para perguntas típicas. Use como gabarito para exercícios de avaliação de retrieval.

| Pergunta | Chunks que DEVEM ser recuperados | Chunks que podem aparecer (relevância menor) |
|----------|----------------------------------|----------------------------------------------|
| "Qual o prazo de devolução?" | POL-001-A, POL-001-B | POL-001-C |
| "Posso devolver carga perigosa?" | POL-001-B | FAQ-03, POL-001-A |
| "Qual o SLA do cliente Gold?" | SLA-2024-B | SLA-2024-A, SLA-2024-C |
| "Qual o SLA do cliente Platinum?" | SLA-2024-A (contém "não existem outros tiers") | FAQ-15 |
| "Frete para 600kg para Manaus?" | PROC-042v2-B, PROC-042v2-A | PROC-042-B (versão antiga — risco de contradição) |
| "Frete para 300kg para Salvador?" | Nenhum chunk relevante (frete padrão < 500kg não está documentado) | PROC-042v2-B (parcialmente relevante, mas não cobre < 500kg) |
| "O que acontece com carga danificada?" | FAQ-38 | Nenhum documento formal cobre isso |
| "Carga perigosa com frete expresso?" | FAQ-32 | Nenhum documento formal cobre isso |
| "Qual o multiplicador para o Sudeste?" | PROC-042v2-B | PROC-042-B (versão antiga — contradição: 1.0 vs 1.1) |
| "Prazo de devolução + carga perigosa + frete especial" (multi-domínio) | POL-001-A, POL-001-B, PROC-042v2-A, PROC-042v2-B | FAQ-03 |