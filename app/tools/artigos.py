from langchain.tools import tool
import requests


#Agente de Artigo Científico
@tool
def search_articles_tool(topic: str) -> str:
    """
    Busca artigos científicos sobre um assunto usando a API OpenAlex.
    Retorna título, autores, ano, resumo e link de até 4 artigos.
    """

    resp = requests.get(
        "https://api.openalex.org/works",
        headers={"User-Agent": "agentes-langchain/1.0"},
        params={
            "search": topic,
            "per-page": 4,
            "select": "title,authorships,publication_year,abstract_inverted_index,doi,id",
        },
        timeout=15,
    )
    resp.raise_for_status()

    resultados = resp.json().get("results", [])
    if not resultados:
        return f"Nenhum artigo encontrado para '{topic}'."

    artigos = []
    for obra in resultados:
        autores = [a["author"]["display_name"] for a in obra.get("authorships", [])]
        autores_txt = ", ".join(autores[:5]) + (" et al." if len(autores) > 5 else "")

        resumo = _reconstruir_resumo(obra.get("abstract_inverted_index"))
        if len(resumo) > 700:
            resumo = resumo[:700] + "..."

        artigos.append(
            f"Título: {obra.get('title')}\n"
            f"Autores: {autores_txt or 'não informado'}\n"
            f"Ano: {obra.get('publication_year')}\n"
            f"Resumo: {resumo or 'não disponível'}\n"
            f"Link: {obra.get('doi') or obra.get('id')}"
        )

    return "\n\n".join(artigos)


def _reconstruir_resumo(indice: dict | None) -> str:
    if not indice:
        return ""
    palavras = {}
    for palavra, posicoes in indice.items():
        for pos in posicoes:
            palavras[pos] = palavra
    return " ".join(palavras[p] for p in sorted(palavras))
