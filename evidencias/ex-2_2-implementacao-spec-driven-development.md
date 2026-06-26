# Evidência exercício 2.2 — Implementação de spec com Spec Driven Development

## O `tasks.md` com tasks atômicas

**Contexto adicionado a sessão:**
- [cenario-novatech.md](../docs/cenario-novatech.md)
- [query-endpoint/plan.md](../novatech-assistant/specs/query-endpoint/plan.md)

**Prompt utilizado:**
```
Você é um Desenvolvedor Sênior e Especialista em TypeScript, focado em metodologias ágeis. Sua missão é atuar como um engenheiro de decomposição de tarefas, analisando um documento de planejamento técnico e quebrando-o em um cronograma de tarefas de desenvolvimento viáveis e atômicas.

Analise o documento de planejamento fornecido e gere um arquivo `/query-endpoint/tasks.md` estruturado.

Diretrizes rigorosas para a geração das tarefas:
1. Granularidade: As tarefas devem ser "atômicas" (o menor incremento de valor possível que pode ser desenvolvido, testado e feito o merge de forma isolada no ecossistema TypeScript).
2. Formato Obrigatório (para cada tarefa, use sintaxe Markdown limpa):
   - **ID:** Identificador único sequencial (ex: TSK-001, TSK-002).
   - **Descrição:** Descrição técnica clara, orientada à ação, de preferência indicando as mudanças nos arquivos TS/configurações.
   - **Critérios de Aceite:** Lista de verificação (bullet points) para garantir que a tarefa cumpre seu propósito e passa em testes.
   - **Dependências:** IDs das tarefas que devem ser estritamente concluídas antes do início desta (ou "Nenhuma").
   - **Estimativa:** Esforço e complexidade usando a escala (P = Pequena, M = Média, G = Grande).

Primeiro faça um breve resumo da arquitetura ou do plano identificado para garantir o alinhamento, e em seguida, apresente as tarefas estruturadas.
```

**Resultado:**
- [query-endpoint/tasks.md](../novatech-assistant/specs/query-endpoint/tasks.md)
- Retorno LLM: [generate-tasks-md.png](./prints/generate-tasks-md.png)

## Implementar primeiras tasks independentes em paralelo

**Contexto adicionado a sessão:**
- [query-endpoint/plan.md](../novatech-assistant/specs/query-endpoint/plan.md)
- [query-endpoint/tasks.md](../novatech-assistant/specs/query-endpoint/tasks.md)

**Prompt utilizado:**
```
Implemente as tasks de 1 a 4 em paralelo, visto que elas não possuem dependência entre si. — O código deve seguir os padrões definidos
```

**Resultado:**
- [types.ts](../novatech-assistant/src/shared/types.ts)
- [config.ts](../novatech-assistant/src/shared/config.ts)
- [logger.ts](../novatech-assistant/src/shared/logger.ts)
- [errors.ts](../novatech-assistant/src/shared/errors.ts)
- Retorno LLM: [tasks-implementation.png](./prints/tasks-implementation.png)

## Implementar task 5 com validador Zod

**Resultado:**
- [validator.ts](../novatech-assistant/src/functions/query/validator.ts)
- Retorno LLM: [task5-implementation.png](./prints/task5-implementation.png)

## Análise crítica antes do code review

**Contexto adicionado a sessão:**
- [query-endpoint/plan.md](../novatech-assistant/specs/query-endpoint/plan.md)
- [query-endpoint/tasks.md](../novatech-assistant/specs/query-endpoint/tasks.md)

**Prompt utilizado:**
```
Atue como um Engenheiro de Software Sênior e Especialista em TypeScript/Node.js. Sua tarefa é realizar uma revisão crítica de código (pré-code review) na base de código do diretório `src/` e no arquivo `package.json`.

Analise o código buscando problemas de arquitetura, más práticas, falhas de segurança, tipagem inadequada (TypeScript) ou configurações incorretas/ausentes de dependências e scripts.

Com base na sua análise, identifique **pelo menos 2 pontos críticos** que precisariam de ajuste imediato antes de passar por um code review real.

Para cada ponto identificado, estruture sua resposta da seguinte forma:

1. **Problema:** Resumo claro do que está errado ou pode ser melhorado.
2. **Localização:** Arquivos afetados (incluindo o package.json, se aplicável).
3. **Impacto:** Por que isso é um problema (ex: performance, segurança, manutenção).
4. **Solução Proposta:** Como corrigir o problema (inclua recortes de código ou ajustes reais no json/ts).
```

**Resultado:**
- [ex-2_2-analise-critica-pre-code-review.md](../docs/ex-2_2-analise-critica-pre-code-review.md)
