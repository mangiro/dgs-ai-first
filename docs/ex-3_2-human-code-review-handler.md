# 📝 Code Review: [Nome da Funcionalidade ou Pull Request]

**Data:** 06/07/2026\
**Revisor:** Gabriel Mangiro\
**Alvo da Revisão:** [handler.ts](../novatech-assistant/src/functions/feedback/handler.ts)

---

## ⚠️ Problemas Encontrados

### Problema: Infringe o modo estrito do TypeScript
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `6`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [ ] **Problema de segurança**
- [ ] **Bug em potencial**
- [ ] Outro (ex: performance, code smell, padrão de projeto)

#### 📝 Descrição do Problema
*Foi identificado uma má prática que infringe o "strict mode" do TypeScript, isso está descrito como proibido nas intruções do `AGENTS.md`.*

#### 💡 Análise Específica

* **Por que fere o AGENTS.md?**
  *Conforme as intruções presentes no `AGENTS.md`, o uso de `any` viola o "strict mode" do TypeScript: "Usar any. Para valores de origem desconhecida (input HTTP, JSON externo), use unknown e restrinja o tipo via Zod..."*

---

### Problema: Não utilização da dependência `Zod`
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `8 - 14`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [ ] **Problema de segurança**
- [ ] **Bug em potencial**
- [ ] Outro (ex: performance, code smell, padrão de projeto)

#### 📝 Descrição do Problema
*Todo endpoint deve usar Zod como validador, esta é a única biblioteca de validação permitida.*

#### 💡 Análise Específica

* **Por que fere o AGENTS.md?**
  *A regra número 2 da seção de Coding Standards é a principal cláusula que comprova essa violação: "Toda entrada que cruza uma fronteira de confiança (body HTTP...) **DEVE** ser parseada e validada com **Zod** antes de ser usada..."*

---

### Problema: Não utilização da dependência `Pino` para logging
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `16`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [ ] **Problema de segurança**
- [ ] **Bug em potencial**
- [ ] Outro (ex: performance, code smell, padrão de projeto)

#### 📝 Descrição do Problema
*Foi utilizado `console.log()` para registros ao invés do pino que é o padrão do projeto.*

#### 💡 Análise Específica

* **Por que fere o AGENTS.md?**
  *A regra número 3 da seção de Coding Standards é a principal cláusula que comprova essa violação: "Todo registro **DEVE** usar a instância `pino` compartilhada em `src/shared/logger.ts` (`logger` ou `childLogger({...})`). É **expressamente proibido** usar `console.*`"*

---

### Problema: Logs de dados pessoais
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `16`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [ ] **Problema de segurança**
- [ ] **Bug em potencial**
- [ ] Outro (ex: performance, code smell, padrão de projeto)

#### 📝 Descrição do Problema
*Está sendo logado o body json que contém informações como e-mail, que é um dado sensível, e dados sensíveis não devem aparecer em nenhum tipo de log.*

#### 💡 Análise Específica

* **Por que fere o AGENTS.md?**
  *A regra número 4 da seção de Coding Standards especifica o recomendável para esse cenário: "Redigir/omitir campos sensíveis antes de logar (ex.: logar `{ hasEmail: true }`, nunca o e-mail)."*

---

### Problema: Imports fora do padrão
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `18`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [ ] **Problema de segurança**
- [ ] **Bug em potencial**
- [x] Outro (ex: performance, code smell, padrão de projeto)

#### 📝 Descrição do Problema
*O import reportado não segue os padrões descritos nas instruções.*

#### 💡 Análise Específica

* **Por que fere o AGENTS.md?**
  *Segundo a regra número 5 da seção de Coding Standards: Todos os imports devem ser declarados no início do módulo, devem ser estáticos e não dinâmicos com `require` e também não devem ocorrer dentro de funções.*
