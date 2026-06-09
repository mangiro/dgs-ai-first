"""
Busca semântica no pipeline RAG de atendimento ao cliente.

Recebe uma pergunta em texto, gera o embedding com o mesmo modelo usado na ingestão
e consulta o ChromaDB local para recuperar os chunks mais similares.
"""

import argparse
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

MODELO_EMBEDDING = "all-MiniLM-L6-v2"
COLLECTION_NAME = "atendimento_cliente"
DB_PATH_PADRAO = str(Path(__file__).parent / "chroma_db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Busca semântica na base RAG de atendimento ao cliente.",
    )
    parser.add_argument(
        "pergunta",
        type=str,
        help="Pergunta em linguagem natural para buscar na base vetorial.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Quantidade de resultados a retornar (padrão: 5).",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=DB_PATH_PADRAO,
        help=f"Caminho do banco ChromaDB (padrão: {DB_PATH_PADRAO}).",
    )
    return parser.parse_args()


def validar_pergunta(pergunta: str) -> None:
    if not pergunta.strip():
        print("ERRO: A pergunta não pode ser vazia.", file=sys.stderr)
        sys.exit(1)


def conectar_chromadb(db_path: str) -> chromadb.ClientAPI:
    caminho = Path(db_path)
    if not caminho.exists():
        print(
            f"ERRO: Banco ChromaDB não encontrado em: {caminho.resolve()}\n"
            f"Execute 'python ingest.py' primeiro para criar a base vetorial.",
            file=sys.stderr,
        )
        sys.exit(1)

    return chromadb.PersistentClient(path=db_path)


def obter_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    try:
        return client.get_collection(name=COLLECTION_NAME)
    except Exception:
        print(
            f"ERRO: Collection '{COLLECTION_NAME}' não encontrada no ChromaDB.\n"
            f"Execute 'python ingest.py' primeiro para popular a base vetorial.",
            file=sys.stderr,
        )
        sys.exit(1)


def gerar_embedding_pergunta(pergunta: str) -> list[float]:
    try:
        modelo = SentenceTransformer(MODELO_EMBEDDING)
        embedding = modelo.encode([pergunta])
        return embedding[0].tolist()
    except Exception as e:
        print(
            f"ERRO: Falha ao gerar embedding da pergunta.\n"
            f"Detalhe: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


def buscar_chunks(
    collection: chromadb.Collection,
    embedding: list[float],
    top_n: int,
) -> dict:
    return collection.query(
        query_embeddings=[embedding],
        n_results=top_n,
        include=["documents", "metadatas", "distances"],
    )


def exibir_resultados(resultados: dict, pergunta: str) -> None:
    documents = resultados["documents"][0]
    metadatas = resultados["metadatas"][0]
    distances = resultados["distances"][0]

    total = len(documents)

    if total == 0:
        print("Nenhum resultado encontrado.")
        return

    print(f'\nPergunta: "{pergunta}"')
    print(f"Resultados: {total}")
    print(f"Modelo de embedding: {MODELO_EMBEDDING}")
    print("=" * 70)

    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), 1):
        print(f"\n--- Resultado #{i} ---")
        print(f"  Distância (L2):  {dist:.6f}")
        print(f"  Documento:       {meta.get('nome_documento', 'N/A')}")
        print(f"  Seção:           {meta.get('secao', 'N/A')}")
        print(f"  Índice do chunk: {meta.get('indice_chunk', 'N/A')}")
        print(f"  Conteúdo:")
        print()
        for linha in doc.split("\n"):
            print(f"    {linha}")
        print()

    print("=" * 70)


def main() -> None:
    args = parse_args()

    validar_pergunta(args.pergunta)

    client = conectar_chromadb(args.db_path)
    collection = obter_collection(client)

    embedding = gerar_embedding_pergunta(args.pergunta)

    resultados = buscar_chunks(collection, embedding, args.top_n)

    exibir_resultados(resultados, args.pergunta)


if __name__ == "__main__":
    main()
