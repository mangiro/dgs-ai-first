# Arquitetura de Servidores MCP (Model Context Protocol)

Abaixo está o mapeamento da arquitetura de integração dos Agentes de IA utilizando servidores MCP de referência, projetado para garantir alto grau de autonomia atrelado ao princípio de privilégio mínimo (least privilege) no ambiente de desenvolvimento local.

---

### 1. Código-fonte do projeto
- **Servidor MCP:** `@modelcontextprotocol/server-filesystem`
- **Exposição:**
  - **Tools:** `read_file`, `write_file`, `search_files`, `list_directory`.
  - **Resources:** URIs de arquivos de código (ex: `file://../novatech-assistant/src/`).
- **Consumo:** O agente utiliza as tools de listagem, busca e leitura para entender a lógica das *Azure Functions* e templates *Bicep*. Durante o *Spec Driven Development*, utiliza a tool de escrita para implantar o código.
- **Escopo Mínimo de Acesso:** Acesso de **Leitura/Escrita** habilitado unicamente e de forma granular nos diretórios `novatech-assistant/src/`, `novatech-assistant/infra/`, `novatech-assistant/tests/` e configurações raiz (`package.json`, `tsconfig.json`). Acesso negado explicitamente a pastas como `node_modules`.
- **Justificativa:** O `server-filesystem` é a implementação oficial para interações I/O em disco. Isolar o escopo garante que o agente atue apenas onde o código-fonte deve nascer ou mudar, não deixando margem para alterações acidentais em dependências ou no host do desenvolvedor.

---

### 2. Documentação de negócios
- **Servidor MCP:** `@modelcontextprotocol/server-filesystem` (Segunda instância com escopo e regras diferentes)
- **Exposição:**
  - **Tools:** `read_file`, `search_files`.
  - **Resources:** Templates, definições ubíquas e ADRs expostos nativamente para o cliente do agente.
- **Consumo:** Antes de iniciar a implementação do código, o agente acessa passivamente estes artefatos para guiar sua modelagem, alinhando-se a SLAs, políticas (como procedimentos de frete) e decisões técnicas vigentes.
- **Escopo Mínimo de Acesso:** Apenas **Leitura (Read-Only)** e estritamente amarrado aos caminhos `novatech-assistant/docs/` e `novatech-assistant/specs/`.
- **Justificativa:** Separação rígida de papéis. Os documentos e requisitos representam a fonte da verdade da área de negócios e de arquitetura. O agente que auxilia no desenvolvimento de software não deve alterar regras de domínio a não ser com ferramentas de revisão específicas, necessitando ser read-only para proteção da integridade dos requisitos.

---

### 3. Chunks de dados para o RAG
- **Servidor MCP:** `@modelcontextprotocol/server-filesystem` (Para lidar com arquivos `*.md` estáticos neste momento)
- **Exposição:**
  - **Tools:** `read_file` e operações de parseamento locais.
  - **Resources:** O arquivo `file://../novatech-assistant/data/retrieval-corpus/chunks-novatech.md` mapeado diretamente.
- **Consumo:** O agente lê estruturas de simulação de corpus para verificar propriedades, checar a conversão de tabelas (problema listado na ADR-0004) e criar scripts de *Embeddings/Chunking* precisos em Typescript de acordo com os dados reais.
- **Escopo Mínimo de Acesso:** Leitura restrita à pasta `novatech-assistant/data/`.
- **Justificativa:** Segregação do dataset. Se a IA em testes acessasse livremente o disco, o RAG poderia acabar se contaminando ou indexando informações da documentação de projeto interna em vez da base de dados (chunks) que deverá ser servida aos usuários finais da NovaTech.

---

### 4. Histórico, branches e operações do Git
- **Servidor MCP:** `@modelcontextprotocol/server-git` (Padrão de gerência de código-fonte referenciado do protocolo)
- **Exposição:**
  - **Tools:** `git_status`, `git_log`, `git_diff`, `git_checkout`, `git_branch`, `git_commit`.
- **Consumo:** O agente lê as alterações vigentes (*diffs*), muda de *branch* associada ao que está sendo especificado no painel web interno, sugere/redige mensagens de commit baseadas estritamente nas mudanças da *staged area* e confere o status com frequência.
- **Escopo Mínimo de Acesso:** Execução travada às sub-rotinas seguras do programa `git`. CWD (Current Working Directory) delimitado para uso irrestritível apenas à raiz do projeto em `.git`.
- **Justificativa:** Expor um servidor de Bash/Shell global seria uma péssima decisão de segurança para um agente. Focar no server especializado para Git concede liberdade e versatilidade na gerência das versões, impedindo comandos destrutivos do sistema operacional, encapsulando puramente ações de SCM (Source Control Management).

---

### 5. Memória persistente (contexto contínuo)
- **Servidor MCP:** `@modelcontextprotocol/server-memory`
- **Exposição:**
  - **Tools:** Interação no grafo de conhecimento - `create_entities`, `create_relations`, `delete_entities`, `search_graph`.
- **Consumo:** O agente aprende dinamicamente as preferências arquiteturais do Tech Lead em TypeScript, que `AZURE_OPENAI` utiliza padrão de versão `2024-02-15-preview`, etc. Ele atualiza ou puxa esses nós e relações em background, sem precisar que o desenvolvedor repita isso.
- **Escopo Mínimo de Acesso:** Uma base de grafo/JSON encapsulada à parte e armazenada fora da esteira de builds do Node ou da infraestrutura (*gitignored* na raiz ou provisionada em escopo de usuário na home).
- **Justificativa:** Janelas de contexto perdem as memórias em cada reinício de sessão, e carregar os 800+ arquivos passados ou histórico de chat explodiria o limite imposto pela ADR-002 e budget de tokens da interface LLM local. Utilizar um Knowledge Graph via memory server é elegante, pois é acionado somente sob demanda semântica, resgatando apenas blocos específicos da "memória contínua" daquele RAG em implantação.
