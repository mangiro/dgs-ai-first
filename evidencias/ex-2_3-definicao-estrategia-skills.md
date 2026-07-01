# Evidência exercício 2.3 — Definição de estratégia de skills do projeto

## A árvore de skills

**Contexto adicionado a sessão:**
- [cenario-novatech.md](../docs/cenario-novatech.md)

**Prompt utilizado:**
```
Você é um Arquiteto de Software Especialista em IA, focado na criação de contexto e "Skill Trees" para agentes de codificação. Sua tarefa é analisar o contexto do nosso projeto e definir uma taxonomia completa de skills que guiará o comportamento da IA.

Siga rigorosamente a hierarquia de camadas abaixo, mapeando cada skill para seu respectivo diretório:

1. **Foundation (`/skills/foundation/`):** Convenções globais transversais.
   - *Exemplos esperados:* Tratamento de erros, logging, configuração de variáveis de ambiente, convenções de TypeScript.
2. **Domain (`/skills/domain/`):** Padrões arquiteturais por camada ou domínio técnico.
   - *Exemplos esperados:* Estrutura de endpoints, padrões de testes, organização de componentes React (arquitetura front-end).
3. **Artifact (`/skills/artifact/`):** Receitas de geração (playbooks) para criar peças específicas de código.
   - *Exemplos esperados:* Passos para criar um endpoint RAG, template para testes de integração.

**CONTEÚDO DE ENTRADA (Artefatos de Alta Repetição do Projeto):**
- Endpoints Azure Functions com padrão RAG (vários ao longo do projeto).
- Testes de integração para os endpoints.
- Componentes React para o painel web (cards de resposta, formulários de feedback).
- Documentação técnica de endpoints (ADRs, README de módulos).
- Specs de produto e tarefas (seguindo template Spec-Driven Development - SDD).

**FORMATO DE SAÍDA ESPERADO:**
Por favor, gere a árvore de skills em um formato de estrutura de diretórios (usando Markdown) seguido por uma tabela detalhando:
- **Caminho/Nome do Arquivo** (ex: `/skills/artifact/create-rag-endpoint.md`)
- **Propósito da Skill** (Qual problema ela resolve para o agente de IA)
- **Gatilhos (Triggers)** (Quando a IA deve utilizar esta skill)

Antes de gerar a resposta final, faça uma breve análise de raciocínio sobre como as necessidades repetitivas do projeto ditam a criação dessas skills.
```

**Resultado:**
- [ex-2_3-skills-taxonomy.md](../docs/ex-2_3-skills-taxonomy.md)

## O mapeamento de criação/consumo das skills

**Contexto adicionado a sessão:**
- [cenario-novatech.md](../docs/cenario-novatech.md)
- [ex-2_3-skills-taxonomy.md](../docs/ex-2_3-skills-taxonomy.md)

**Prompt utilizado:**
```
Você é um Arquiteto de Sistemas de IA especialista em design de agentes e governança de skills.

Sua tarefa é interpretar o documento de análise de taxonomia fornecido e extrair um mapeamento estruturado detalhando o ciclo de vida e a aplicação de cada skill identificada.

Para cada skill listada ou inferida na taxonomia, extraia as seguintes informações e apresente o resultado EXCLUSIVAMENTE em uma **tabela Markdown**:

1. **Nome da Skill:** Nome curto, padronizado e descritivo.
2. **Descrição / Frase de Ativação:** A declaração, intenção de usuário ou prompt exato que um agente reconheceria para disparar essa skill.
3. **Quem Cria:** Qual papel (desenvolvedor, engenheiro de prompt, especialista de domínio, etc.) é responsável por desenvolvê-la.
4. **Quem Consome:** Quais papéis humanos e específicos agentes de IA utilizarão essa skill.
5. **Frequência de Uso Estimada:** Ex: Alta (Diária), Média (Semanal), Baixa (Mensal ou sob demanda).
```

**Resultado:**
- [ex-2_3-skills-triggers.md](../docs/ex-2_3-skills-triggers.md)

## O SKILL.md Foundation

**Contexto adicionado a sessão:**
- [cenario-novatech.md](../docs/cenario-novatech.md)
- [ex-2_3-skills-taxonomy.md](../docs/ex-2_3-skills-taxonomy.md)
- [ex-2_3-skills-triggers.md](../docs/ex-2_3-skills-triggers.md)

**Prompt utilizado:**
```
Crie/preencha o SKILL.md da skill Foundation mais importante (a que será usada por todas as outras como base). O arquivo deve conter: contexto, regras prescritivas, exemplos concretos (FAÇA/NÃO FAÇA com código), e anti-padrões
```

**Resultado:**
- [foundation/typescript-conventions.md](../novatech-assistant/skills/foundation/typescript-conventions.md)
- Retorno LLM: [skill-md-creation.png](./prints/skill-md-creation.png)
