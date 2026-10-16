import requests

from app.tools.artigos.comum import HEADERS, TIMEOUT, Artigo, limpar_html

URL = "https://api.ies.ed.gov/eric/"


def buscar(tema: str, limite: int) -> list[Artigo]:
    """Busca artigos no ERIC (pesquisa em educação)"""

    resp = requests.get(
        URL,
        params={
            # e_fulltextauth:1 = o PDF completo está hospedado no próprio ERIC.
            "search": f"{tema} AND e_fulltextauth:1",
            "format": "json",
            "rows": limite,
            "fields": "id,title,author,publicationdateyear,description,url,e_fulltextauth",
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()

    artigos = []
    for item in resp.json().get("response", {}).get("docs", []):
        if item.get("e_fulltextauth") != 1:
            continue

        url = item.get("url", "")
        doi = url.split("doi.org/", 1)[1] if "doi.org/" in url else None

        artigos.append(
            Artigo(
                titulo=limpar_html(item.get("title")),
                autores=item.get("author", []),
                ano=item.get("publicationdateyear"),
                resumo=limpar_html(item.get("description")),
                link=f"https://files.eric.ed.gov/fulltext/{item.get('id')}.pdf",
                doi=doi,
                fonte="ERIC",
            )
        )
    return artigos
