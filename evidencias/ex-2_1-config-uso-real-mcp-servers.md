# Evidência exercício 2.1 — Configuração e uso real de MCP servers no projeto

## Mapeamento de necessidades do projeto para reference servers

**Contexto adicionado a sessão:**
- [cenario-novatech.md](../docs/cenario-novatech.md)

**Prompt utilizado:**
```
Atue como um Arquiteto de Sistemas Sênior, especialista em Model Context Protocol (MCP) e design de Agentes de IA.

Estou desenvolvendo um projeto TypeScript em `novatech-assistant/` que implementa RAG no Azure e estou configurando o ambiente local dos meus agentes de IA. Eles precisam de acesso aos seguintes contextos e sistemas:

1. Código-fonte do projeto.
2. Documentação de negócios em `novatech-assistant/docs/novatech/`.
3. Chunks de dados para o RAG em `novatech-assistant/data/retrieval-corpus/`.
4. Histórico, branches e operações do Git.
5. Memória persistente (contexto contínuo entre sessões).

Sua Tarefa:
Mapeie cada uma das 5 necessidades acima para os *MPC reference servers* **locais** mais adequados.

Para cada necessidade, forneça uma análise estruturada contendo obrigatoriamente as seguintes informações:

- Servidor MCP: (O nome do servidor, ex: @modelcontextprotocol/server-filesystem)
- Exposição: (Liste exatamente quais tools, resources ou prompts o servidor irá expor para o modelo)
- Consumo: (Como o agente interage com ele na prática)
- Escopo Mínimo de Acesso: (Diretórios exatos, variáveis de ambiente ou políticas de restrição necessárias por motivos de segurança)
- Justificativa: (Por que esta é a melhor escolha técnica e de segurança para este requisito específico)

Apresente esta análise em um arquivo markdown utilizando um formato limpo, separando cada necessidade em tópicos claros ou em uma tabela de arquitetura.
```

**Resultado:**
- [mcp-architecture.md](../docs/mcp-architecture.md)

## Configuração dos MCPs com base no mapeamento

**Contexto adicionado a sessão:**
- [cenario-novatech.md](../docs/cenario-novatech.md)
- [mcp-architecture.md](../docs/mcp-architecture.md)
- [mcp.example.json](../novatech-assistant/.mcp/mcp.example.json)

**Prompt utilizado:**
```
Atue como um Especialista em Segurança e Arquiteto de Software. Sua tarefa é interpretar a análise fornecida `mcp-architecture.md` e preencher o arquivo de configuração `.mcp/mcp.json`.

Diretrizes Essenciais:

1. **Princípio do Menor Privilégio (Least Privilege):** Este é o requisito fundamental absoluto. Atribua estritamente apenas os escopos e acessos necessários para cada servidor, nada além disso.
2. **Separação de Escopos (Leitura vs. Escrita):** Traduza os mapeamentos de escopo da arquitetura fielmente. Para aplicar limites rigorosos entre permissões read-only e read-write, adote uma destas abordagens no JSON:
    - Crie instâncias separadas e distintas do mesmo servidor.
    - Utilize as restrições e flags de permissão específicas que o servidor suporta nativamente.
3. **Validação:** Garanta que cada servidor mapeado não tenha acessos implícitos ou permissões excessivas.
```

**Resultado:**
- [mcp.json](../novatech-assistant/.mcp/mcp.json)

## Execução e uso dos MCPs

**Resultado:**
- Servers ativos: [mcp-servers-up.png](./prints/mcp-servers-up.png)
- Listar e ler um documento de `docs/novatech/`: [mcp-filesystem-docs.png](./prints/mcp-filesystem-docs.png)
- Recuperar um chunk relevante de `data/retrieval-corpus/`: [mcp-filesystem-data.png](./prints/mcp-filesystem-data.png)
- Ler o histórico do repositório via `git`: [mcp-git.png](./prints/mcp-git.png)

## Análise de riscos no uso dos MCPs

**Contexto adicionado a sessão:**
- [mcp-architecture.md](../docs/mcp-architecture.md)
- [mcp.json](../novatech-assistant/.mcp/mcp.json)

**Prompt utilizado:**
```
Atue como um Engenheiro de Segurança de IA especializado no Model Context Protocol (MCP). Analise o ambiente de desenvolvimento local atual em `novatech-assistant/` e identifique pelo menos 2 riscos de segurança críticos introduzidos pelo uso de servidores MCP.

Para a sua análise, tome como base cenários comuns (como um servidor filesystem com escopo excessivo que pode expor arquivos .env, ou um servidor com privilégios de escrita que permite alterações diretas no código sem revisão humana).

Apresente sua resposta na seguinte estrutura para cada risco:

- **Nome do Risco:** [Nome claro da vulnerabilidade]
- **Vetor de Ameaça:** [Como o agente ou um invasor poderia explorar essa brecha no ambiente local]
- **Impacto Potencial:** [O que pode dar errado se explorado]
- **Plano de Mitigação:** [Ações técnicas, de configuração ou arquiteturais para isolar e resolver o problema]
```

**Resultado:**
- [mcp-security-analysis.md](../docs/mcp-security-analysis.md)
