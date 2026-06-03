# [TESTE] Perguntas e respostas — System Prompt V2

## Inicialização

**Contexto adicionado:**
> Disponível em [ex-1_2-chunks-simulados.md](../docs/ex-1_2-chunks-simulados.md)

**Mensagem de início:**
> Contexto carregado. Estou operando como o Assistente de Conhecimento Operacional da NovaTech Logística, com base exclusivamente nos seguintes documentos disponíveis nesta sessão:
>
> - Política POL-001 (seção 3.2) — Política de Devolução
> - Tabela SLA-2024 — SLAs por categoria de cliente
> - Procedimento PROC-042-v2 (seção 2) — Frete especial para cargas acima de 500 kg
>
> Pode encaminhar a consulta do atendente.

### Pergunta 1

P:
> Qual o prazo de devolução para carga perigosa?

R:
> [RESPOSTA]<br>Cargas classificadas como perigosas (classes 1 a 6 da ANTT) são expressamente excluídas da política de devolução. Não há prazo de devolução aplicável a esse tipo de carga.
>
> [FONTE(S)]<br>• Política – POL-001 – seção 3.2
>
> [OBSERVAÇÕES]<br>Caso o cliente solicite devolução de carga perigosa, o atendente deve suspender a tratativa e escalar imediatamente ao supervisor, pois a situação não está coberta pela política vigente.

### Pergunta 2

P:
> Meu cliente é Gold, qual o SLA de resolução?

R:
> [RESPOSTA]<br>Para clientes Gold, o SLA de resolução é de até 24 horas, com resposta inicial em até 2 horas.
>
> [FONTE(S)]<br>• Planilha de Referência – Tabela SLA-2024

### Pergunta 3

P:
> Quanto custa o frete para 600kg para Manaus?

R:
> [RESPOSTA]<br>A carga de 600kg se enquadra na regra de frete especial (acima de 500kg), com valor calculado pela fórmula: valor base × multiplicador regional.<br>No entanto, não é possível concluir o cálculo por duas razões:
> 1. A documentação disponível não mapeia cidades às suas respectivas regiões — portanto, não é possível confirmar a qual região Manaus pertence com base nos documentos fornecidos.
> 2. O valor base do frete não consta nos documentos disponíveis.
>
> Não localizei informação sobre estes dados na documentação disponível.
>
> [FONTE(S)]<br>• Procedimento – PROC-042-v2 – seção 2
>
> [OBSERVAÇÕES]<br>O atendente deve suspender a resposta ao cliente e escalar imediatamente ao supervisor para obter o valor base do frete e a classificação regional oficial de Manaus antes de prosseguir.
