# Evidência exercício 1.2 — Prototipação de prompt com engenharia de contexto

## Criação do System Prompt V1

**Contexto adicionado a sessão:**
> Disponível em [cenario-novatech.md](../docs/cenario-novatech.md) e [prototipacao-de-prompt-engenharia-de-contexto.md](../docs/prototipacao-de-prompt-engenharia-de-contexto.md)

**Prompt utilizado:**
```
Atue como um Especialista em Engenharia de Prompts. Sua tarefa é redigir um System Prompt rigoroso e altamente estruturado para um novo assistente de IA. Não utilize aberturas genéricas como "você é um assistente útil".

Estruture o System Prompt gerado em seções claras (preferencialmente utilizando tags XML como `<identidade>`, `<guardrails>`, etc.) contemplando obrigatoriamente os seguintes elementos:

	1. Identidade e Escopo: Defina claramente o papel do assistente, indicando que ele trabalha para a NovaTech e é um especialista no domínio de Logística.
	2. Regras e Guardrails: Liste de forma imperativa os 4 guardrails de segurança e escopo definidos pelo Product Specialist.
	3. Formato de Resposta: Estabeleça a estrutura e o tom exatos que o assistente deve adotar ao responder ao usuário final.
	4. Instruções Estritas de Consulta (Chunks): Crie uma seção de comandos diretos informando que o assistente deve basear suas respostas EXCLUSIVAMENTE nos documentos fornecidos como contexto (chunks).
		Inclua a seguinte matriz de resolução de conflitos para fontes divergentes:
			- Critério 1 (Temporal): A versão mais recente sempre prevalece (ex: v2 anula v1).
			- Critério 2 (Autoridade): Documentos formais (como Políticas - POL e Procedimentos - PROC) têm precedência sobre documentos informais (como FAQs).
			- Exceção/Escalonamento: Caso seja impossível determinar a versão mais recente ou o nível de autoridade, instrua o assistente a apresentar ambas as informações, citar claramente a fonte de cada uma e orientar o atendente a escalar a dúvida imediatamente para a supervisão.
```

**Resultado:**
> Disponível em [ex-1_2-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-system-prompt-v1.md)

## Análise da Estrutura de Contexto do System Prompt V1

**Contexto adicionado a sessão:**
> Disponível em [ex-1_2-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-system-prompt-v1.md) e [ex-1_1-analise-final-rag-novatech.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_1-analise-final-rag-novatech.md)

**Prompt utilizado:**
```
Atue como um Engenheiro de Prompt Sênior e especialista em arquitetura de contexto de LLMs.

Sua tarefa é documentar e dissecar a estrutura de contexto de um System Prompt fornecido. Siga os passos abaixo rigorosamente:

	1. **Decomposição:** Quebre o System Prompt em seus blocos lógicos estruturais (ex: Definição de Papel, Diretrizes, Regras de Formatação, Variáveis).
	2. **Classificação de Estabilidade:** Classifique cada bloco como:
		- **[ESTÁTICO]:** Parte central do prompt que deve ser enviada inalterada em todas as queries.
		- **[DINÂMICO]:** Componentes variáveis (ex: histórico de chat, dados do usuário, RAG) que mudam a cada nova query.
	3. Estimativa de Tokens: Calcule o tamanho estimado em tokens de cada parte.

**Formato de Saída Exigido:**

	- Uma Tabela Markdown contendo as colunas: Componente/Bloco, Tipo (Estático/Dinâmico), Descrição Resumida e Tokens Estimados.
	- Um cálculo final indicando o Custo de Contexto Fixo (Total de tokens estáticos) versus a Média de Contexto Variável.
```

**Resultado:**
> Disponível em [ex-1_2-analise-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-analise-system-prompt-v1.md)

## Teste System Prompt V1

**Contexto adicionado a sessão:**
> Disponível em [ex-1_2-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-system-prompt-v1.md) e [ex-1_2-chunks-simulados.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-chunks-simulados.md)

**Resultado:**
> Disponível em [ex-1_2-teste-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-teste-system-prompt-v1.md)

## Análise crítica do resultado do teste do System Prompt V1

**Contexto adicionado a sessão:**
> Disponível em [ex-1_2-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-system-prompt-v1.md) e [ex-1_2-teste-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-teste-system-prompt-v1.md)

**Prompt utilizado:**
```
Você atuará como um Analista de Qualidade de Modelos de IA (QA), analisando o teste do "System Prompt V1". Sua tarefa é analisar criticamente cada resposta gerada pelo modelo e avaliar os seguintes critérios:

1. **Está factualmente correta?** - A pegadinha principal: carga perigosa (classes 1-6 ANTT) é exceção à política de devolução. A resposta correta é que não pode devolver. Se o modelo disse que pode, é uma falha.
2. **Citou a fonte?** - O modelo referenciou corretamente o documento e a seção que embasam sua resposta (ex: "Conforme POL-001, seção 3.2...")?
3. **Respeitou os guardrails?** - A linguagem está em português formal? Houve alguma invenção (alucinação) de valores, cláusulas ou procedimentos que não constam na política original?
4. **Onde errou e por quê?** Para cada erro encontrado, explique onde e por que o modelo falhou. Documente a causa provável (ex: "O modelo ignorou a cláusula de exceção; o System Prompt não enfatizou suficientemente que exceções devem ser tratadas primeiro").

Formato de Saída Exigido (Para cada Pergunta/Resposta):

[Número ou Tema da Pergunta]
- Correção Factual: [Passou / Falhou] – [Breve justificativa baseada na regra]
- Citação de Fonte: [Passou / Falhou] – [A citação feita ou a indicação de falta]
- Guardrails: [Passou / Falhou] – [Comentário sobre tom formal e ausência de alucinações]
- Diagnóstico do Erro: [Explicação da falha e hipótese de melhoria para o System Prompt - preencher apenas se houver falha]
```

**Resultado:**
> Disponível em [ex-1_2-qa-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-qa-system-prompt-v1.md)

## Criação do System Prompt V2

**Contexto adicionado a sessão:**
> Disponível em [ex-1_2-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-system-prompt-v1.md), [ex-1_2-teste-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-teste-system-prompt-v1.md) e [ex-1_2-qa-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-qa-system-prompt-v1.md)

**Prompt utilizado:**
```
Atue como um Engenheiro de Prompt Sênior. Sua tarefa é gerar o System Prompt V2.

O V2 deve ser baseado integralmente no System Prompt V1 e incorporar apenas as melhorias identificadas na análise de QA do teste, sem alterar nenhuma outra parte do prompt.

Regras para geração:

- Mantenha a estrutura XML original (<identidade>, <guardrails>, <formato_de_resposta>, <instrucoes_de_consulta>) inalterada, exceto nos pontos de melhoria.
- Não reescreva, reformule nem otimize nenhuma parte além do especificado.
- Entregue o prompt completo (não apenas os trechos modificados), de forma que o V2 seja autossuficiente.
```

**Resultado:**
> Disponível em [ex-1_2-system-prompt-v2.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-system-prompt-v2.md)

## Teste System Prompt V2

**Contexto adicionado a sessão:**
> Disponível em [ex-1_2-system-prompt-v2.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-system-prompt-v2.md) e [ex-1_2-chunks-simulados.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-chunks-simulados.md)

**Resultado:**
> Disponível em [ex-1_2-teste-system-prompt-v2.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-teste-system-prompt-v2.md)

## Análise Comparativa — System Prompt V1 × V2

**Contexto adicionado a sessão:**
> Disponível em [ex-1_2-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-system-prompt-v1.md), [ex-1_2-system-prompt-v2.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-system-prompt-v2.md), [ex-1_2-teste-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-teste-system-prompt-v1.md), [ex-1_2-qa-system-prompt-v1.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-qa-system-prompt-v1.md) e [ex-1_2-teste-system-prompt-v2.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-teste-system-prompt-v2.md)

**Prompt utilizado:**
```
Você é um avaliador especialista em qualidade de sistemas RAG e design de prompts de IA. Realize uma análise comparativa estruturada entre os testes e o QA do System Prompt V1 e o teste do System Prompt V2, respondendo objetivamente às seguintes questões:

1. As respostas melhoraram do V1 para o V2?
Para cada pergunta, compare:

	- Qualidade e precisão da resposta
	- Aderência ao formato exigido ([RESPOSTA], [FONTE(S)], [OBSERVAÇÕES])
	- Tratamento de lacunas informacionais
	- Clareza das instruções de escalonamento ao supervisor

2. As falhas identificadas no QA do V1 foram corrigidas no V2?

3. O V2 introduziu novas falhas ou regressões?
Identifique qualquer deterioração em relação ao V1, incluindo respostas que ficaram menos objetivas, mais prolixas ou menos precisas.

Formato esperado: Tabela comparativa por pergunta + parecer final indicando se o V2 representa uma evolução efetiva sobre o V1.
```

**Resultado:**
> Disponível em [ex-1_2-analise-comparativa-v1-v2.md](../.spec/ex-1_2-engenharia-de-contexto/ex-1_2-analise-comparativa-v1-v2.md)
