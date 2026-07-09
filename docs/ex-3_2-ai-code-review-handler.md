# 📝 Code Review: Módulo de Feedback (`POST /api/feedback`)

**Data:** 07/07/2026\
**Revisor:** Claude Code (Engenheiro de Software Sênior — Segurança, Qualidade e Conformidade de Arquitetura)\
**Alvo da Revisão:** [handler.ts](../novatech-assistant/src/functions/feedback/handler.ts)

---

## ⚠️ Problemas Encontrados

### Problema: Uso de `any` no body da requisição
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `6`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [ ] **Problema de segurança**
- [ ] **Bug em potencial**
- [ ] Outro

#### 📝 Descrição do Problema
*O body HTTP é lido e imediatamente convertido com `await request.json() as any`. O comportamento esperado é tratar toda entrada externa como `unknown` e estreitar o tipo via Zod; o comportamento atual desliga a checagem de tipos exatamente na fronteira mais perigosa (input não confiável), propagando um tipo "coringa" por todo o resto da função.*

#### 💡 Análise Específica
* **Por que fere o AGENTS.md?**
  *Viola a Regra 1 (TypeScript em modo estrito), seção **NÃO DEVE**: "Usar `any`. Para valores de origem desconhecida (input HTTP, JSON externo), use `unknown` e restrinja o tipo via Zod (ver regra 2)." O padrão correto está em `src/functions/query/validator.ts`, cuja função recebe `body: unknown`.*

---

### Problema: Ausência total de validação com Zod na fronteira de confiança
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `6 - 14`, `23`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [x] **Problema de segurança**
- [x] **Bug em potencial**
- [ ] Outro

#### 📝 Descrição do Problema
*Os campos (`queryId`, `rating`, `comment`, `attendantEmail`) são extraídos diretamente do body sem nenhuma validação e persistidos no Cosmos DB. Esperava-se um schema Zod com `.strict()` convertendo falhas em `ValidationError`; o que existe é acesso manual a propriedades de um objeto não confiável, sem garantia de tipo, formato, presença ou limite de tamanho.*

#### 💡 Análise Específica
* **Por que fere o AGENTS.md?**
  *Viola a Regra 2 (Validação exclusivamente com Zod): "Toda entrada que cruza uma fronteira de confiança (body HTTP...) **DEVE** ser parseada e validada com **Zod** antes de ser usada." Não há schema, `.safeParse`, `.strict()` nem conversão para `ValidationError`. Também desrespeita a convenção de módulo do tripé **handler / validator / response-builder** — não existe `validator.ts` e o handler não delega a validação.*

* **Qual é o risco de segurança?**
  *Dado não confiável é gravado no banco sem sanitização (persistência de conteúdo malicioso / poluição de dados). `comment` não tem limite de tamanho: um cliente pode enviar payloads gigantes, gerando abuso de armazenamento e custo (vetor de DoS). `rating` sem faixa aceita qualquer valor, corrompendo métricas.*

* **Por que é um potencial bug?**
  *Qualquer campo ausente é gravado como `undefined`, produzindo documentos malformados. Sem `.strict()`, campos inesperados passam despercebidos. A falta de validação torna o comportamento do endpoint dependente do formato arbitrário do que o cliente enviar.*

---

### Problema: Uso de `console.log` em vez do logger `pino`
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `16`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [ ] **Problema de segurança**
- [ ] **Bug em potencial**
- [ ] Outro

#### 📝 Descrição do Problema
*O registro é feito com `console.log`, quando o projeto exige a instância compartilhada de `pino` (`logger`/`childLogger`) de `src/shared/logger.ts`, com log estruturado e correlação por `requestId`.*

#### 💡 Análise Específica
* **Por que fere o AGENTS.md?**
  *Viola a Regra 3 (Logging exclusivamente com pino): "É **expressamente proibido** usar `console.*`." O ESLint (`no-console`) deve barrar isso no portão de qualidade. Além disso, não há `childLogger({ requestId })` para propagar correlation ID.*

---

### Problema: Vazamento de PII (e-mail e comentário do atendente) em log
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `16`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [x] **Problema de segurança**
- [ ] **Bug em potencial**
- [ ] Outro

#### 📝 Descrição do Problema
*A linha loga o objeto `feedback` inteiro serializado, que contém `attendantEmail` (identificador direto) e `comment` (texto livre, que pode conter PII). Este é exatamente o incidente descrito no `AGENTS.md` ("um módulo de feedback gerado por IA... logou dados sensíveis do atendente") que as regras existem para impedir.*

#### 💡 Análise Específica
* **Por que fere o AGENTS.md?**
  *Viola a Regra 4 (Nunca logar PII): "e-mails, nomes... **NÃO DEVEM** aparecer em log algum, em nenhum nível." Deve-se logar apenas identificadores não-sensíveis (`requestId`, `queryId`) e, no máximo, flags como `{ hasComment: true }`.*

* **Qual é o risco de segurança?**
  *Exposição de dados pessoais em sistemas de log/observabilidade — potencial não-conformidade com a LGPD. Logs costumam ser retidos, replicados e acessíveis a mais pessoas que o banco, ampliando a superfície de vazamento de um identificador direto.*

---

### Problema: `require` dinâmico no meio da função
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `18`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [ ] **Problema de segurança**
- [x] **Bug em potencial**
- [x] Outro (performance)

#### 📝 Descrição do Problema
*`const { CosmosClient } = require('@azure/cosmos')` é um import dinâmico executado dentro da função a cada requisição. O projeto é ESM puro (`"type": "module"`) e exige imports estáticos no topo do arquivo, com extensão `.js` nos paths relativos.*

#### 💡 Análise Específica
* **Por que fere o AGENTS.md?**
  *Viola a Regra 5 (Somente imports estáticos no topo do arquivo): "Usar `require(...)`... no meio da lógica" está listado em **NÃO DEVE**. Em módulo ESM, `require` sequer está disponível no escopo padrão — o código pode nem executar em runtime.*

* **Por que é um potencial bug?**
  *Além do risco de `require is not defined` em ESM, resolver o módulo dentro do caminho quente da requisição adiciona latência desnecessária.*

---

### Problema: Cliente Cosmos criado a cada requisição
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `18 - 21`

#### 🔍 Classificação:
- [ ] **Violação do AGENTS.md**
- [ ] **Problema de segurança**
- [x] **Bug em potencial**
- [x] Outro (performance)

#### 📝 Descrição do Problema
*Um novo `CosmosClient` (e as referências de database/container) é instanciado a cada invocação. O esperado é reutilizar um cliente singleton em nível de módulo, pois o cliente mantém pool de conexões e cache de metadados.*

#### 💡 Análise Específica
* **Por que é um potencial bug?**
  *Sob carga, criar um cliente por requisição multiplica handshakes TCP/TLS, aumenta a latência e pode esgotar sockets/conexões, degradando o endpoint. Isso é especialmente relevante para a demonstração à diretoria em 2 semanas, quando o tráfego concentra.*

---

### Problema: Segredo e config lidos de `process.env` sem validação fail-fast
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `19`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [x] **Problema de segurança**
- [x] **Bug em potencial**
- [ ] Outro

#### 📝 Descrição do Problema
*`process.env.COSMOS_CONNECTION_STRING` é lido diretamente no meio do handler, sem validação. A convenção manda que configuração venha exclusivamente de variáveis de ambiente lidas e validadas no startup com fail-fast (`src/shared/config.ts`).*

#### 💡 Análise Específica
* **Por que fere o AGENTS.md?**
  *Contraria a convenção de módulo: "Configuração vem exclusivamente de variáveis de ambiente, lidas e validadas no startup com **fail-fast** (`src/shared/config.ts`)."*

* **Qual é o risco de segurança?**
  *Uma connection string é um segredo; passá-la ad hoc no handler dificulta rotação e auditoria centralizadas e favorece o vazamento acidental (ex.: em logs de erro).*

* **Por que é um potencial bug?**
  *Se a variável estiver ausente, o valor é `undefined` e o construtor do `CosmosClient` lança em runtime — falha tardia, por requisição, em vez de falha no startup. `TypeScript strict` também acusa `string | undefined` onde se espera `string`.*

---

### Problema: `request.json()` sem tratamento — exceções não tratadas vazam para 500
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `6`, `23`

#### 🔍 Classificação:
- [x] **Violação do AGENTS.md**
- [x] **Problema de segurança**
- [x] **Bug em potencial**
- [ ] Outro

#### 📝 Descrição do Problema
*Não há `try/catch` em toda a função. `await request.json()` lança quando o body não é JSON válido; `container.items.create` lança em falha de rede/banco. Como nada é capturado, a exceção sobe sem mapeamento e o Azure Functions responde 500, potencialmente com detalhes internos.*

#### 💡 Análise Específica
* **Por que fere o AGENTS.md?**
  *Contraria a convenção: "Erros de domínio herdam de `AppError` (`src/shared/errors.ts`) e carregam o `statusCode` HTTP. O handler mapeia erros para respostas **sem vazar stack traces**." Nenhum `AppError`/`ValidationError` é usado nem mapeado.*

* **Qual é o risco de segurança?**
  *Erros não tratados podem retornar stack traces ou mensagens internas ao cliente, revelando estrutura do código e da infraestrutura (info disclosure).*

* **Por que é um potencial bug?**
  *Um body malformado (JSON inválido) derruba a requisição com 500 em vez do 400 adequado. Uma indisponibilidade transitória do Cosmos também vira 500 genérico, sem log estruturado da causa.*

---

### Problema: Documento persistido sem `id`/partition key e endpoint sem autenticação
**Arquivo(s):** `src/functions/feedback/handler.ts` | **Linhas:** `8 - 14`, `23`, `28 - 31`

#### 🔍 Classificação:
- [ ] **Violação do AGENTS.md**
- [x] **Problema de segurança**
- [x] **Bug em potencial**
- [ ] Outro

#### 📝 Descrição do Problema
*O objeto `feedback` não inclui `id` nem um campo de partition key explícito, e o registro em `app.http` não define `authLevel`. Dependendo da configuração do container, `items.create` pode falhar por ausência de partition key; e sem controle de acesso o endpoint fica aberto a escrita anônima.*

#### 💡 Análise Específica
* **Qual é o risco de segurança?**
  *Sem `authLevel` (ou outro mecanismo de autenticação) qualquer cliente na rede pode gravar feedbacks arbitrários no banco — abuso, envenenamento de dados e custo de armazenamento não controlados.*

* **Por que é um potencial bug?**
  *Se o container tiver partition key obrigatória e o documento não a fornecer, `create` lança em runtime. A ausência de `id` delega a geração ao SDK e impede idempotência/deduplicação de reenvios.*

---

## ✅ Recomendação (portão de qualidade)

Este artefato **não deve ser mesclado**. Ele viola as 5 regras não-negociáveis de Coding Standards e reproduz o incidente que o `AGENTS.md` documenta. Correções mínimas antes de reavaliar:

1. **Reestruturar no tripé** `handler / validator / response-builder`, espelhando `src/functions/query/`.
2. **Validar o body com Zod** (`.strict()`, limites em `rating`/`comment`, formato de e-mail), convertendo falhas em `ValidationError`.
3. **Trocar `console.log` por `childLogger({ requestId })`**, logando só identificadores/métricas — nunca `attendantEmail`/`comment`.
4. **Mover `import` do Cosmos para o topo** (estático, ESM) e criar o cliente como **singleton de módulo**.
5. **Centralizar a connection string** em `src/shared/config.ts` (fail-fast no startup).
6. **Envolver o fluxo em `try/catch`**, mapeando `AppError` → `statusCode` e retornando resposta sem stack trace.
7. **Definir `authLevel`/autenticação** e incluir `id`/partition key no documento.

Após as correções, o gate `lint` + `build` + `test` e a revisão humana (human-in-the-loop) das 5 regras devem passar.
