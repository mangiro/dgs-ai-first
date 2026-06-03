## Decomposição Estrutural do System Prompt — NovaTech Logística

### Tabela de Componentes

| Componente / Bloco | Tipo | Descrição Resumida | Tokens Estimados |
|---|---|---|---|
| `<identidade>` | **ESTÁTICO** | Define o papel do assistente (Assistente de Conhecimento Operacional), o domínio de atuação (logística NovaTech) e as limitações de escopo ("não sou uso geral, não especulo"). É o núcleo de ancoragem comportamental — jamais deve variar. | **~150** |
| `<guardrails>` — REGRA 1 (Citação obrigatória) | **ESTÁTICO** | Impõe que toda resposta factual cite explicitamente o documento de origem, tipo e versão. Define o critério de validade de uma resposta. | **~80** |
| `<guardrails>` — REGRA 2 (Proibição de invenção) | **ESTÁTICO** | Proíbe geração de dados numéricos (prazos, valores, SLAs) não presentes textualmente nos chunks. Hard constraint anti-alucinação. | **~75** |
| `<guardrails>` — REGRA 3 (Ausência declarada) | **ESTÁTICO** | Instrui o modelo a declarar explicitamente quando a documentação não contém a resposta, e a escalar ao supervisor. Define o fallback comportamental. | **~70** |
| `<guardrails>` — REGRA 4 (Língua e registro) | **ESTÁTICO** | Define o registro linguístico: PT-BR formal mas acessível, tom profissional e direto. | **~45** |
| `<formato_de_resposta>` — Template `[RESPOSTA]` | **ESTÁTICO** | Estrutura obrigatória da seção principal: objetiva, sem parafrasear a pergunta, priorizando clareza. | **~65** |
| `<formato_de_resposta>` — Template `[FONTE(S)]` | **ESTÁTICO** | Estrutura de listagem de fontes consultadas com formato bullet padronizado. | **~40** |
| `<formato_de_resposta>` — Template `[OBSERVAÇÕES]` | **ESTÁTICO** | Campo condicional para conflito de fontes, escalonamento ou desatualização potencial. | **~65** |
| `<formato_de_resposta>` — Restrições de formato | **ESTÁTICO** | 4 restrições negativas (sem intro genérica, sem repetir pergunta) e 2 permissivas (listas e tabelas condicionais). | **~80** |
| `<instrucoes_de_consulta>` — INSTRUÇÃO 1 (Exclusividade das fontes) | **ESTÁTICO** | Proíbe uso do conhecimento de treinamento como fonte; limita respostas estritamente aos chunks injetados. Força o modelo a operar em modo RAG puro. | **~90** |
| `<instrucoes_de_consulta>` — INSTRUÇÃO 2 (Prioridade de chunks) | **ESTÁTICO** | Instrui a avaliação semântica diferenciada entre chunks — rejeita tratamento uniforme de todos os trechos recuperados. | **~65** |
| `<instrucoes_de_consulta>` — INSTRUÇÃO 3 (Matriz de conflitos) | **ESTÁTICO** | Hierarquia completa de resolução de conflitos: Critério Temporal → Critério de Autoridade (5 níveis) → Exceção com escalonamento obrigatório. O bloco mais denso em tokens do prompt. | **~250** |
| **[DINÂMICO] Chunks RAG recuperados** | **DINÂMICO** | Trechos dos documentos NovaTech retornados pelo sistema vetorial a cada query. Volume varia com o tipo de consulta (3–15 chunks × ~500 tokens). | **~1.500–7.500** |
| **[DINÂMICO] Query do atendente** | **DINÂMICO** | Pergunta atual submetida na sessão. | **~50–200** |
| **[DINÂMICO] Histórico de conversa** | **DINÂMICO** | Turnos anteriores da sessão, se implementado em modo multi-turn (3 turnos ≈ 1.500 tokens). | **~0–1.500** |
| **[DINÂMICO] Reformulação / HyDE da query** | **DINÂMICO** | Expansão da query para melhora de retrieval (opcional, conforme pipeline da seção 4.4 da análise RAG). | **~0–300** |

---

### Cálculo de Custo de Contexto

#### Contexto Fixo (tokens estáticos — pagos em **toda** query)

| Bloco | Tokens |
|---|---|
| `<identidade>` | 150 |
| `<guardrails>` (4 regras) | 270 |
| `<formato_de_resposta>` (template + restrições) | 250 |
| `<instrucoes_de_consulta>` (3 instruções + matriz) | 405 |
| Overhead estrutural (tags XML, separadores) | 50 |
| **Total Estático** | **≈ 1.125 tokens** |

> **Nota de calibração:** a análise RAG (seção 3.2) orça 2.000 tokens para o system prompt. A diferença (~875 tokens) representa margem de segurança para expansões futuras — útil se o prompt for estendido com exemplos few-shot ou regras adicionais de domínio.

#### Contexto Variável (estimativa por tipo de consulta)

| Cenário de Query | Chunks RAG | Query + HyDE | Histórico | Total Dinâmico | **Total da Janela** |
|---|---|---|---|---|---|
| Factual simples ("Qual SLA tipo Gold?") | 3 × 500 = **1.500** | ~200 | 0 | **~1.700** | **~2.825** |
| Procedural ("Passos para reclamação?") | 7 × 500 = **3.500** | ~350 | ~750 | **~4.600** | **~5.725** |
| Comparativa ("Diferença política A vs B?") | 12 × 500 = **6.000** | ~400 | ~1.500 | **~7.900** | **~9.025** |
| Síntese ("Regras de frete Região Sul") | 15 × 500 = **7.500** | ~450 | ~1.500 | **~9.450** | **~10.575** |

---

### Observações Arquiteturais

**1. Eficiência do design estático:** Os ~1.125 tokens fixos cobrem quatro funções críticas simultaneamente (persona, guardrails, formato e lógica RAG). É um prompt compacto dado o nível de controle comportamental que impõe — o bloco mais custoso (`<instrucoes_de_consulta>`) carrega a lógica de negócio mais complexa (matriz de conflitos) e representa apenas ~36% do total estático.

**2. Candidato a cache:** O bloco estático inteiro é ideal para **prompt caching** (ex: Anthropic API `cache_control: ephemeral`). Com TTL de 5 minutos e volume alto de queries simultâneas de atendentes, a economia pode chegar a 90% do custo dos tokens de input fixos.

**3. Ponto de atenção — `<instrucoes_de_consulta>`:** Este bloco pressupõe que os chunks serão injetados no contexto, mas o prompt não define **onde** e **em que formato** os chunks chegam (como mensagem `user`, bloco `<context>` separado, ou dentro de um template). Essa lacuna deve ser endereçada na camada de orquestração da aplicação, não no próprio system prompt.
