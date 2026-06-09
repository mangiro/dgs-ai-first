"""
Pipeline de ingestão RAG para sistema de atendimento ao cliente.

Este script lê documentos Markdown, aplica chunking híbrido (por cabeçalhos + tamanho fixo),
gera embeddings com sentence-transformers e persiste os dados no ChromaDB.
"""

import logging
import re
import time
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fase 1 — Leitura de Documentos
# ---------------------------------------------------------------------------

def carregar_documentos(diretorio: str) -> list[dict]:
    """Lê todos os arquivos .md do diretório informado.

    Retorna lista de dicts com 'nome_arquivo' e 'conteudo'.
    Ignora arquivos vazios com warning.
    """
    caminho = Path(diretorio)

    if not caminho.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {diretorio}")

    arquivos_md = sorted(caminho.glob("*.md"))

    if not arquivos_md:
        raise FileNotFoundError(f"Nenhum arquivo .md encontrado em: {diretorio}")

    documentos: list[dict] = []
    for arquivo in arquivos_md:
        conteudo = arquivo.read_text(encoding="utf-8")
        if not conteudo.strip():
            logger.warning("Arquivo vazio ignorado: %s", arquivo.name)
            continue
        documentos.append({"nome_arquivo": arquivo.name, "conteudo": conteudo})
        logger.info("Documento carregado: %s (%d caracteres)", arquivo.name, len(conteudo))

    if not documentos:
        raise ValueError("Todos os arquivos .md encontrados estão vazios.")

    return documentos


# ---------------------------------------------------------------------------
# Fase 2 — Chunking Híbrido
# ---------------------------------------------------------------------------

# -------------------------------------------------------------------------
# JUSTIFICATIVA DA ESTRATÉGIA DE CHUNKING HÍBRIDO
# -------------------------------------------------------------------------
# Em sistemas de atendimento ao cliente, as perguntas dos usuários mapeiam
# naturalmente para SEÇÕES de documentos, não para blocos arbitrários de texto.
#
# Exemplos concretos deste projeto:
#   - "Qual a política de devolução?" → seção inteira do POL-001
#   - "Qual o SLA do cliente Gold?"   → tabela de tiers do SLA-2024
#   - "Como calcular frete especial?" → fórmula completa do PROC-042
#
# POR QUE NÃO usar chunking puramente por tamanho fixo?
#   1. CORTA TABELAS: uma tabela de SLA com 15 colunas seria dividida no meio,
#      gerando chunks sem sentido que não respondem a pergunta.
#   2. MISTURA CONTEXTOS: um chunk de 500 tokens pode conter o final de
#      "Exceções de Devolução" e o início de "Procedimento de Reembolso",
#      confundindo o retrieval.
#   3. PERDE HIERARQUIA: cabeçalhos markdown (##, ###) delimitam unidades
#      semânticas intencionais do autor do documento. Ignorá-los descarta
#      informação estrutural valiosa.
#
# A ESTRATÉGIA HÍBRIDA combina o melhor dos dois mundos:
#   - PRIMÁRIA: divisão por cabeçalhos preserva unidades semânticas completas.
#   - SECUNDÁRIA: subdivisão por tamanho fixo (500 tokens, overlap 50) é
#     aplicada APENAS em seções muito longas (ex: FAQ com 47 itens), evitando
#     chunks excessivamente grandes que diluem a relevância no embedding.
# -------------------------------------------------------------------------


def dividir_por_secoes(conteudo: str, nome_arquivo: str) -> list[dict]:
    """Divide o conteúdo de um documento em seções baseadas nos cabeçalhos markdown.

    Preserva a hierarquia: seções ## herdam o título do # pai,
    e seções ### herdam o título do ## pai.
    """
    linhas = conteudo.split("\n")
    secoes: list[dict] = []
    secao_atual_texto: list[str] = []
    hierarquia: dict[int, str] = {}  # nível -> título do cabeçalho
    secao_atual_titulo = "Introdução"

    padrao_cabecalho = re.compile(r"^(#{1,3})\s+(.+)$")

    for linha in linhas:
        match = padrao_cabecalho.match(linha)
        if match:
            # Salva a seção anterior se houver conteúdo
            texto_acumulado = "\n".join(secao_atual_texto).strip()
            if texto_acumulado:
                secoes.append({
                    "texto": texto_acumulado,
                    "secao": secao_atual_titulo,
                    "nome_documento": nome_arquivo,
                })

            nivel = len(match.group(1))
            titulo = match.group(2).strip()
            hierarquia[nivel] = titulo

            # Limpa níveis inferiores ao atual
            for n in list(hierarquia.keys()):
                if n > nivel:
                    del hierarquia[n]

            # Monta título hierárquico (ex: "Política > Exceções > Classe 1")
            titulos_ordenados = [hierarquia[n] for n in sorted(hierarquia.keys())]
            secao_atual_titulo = " > ".join(titulos_ordenados)
            secao_atual_texto = []
        else:
            secao_atual_texto.append(linha)

    # Salva a última seção
    texto_acumulado = "\n".join(secao_atual_texto).strip()
    if texto_acumulado:
        secoes.append({
            "texto": texto_acumulado,
            "secao": secao_atual_titulo,
            "nome_documento": nome_arquivo,
        })

    return secoes


def subdividir_secao(secao: dict, max_tokens: int = 500, overlap: int = 50) -> list[dict]:
    """Subdivide uma seção em chunks menores se exceder max_tokens.

    Usa len(texto.split()) como proxy de contagem de tokens —
    suficiente para POC sem dependência adicional de tokenizer.
    """
    palavras = secao["texto"].split()
    total_tokens = len(palavras)

    if total_tokens <= max_tokens:
        return [secao]

    chunks: list[dict] = []
    inicio = 0
    sub_indice = 0

    while inicio < total_tokens:
        fim = min(inicio + max_tokens, total_tokens)
        chunk_palavras = palavras[inicio:fim]
        chunk_texto = " ".join(chunk_palavras)

        chunks.append({
            "texto": chunk_texto,
            "secao": secao["secao"],
            "nome_documento": secao["nome_documento"],
            "sub_indice": sub_indice,
        })

        sub_indice += 1
        inicio += max_tokens - overlap

    return chunks


def processar_chunks(documentos: list[dict]) -> list[dict]:
    """Orquestra o chunking híbrido para todos os documentos.

    1. Divide cada documento por cabeçalhos markdown (chunking semântico).
    2. Subdivide seções longas (>500 tokens) com overlap (chunking por tamanho).
    3. Atribui índice global sequencial a cada chunk.
    """
    todos_chunks: list[dict] = []
    indice_global = 0

    for doc in documentos:
        secoes = dividir_por_secoes(doc["conteudo"], doc["nome_arquivo"])

        for secao in secoes:
            sub_chunks = subdividir_secao(secao)

            for chunk in sub_chunks:
                chunk["indice_chunk"] = indice_global
                chunk["documento_completo"] = doc["nome_arquivo"]
                # Remove campo auxiliar de sub-índice se presente
                chunk.pop("sub_indice", None)
                todos_chunks.append(chunk)
                indice_global += 1

    logger.info("Total de chunks gerados: %d", len(todos_chunks))
    return todos_chunks


# ---------------------------------------------------------------------------
# Fase 3 — Geração de Embeddings
# ---------------------------------------------------------------------------

def gerar_embeddings(chunks: list[dict], modelo_nome: str = "all-MiniLM-L6-v2") -> list[dict]:
    """Gera embeddings para cada chunk usando sentence-transformers.

    Processa em batch para eficiência.
    """
    logger.info("Carregando modelo de embeddings: %s", modelo_nome)
    try:
        modelo = SentenceTransformer(modelo_nome)
    except Exception as e:
        raise RuntimeError(f"Falha ao carregar modelo '{modelo_nome}': {e}") from e

    textos = [chunk["texto"] for chunk in chunks]
    logger.info("Gerando embeddings para %d chunks...", len(textos))
    embeddings = modelo.encode(textos, show_progress_bar=True)

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()

    logger.info("Embeddings gerados com sucesso (dimensão: %d)", len(chunks[0]["embedding"]))
    return chunks


# ---------------------------------------------------------------------------
# Fase 4 — Persistência no ChromaDB
# ---------------------------------------------------------------------------

def persistir_no_chromadb(chunks: list[dict], diretorio_db: str = "./chroma_db") -> None:
    """Persiste os chunks com embeddings e metadados no ChromaDB.

    Usa IDs determinísticos para permitir re-execução idempotente.
    """
    logger.info("Conectando ao ChromaDB em: %s", diretorio_db)
    client = chromadb.PersistentClient(path=diretorio_db)
    collection = client.get_or_create_collection(name="atendimento_cliente")

    ids: list[str] = []
    documents: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict] = []

    for chunk in chunks:
        chunk_id = f"{chunk['nome_documento']}_{chunk['indice_chunk']}"
        ids.append(chunk_id)
        documents.append(chunk["texto"])
        embeddings.append(chunk["embedding"])
        metadatas.append({
            "nome_documento": chunk["nome_documento"],
            "secao": chunk["secao"],
            "indice_chunk": chunk["indice_chunk"],
            "documento_completo": chunk["documento_completo"],
        })

    # Upsert para idempotência — re-executar o script atualiza em vez de duplicar
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info("Persistidos %d chunks na collection '%s'", len(ids), collection.name)


# ---------------------------------------------------------------------------
# Fase 5 — Orquestração e Resumo
# ---------------------------------------------------------------------------

def main() -> None:
    """Executa o pipeline completo de ingestão RAG."""
    inicio = time.perf_counter()

    diretorio_docs = Path(__file__).parent / "docs"

    # Fase 1 — Leitura
    documentos = carregar_documentos(str(diretorio_docs))

    # Fase 2 — Chunking
    chunks = processar_chunks(documentos)

    # Fase 3 — Embeddings
    chunks = gerar_embeddings(chunks)

    # Fase 4 — Persistência
    persistir_no_chromadb(chunks)

    # Resumo
    tempo_total = time.perf_counter() - inicio
    print("\n" + "=" * 60)
    print("RESUMO DA INGESTÃO")
    print("=" * 60)
    print(f"  Documentos processados:  {len(documentos)}")
    print(f"  Chunks gerados:          {len(chunks)}")
    print(f"  Tempo de execução:       {tempo_total:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
