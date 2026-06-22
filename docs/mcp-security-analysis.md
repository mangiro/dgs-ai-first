# Análise de Segurança de IA: Model Context Protocol (MCP)

Durante a revisão da arquitetura e configuração (conforme `docs/mcp-architecture.md` e `novatech-assistant/.mcp/mcp.json`) do ambiente de desenvolvimento local, foram identificados riscos críticos de segurança introduzidos pela implementação dos servidores MCP.

Abaixo estão detalhados os riscos, vetores de ameaça, impactos e seus respectivos planos de mitigação.

---

### 1. Sobrescrita Arbitrária de Código via Injeção de Prompt Indireta (Unrestricted Write em `filesystem-code`)
- **Vetor de Ameaça:** O servidor `filesystem-code` concede à ferramenta `write_file` privilégios de escrita ininterruptos nas pastas `src`, `infra` e `tests`. Se o agente ingerir conteúdos maliciosos – por exemplo, processando dados envenenados no arquivo `chunks-novatech.md` (RAG corpus) ou lendo uma issue/documentação comprometida – uma Injeção de Prompt Indireta (*Indirect Prompt Injection*) poderá comandar o agente a injetar um backdoor no código-fonte, ou introduzir recursos inseguros silenciosamente nos arquivos de infraestrutura (como `main.bicep`).
- **Impacto Potencial:** Introdução de código malicioso e corrupção silenciosa da infraestrutura como código (IaC). Se os arquivos Bicep forem alterados, a próxima implantação poderá abrir firewalls, expor instâncias do Cosmos DB ou vazar chaves de APIs. Como não há bloqueios mecânicos na gravação de arquivos, o estrago inicial é feito no ambiente local sem impedimentos.
- **Plano de Mitigação:**
  1. **Técnica:** Implementar o padrão *Human-in-the-Loop (HITL)* obrigatório na interface cliente. A execução do `write_file` via MCP não deve ocorrer silenciosamente, necessitando de um prompt de aprovação com verificação de *diff* direto na interface do desenvolvedor local.
  2. **Arquitetural:** Como alternativa de segurança para agentes puramente cognitivos, instanciar também a base de código como *Read-Only* (apenas extraindo os trechos sugeridos via chat) em vez de habilitar livre navegação de escrita no diretório do projeto.

---

### 2. Sequestro de Execução via Ataque de Cadeia de Suprimentos (Uso inseguro do `npx -y` sem fixação de versão)
- **Vetor de Ameaça:** No arquivo `mcp.json`, os comandos de inicialização dos servidores são declarados usando `npx -y @modelcontextprotocol/server-filesystem` e `server-memory`. A flag `-y` indica ao npx para instalar o pacote silenciosamente e pular a confirmação da instalação. Além disso, as versões não estão fixadas (ex: `@1.0.0`). Sempre que o cache local for limpo ou uma nova versão for publicada, o npx buscará automaticamente a versão mais recente (*latest*) no registro do NPM e a executará imediatamente.
- **Impacto Potencial:** Se um atacante conseguir assumir a conta do mantenedor oficial no NPM (Account Takeover) ou utilizar técnicas de confusão de dependências para enviar uma versão maliciosa dos servidores MCP, o ambiente de desenvolvimento fará o download e executará automaticamente o malware. O código malicioso rodará com os privilégios do usuário logado na máquina, permitindo roubo de credenciais (ex: SSH, tokens AWS/Azure) e exfiltração de dados sensíveis da máquina do desenvolvedor.
- **Plano de Mitigação:**
  1. **Configuração Técnica:** Alterar o `mcp.json` para utilizar versões estritamente "pinadas" (travadas) em todos os comandos (ex: `npx @modelcontextprotocol/server-filesystem@0.6.2`).
  2. **Arquitetural:** Instalar os servidores como dependências do projeto local (no `package.json` em `devDependencies`) e usar o arquivo `package-lock.json` ou `yarn.lock` para congelar os hashes de integridade das dependências. Em seguida, usar a chamada do script local no `mcp.json`, garantindo rastreabilidade e controle absoluto do código executado.
