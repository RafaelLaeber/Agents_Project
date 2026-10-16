import requests

from app.tools.artigos.comum import HEADERS, TIMEOUT, Artigo, limpar_html

URL = "https://api.crossref.org/works"


def buscar(tema: str, limite: int) -> list[Artigo]:
    resp = requests.get(
        URL,
        params={
            "query": tema,
            "rows": limite,
            "filter": "type:journal-article",
            "select": "DOI,title,author,issued,abstract,URL",
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()

    artigos = []
    for item in resp.json()["message"]["items"]:
        titulos = item.get("title") or []
        if not titulos:
            continue

        autores = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in item.get("author", [])
        ]
        partes = (item.get("issued") or {}).get("date-parts") or [[None]]
        doi = item.get("DOI")

        artigos.append(
            Artigo(
                titulo=limpar_html(titulos[0]),
                autores=[a for a in autores if a],
                ano=partes[0][0] if partes[0] else None,
                resumo=limpar_html(item.get("abstract")),
                link=item.get("URL") or f"https://doi.org/{doi}",
                doi=doi,
                fonte="Crossref",
            )
        )
    return artigos
