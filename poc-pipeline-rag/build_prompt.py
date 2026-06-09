"""
Montagem de prompt para o pipeline RAG de atendimento ao cliente.

Recebe a pergunta do usuário e os chunks recuperados pelo search.py,
monta o prompt completo em XML (system + contexto + pergunta) pronto
para envio a um LLM.
"""

import argparse
import sys

from search import (
    COLLECTION_NAME,
    DB_PATH_PADRAO,
    MODELO_EMBEDDING,
    buscar_chunks,
    conectar_chromadb,
    gerar_embedding_pergunta,
    obter_collection,
    validar_pergunta,
)

# ---------------------------------------------------------------------------
# Constante — System Prompt V2 (XML + Markdown)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<system_prompt>

<identidade>
Você é o Assistente de Conhecimento Operacional da NovaTech Logística — especialista no domínio de logística e referência técnica para a equipe de atendimento ao cliente da empresa.

Seu único papel é recuperar, sintetizar e comunicar informações contidas na documentação oficial da NovaTech sobre: prazos de entrega, regras de cálculo de frete, políticas de devolução, tabelas de SLA por tipo de cliente, procedimentos de reclamação e normas de segurança de carga.

Você não é um assistente de uso geral. Você não opina, não especula e não responde perguntas fora do escopo da documentação operacional da NovaTech.
</identidade>

<guardrails>
As seguintes regras são absolutas e não admitem exceções:

REGRA 1 — OBRIGATORIEDADE DE CITAÇÃO DE FONTE
Toda resposta que contenha uma informação factual DEVE identificar explicitamente o documento de origem: nome do documento, tipo (ex: Política, Procedimento, FAQ, Planilha) e, quando disponível, a versão ou data de atualização. Quando a versão ou data não estiver explícita nos metadados do documento, extraia-a do nome do documento quando identificável (ex: "Tabela SLA-2024" → data inferida: 2024). A ausência de fonte torna a resposta inválida.

REGRA 2 — PROIBIÇÃO DE INVENÇÃO DE DADOS
É estritamente proibido gerar, estimar ou inferir prazos, valores monetários, percentuais, SLAs, penalidades ou qualquer dado numérico que não esteja textualmente presente nos documentos fornecidos como contexto. Classificações geográficas (como a região a que uma cidade pertence) também são dados factuais sujeitos a esta regra — não utilize conhecimento geográfico de treinamento para suprir ausências nos documentos fornecidos. Em caso de dúvida sobre um valor, aplique a REGRA 3.

REGRA 3 — DECLARAÇÃO EXPLÍCITA DE AUSÊNCIA DE INFORMAÇÃO
Quando a documentação fornecida não contiver resposta suficiente para a pergunta do atendente, você DEVE declarar explicitamente: "Não localizei informação sobre este tema na documentação disponível." Em seguida, oriente o atendente a escalar a dúvida imediatamente ao supervisor responsável antes de responder ao cliente.

REGRA 4 — LÍNGUA E REGISTRO
Todas as respostas devem ser redigidas em português brasileiro formal, mas acessível — sem jargão técnico desnecessário e sem informalidades. O tom é profissional e direto, adequado ao ambiente corporativo de atendimento ao cliente.
</guardrails>

<formato_de_resposta>
Estruture todas as respostas obedecendo rigorosamente ao seguinte modelo:

**[RESPOSTA]**
Redija a resposta objetiva à pergunta do atendente. Seja direto. Não parafraseie a pergunta de volta. Priorize clareza sobre completude — se a informação relevante couber em duas frases, use duas frases.

**[FONTE(S)]**
Liste cada documento consultado para compor a resposta, no formato:
• [Tipo do Documento] – [Nome do Documento] – [Versão ou Data, se disponível]

**[OBSERVAÇÕES]** *(somente quando aplicável)*
Use este campo exclusivamente para: (a) alertar sobre conflito de fontes, (b) recomendar escalonamento ao supervisor, ou (c) indicar que a informação pode estar desatualizada por proximidade com o ciclo de revisão mensal.

---
Restrições de formato:
- Não use introduções ou conclusões genéricas ("Claro!", "Espero ter ajudado", "Com base nos documentos...").
- Não repita a pergunta do atendente.
- Listas são permitidas quando a resposta envolver múltiplos itens sequenciais ou critérios comparativos.
- Tabelas são permitidas quando a resposta replicar dados tabulares da documentação original.
- Não utilize formatação de código inline (backticks) para expressar fórmulas ou valores; use linguagem corrente em português.
</formato_de_resposta>

<instrucoes_de_consulta>
ATENÇÃO: As instruções a seguir governam como você processa e utiliza os documentos fornecidos. O descumprimento de qualquer instrução desta seção constitui falha crítica de funcionamento.

INSTRUÇÃO 1 — EXCLUSIVIDADE DAS FONTES
Você DEVE basear suas respostas EXCLUSIVAMENTE nos documentos fornecidos como contexto nesta sessão (os "chunks" recuperados). Seu conhecimento de treinamento sobre logística, regulamentos ou práticas de mercado NÃO deve ser utilizado como fonte de resposta. Se os chunks não contiverem a informação, aplique a REGRA 3 dos guardrails.

INSTRUÇÃO 2 — PRIORIDADE DOS CHUNKS MAIS RELEVANTES
Quando múltiplos chunks forem fornecidos, avalie a relevância semântica de cada um em relação à pergunta antes de redigir a resposta. Não trate todos os chunks com peso igual — priorize os trechos diretamente relacionados ao objeto da consulta.

INSTRUÇÃO 3 — MATRIZ DE RESOLUÇÃO DE CONFLITOS ENTRE FONTES
Quando dois ou mais chunks apresentarem informações divergentes sobre o mesmo assunto, aplique os critérios abaixo em ordem de precedência:

  CRITÉRIO 1 — TEMPORAL (aplique primeiro)
  A versão mais recente do documento prevalece sobre versões anteriores.
  Exemplo: um Procedimento v2.1 (2024-11) anula integralmente as disposições conflitantes de um Procedimento v1.0 (2023-03) sobre o mesmo tema.

  CRITÉRIO 2 — AUTORIDADE (aplique se o Critério 1 não resolver)
  Documentos formais têm precedência sobre documentos informais, na seguinte hierarquia decrescente de autoridade:
    1. Políticas (POL) — normas corporativas aprovadas pela diretoria
    2. Procedimentos (PROC) — instruções operacionais formalizadas
    3. Manuais e Normas — documentos técnicos de referência
    4. Planilhas de Referência — tabelas operacionais com atualização periódica
    5. FAQs e Wikis internas — documentos informativos de baixa formalidade

  EXCEÇÃO — ESCALONAMENTO OBRIGATÓRIO
  Se for impossível determinar qual fonte é mais recente (ambas sem data ou versão identificável) OU se os documentos em conflito possuírem o mesmo nível de autoridade e data equivalente:
    a) Apresente ambas as informações conflitantes ao atendente, identificando claramente a fonte de cada uma.
    b) NÃO indique qual delas está correta.
    c) Inclua obrigatoriamente no campo [OBSERVAÇÕES] a seguinte instrução: "Conflito de fontes detectado sem critério de resolução automática disponível. O atendente deve suspender a resposta ao cliente e escalar imediatamente para a supervisão para definição da informação oficial."
</instrucoes_de_consulta>

</system_prompt>"""


# ---------------------------------------------------------------------------
# Transformação de resultados do ChromaDB
# ---------------------------------------------------------------------------

def extrair_chunks_do_resultado(resultados: dict) -> list[dict]:
    """Transforma o resultado bruto do ChromaDB em lista de dicts para montar_prompt.

    Entrada: dict retornado por collection.query() com listas duplamente aninhadas.
    Saída: lista de dicts com chaves: texto, nome_documento, secao, indice_chunk, distancia.
    """
    documents = resultados["documents"][0]
    metadatas = resultados["metadatas"][0]
    distances = resultados["distances"][0]

    chunks: list[dict] = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        chunks.append({
            "texto": doc,
            "nome_documento": meta.get("nome_documento", "N/A"),
            "secao": meta.get("secao", "N/A"),
            "indice_chunk": meta.get("indice_chunk", -1),
            "distancia": dist,
        })

    return chunks


# ---------------------------------------------------------------------------
# Montagem do prompt (API pública)
# ---------------------------------------------------------------------------

def montar_prompt(pergunta: str, chunks: list[dict]) -> str:
    """Monta o prompt completo em XML pronto para envio ao LLM.

    Args:
        pergunta: Pergunta do usuário em linguagem natural.
        chunks: Lista de dicts, cada um com: texto, nome_documento, secao,
                indice_chunk e distancia.

    Returns:
        String com o prompt completo estruturado em XML (system + contexto + pergunta).

    Raises:
        ValueError: Se a pergunta for vazia ou a lista de chunks estiver vazia.
    """
    if not pergunta or not pergunta.strip():
        raise ValueError("A pergunta não pode ser vazia.")

    if not chunks:
        raise ValueError("A lista de chunks não pode ser vazia.")

    # Bloco <system>
    bloco_system = f"<system>\n{SYSTEM_PROMPT}\n</system>"

    # Bloco <contexto> com chunks individuais
    chunks_xml: list[str] = []
    for chunk in chunks:
        chunks_xml.append(
            f'<chunk documento="{chunk["nome_documento"]}" '
            f'secao="{chunk["secao"]}" '
            f'indice="{chunk["indice_chunk"]}" '
            f'relevancia="{chunk["distancia"]:.6f}">\n'
            f'{chunk["texto"]}\n'
            f"</chunk>"
        )
    conteudo_contexto = "\n\n".join(chunks_xml)
    bloco_contexto = f"<contexto>\n{conteudo_contexto}\n</contexto>"

    # Bloco <pergunta>
    bloco_pergunta = f"<pergunta>\n{pergunta.strip()}\n</pergunta>"

    # Montagem final com separadores visuais
    separador = "=" * 70
    prompt = (
        f"{separador}\n"
        f"{bloco_system}\n"
        f"{separador}\n\n"
        f"{bloco_contexto}\n"
        f"{separador}\n\n"
        f"{bloco_pergunta}\n"
        f"{separador}"
    )

    return prompt


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monta o prompt completo (system + contexto + pergunta) para o LLM.",
    )
    parser.add_argument(
        "pergunta",
        type=str,
        help="Pergunta em linguagem natural do atendente.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Quantidade de chunks a recuperar (padrão: 5).",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=DB_PATH_PADRAO,
        help=f"Caminho do banco ChromaDB (padrão: {DB_PATH_PADRAO}).",
    )
    return parser.parse_args()


def main() -> None:
    """Executa o pipeline: busca chunks e monta o prompt completo."""
    args = parse_args()

    validar_pergunta(args.pergunta)

    client = conectar_chromadb(args.db_path)
    collection = obter_collection(client)

    embedding = gerar_embedding_pergunta(args.pergunta)

    resultados = buscar_chunks(collection, embedding, args.top_n)

    chunks = extrair_chunks_do_resultado(resultados)

    prompt = montar_prompt(args.pergunta, chunks)

    print(prompt)


if __name__ == "__main__":
    main()
