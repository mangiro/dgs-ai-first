# [TESTE] Perguntas e respostas — System Prompt V1

## Inicialização

**Contexto adicionado:**
> Disponível em [ex-1_2-chunks-simulados.md](../docs/ex-1_2-chunks-simulados.md)

**Mensagem de início:**
> Contexto carregado. Estou operando como Assistente de Conhecimento Operacional da NovaTech Logística com base nos seguintes chunks disponíveis:
>
> - Chunk A — Política de Devolução POL-001, seção 3.2
> - Chunk B — Tabela SLA-2024 por categoria de cliente
> - Chunk C — PROC-042-v2, seção 2 — Cálculo de frete especial por região
>
> Aguardando a consulta do atendente.

### Pergunta 1

P:
> Qual o prazo de devolução para carga perigosa?

R:
> [RESPOSTA]<br>Cargas classificadas como perigosas (classes 1 a 6 da ANTT) são exceção expressa à política de devolução da NovaTech — ou seja, não são elegíveis para devolução.
>
> [FONTE(S)]<br>• Política – Política de Devolução POL-001 – seção 3.2

### Pergunta 2

P:
> Meu cliente é Gold, qual o SLA de resolução?

R:
> [RESPOSTA]<br>Para clientes Gold, o SLA de resolução é de até 24 horas, com tempo de resposta inicial de até 2 horas.
>
> [FONTE(S)]<br>• Planilha de Referência – Tabela SLA-2024

### Pergunta 3

P:
> Quanto custa o frete para 600kg para Manaus?

R:
> [RESPOSTA]<br>Manaus está na Região Norte. Para a carga de 600 kg (acima do limite de 500 kg que aciona o frete especial), aplica-se o multiplicador regional de 1,8 sobre o valor base: `valor base × 1,8`.<br>Não localizei o valor base de frete na documentação disponível. O atendente deve escalar a consulta ao supervisor responsável para obter esse valor antes de informar o custo final ao cliente.
>
> [FONTE(S)]<br>• Procedimento – PROC-042-v2 – seção 2
