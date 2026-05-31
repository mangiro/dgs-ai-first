# Evidência exercício 1.1 — Análise de viabilidade técnica com fundamentos de LLM e engenharia de contexto

## Iteração 1

**Contexto adicionado a sessão:**
> Disponível em [cenario-novatech.md](../docs/cenario-novatech.md)

**Prompt utilizado:**
```
Atue como um arquiteto de RAG sênior e produza uma análise técnica objetiva, para planejamento de ingestão e retrieval.

Contexto:

	- Fontes de dados:
		1. PDFs com tabelas
		2. PDFs escaneados
		3. Wiki com links internos
		4. Planilhas com fórmulas

	- Volume estimado:
		- ~800 PDFs, média de 10 páginas por PDF
		- ~400 páginas wiki, média de 1.500 palavras por página
		- ~50 planilhas

	- Regra prática de conversão: 0,75 palavras por token
	- Orçamento de contexto:
		- Janela do GPT-4o: 128.000 tokens
		- Prompt de sistema + instruções: ~2.000 tokens
		- Chunk alvo: ~500 tokens

Tarefa:

	1. Para cada tipo de fonte (os 4 acima), explique:
		- principal desafio para pipeline de RAG,
		- impacto esperado na qualidade das respostas,
		- estratégia de tratamento recomendada (ingestão, parsing, chunking, metadata, retrieval e validação).

	2. Estime o tamanho da base em tokens:
		- Mostre contas passo a passo em tabela.
		- Quando faltar dado explícito (ex.: palavras por página em PDF e planilha), declare premissas razoáveis e forneça faixa mínima–máxima + valor central.

	3. Faça análise de orçamento de contexto:
		- Calcule quantos chunks de ~500 tokens cabem por query após descontar 2.000 tokens fixos.
		- Considere também overhead de instruções de usuário, histórico e citações (explique com cenário realista).
		- Conclua o número “teórico” e o “prático” de chunks por consulta.

	4. Recomende estratégia de chunking:
		- Justifique pelo tipo de pergunta de negócio esperado (perguntas factuais, comparativas, procedimentais e de síntese).
		- Explique como mitigar o efeito lost in the middle.
		- Inclua recomendações de:
			- tamanho de chunk,
			- overlap,
			- chunking semântico vs estrutural,
			- reranking e número de documentos recuperados (top-k),
			- when-to-use parent-child retrieval / summary index.

Formato de saída obrigatório:

	- Seções numeradas.
	- Pelo menos 2 tabelas:
		- Tabela A: desafios/impactos/estratégias por tipo de fonte.
		- Tabela B: estimativas de tokens e contas.
	- Lista final com “Recomendações acionáveis (próximos 30 dias)” em até 10 itens priorizados.
	- Seja técnico, claro e direto. Evite generalidades.
```

**Resultado:**
> Disponível em [ex-1_1-analise-rag-novatech.md](../docs/ex-1_1-analise-rag-novatech.md)

## Iteração 2

**Contexto adicionado a sessão:**
> Disponível em [ex-1_1-analise-rag-novatech.md](../docs/ex-1_1-analise-rag-novatech.md)

**Prompt utilizado:**
```
Revise a análise: identifique pontos fracos, estimativas otimistas demais ou riscos que não foram considerados
```

**Resultado:**
> Disponível em [ex-1_1-revisao-critica-rag-novatech.md](../docs/ex-1_1-revisao-critica-rag-novatech.md)

## Iteração 3

**Contexto adicionado a sessão:**
> Disponível em [ex-1_1-analise-rag-novatech.md](../docs/ex-1_1-analise-rag-novatech.md) e [ex-1_1-revisao-critica-rag-novatech.md](../docs/ex-1_1-revisao-critica-rag-novatech.md)

**Prompt utilizado:**
```
Contemple a análise inicial e a revisão crítica em um novo documento como sendo a análise final
```

**Resultado:**
> Disponível em [ex-1_1-analise-final-rag-novatech.md](../docs/ex-1_1-analise-final-rag-novatech.md)

> A estrutura integra as duas análises da seguinte forma:
>	- Seção 1 — mantém a Tabela A original, mas corrige a recomendação do openpyxl (substituído por xlwings/M365 API) e adiciona duas subseções com as estratégias faltantes: política concreta para links Confluence não resolvidos e pipeline de detecção de fluxogramas em imagens
>	- Seção 2 — preserva a Tabela B e as premissas, mas adiciona uma coluna de risco por premissa, destaca P6 (10 páginas/PDF) como a mais frágil, e acrescenta a estimativa de custo de embedding que estava ausente
>	- Seção 3 — mantém o orçamento de contexto e adiciona a Seção 3.4 com o breakdown de latência end-to-end e as alavancas de otimização
>	- Seção 4 — preserva toda a estratégia de chunking, adiciona o limite de 4 parents simultâneos para evitar explosão de contexto, e acrescenta a Seção 4.7 com avaliação de modelos de embedding para português brasileiro
>	- Seção 5 (nova) — consolida todos os riscos sistêmicos ausentes: LGPD, controle de acesso por perfil, conflito entre versões com mecanismo de soft delete confiável, e extensão do grounding check para entidades textuais
>	- Seção 6 — plano de 30 dias expandido de 10 para 14 ações, com a antecipação do procurement Azure na Semana 1 e os thresholds de aceitação definidos antes das avaliações
>	- Seção 7 — tabela de rastreabilidade mapeando cada gap da revisão crítica para a seção onde foi resolvido
