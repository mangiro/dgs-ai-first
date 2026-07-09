# Evidência exercício 3.2 — Revisão crítica de código gerado por IA

## A revisão feita por humano de `/src/functions/feedback/handler.ts`

**Resultado:**
- [ex-3_2-human-code-review-handler.md](../docs/ex-3_2-human-code-review-handler.md)

## A revisão feita por IA de `/src/functions/feedback/handler.ts`

**Contexto adicionado a sessão:**
- [cenario-novatech.md](../docs/cenario-novatech.md)
- [AGENTS.md](../novatech-assistant/AGENTS.md)
- O código de `/src/functions/feedback/handler.ts` (pré ajustes):
    ```typescript
      import { app, HttpRequest, HttpResponseInit } from '@azure/functions';

      export async function feedbackHandler(
        request: HttpRequest
      ): Promise<HttpResponseInit> {
        const body = await request.json() as any;

        const feedback = {
          queryId: body.queryId,
          rating: body.rating,
          comment: body.comment,
          attendantEmail: body.attendantEmail,
          timestamp: new Date().toISOString()
        };

        console.log('Feedback recebido:', JSON.stringify(feedback));

        const { CosmosClient } = require('@azure/cosmos');
        const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING);
        const database = client.database('novatech');
        const container = database.container('feedbacks');

        await container.items.create(feedback);

        return { status: 200, body: 'OK' };
      }

      app.http('feedback', {
        methods: ['POST'],
        handler: feedbackHandler
      });
    ```

**Prompt utilizado:**
```
Atue como um Engenheiro de Software Sênior especializado em segurança, qualidade de código e conformidade de arquitetura.

Realize um code review aprofundado do arquivo `/src/functions/feedback/handler.ts`.

Suas tarefas específicas são:

1. **Analisar Conformidade:** Verifique o código contra as diretrizes estabelecidas no arquivo `AGENTS.md`.
2. **Auditoria de Segurança:** Identifique quaisquer vulnerabilidades e problemas de segurança.
3. **Detecção de Bugs:** Aponte erros de lógica, problemas de concorrência, exceções não tratadas ou desempenho ruim.
4. **Classificação:** Para cada problema encontrado, você DEVE atribuí-lo a uma das seguintes categorias exatas: `[Violação do AGENTS.md]`, `[Problema de Segurança]` ou `[Bug em Potencial]`.

Antes de iniciar a estruturação da resposta, faça uma análise silenciosa (ou use tags `<thinking>`) para consolidar suas observações.
```

**Resultado:**
- [ex-3_2-ai-code-review-handler.md](../docs/ex-3_2-ai-code-review-handler.md)

## A comparação entre a review humana e a review da IA

**Contexto adicionado a sessão:**
- [ex-3_2-human-code-review-handler.md](../docs/ex-3_2-human-code-review-handler.md)
- [ex-3_2-ai-code-review-handler.md](../docs/ex-3_2-ai-code-review-handler.md)

**Resultado:**
- [ex-3_2-analise-comparativa-code-reviews.md](../docs/ex-3_2-analise-comparativa-code-reviews.md)

## O código de `/src/functions/feedback/handler.ts` reescrito

**Contexto adicionado a sessão:**
- [ex-3_2-ai-code-review-handler.md](../docs/ex-3_2-ai-code-review-handler.md)
- [AGENTS.md](../novatech-assistant/AGENTS.md)

**Prompt utilizado:**
```
Reescreva o módulo `handler.ts` corrigindo os problemas apresentados no code review fornecido. O código final deve seguir o AGENTS.md
```

**Resultado:**
- [handler.ts](../novatech-assistant/src/functions/feedback/handler.ts)
- Retorno LLM: [rewrite-handlerts.png](./prints/rewrite-handlerts.png)
