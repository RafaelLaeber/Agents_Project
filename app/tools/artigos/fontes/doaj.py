from urllib.parse import quote

import requests

from app.tools.artigos.comum import HEADERS, TIMEOUT, Artigo, limpar_html

URL = "https://doaj.org/api/search/articles/"


def buscar(tema: str, limite: int) -> list[Artigo]:
    """Busca artigos na DOAJ (revistas de acesso aberto, todas as áreas)"""

    # O tema vai no caminho da URL, não nos params.
    resp = requests.get(
        URL + quote(tema),
        params={"pageSize": limite},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()

    artigos = []
    for item in resp.json().get("results", []):
        dados = item.get("bibjson", {})

        doi = next(
            (i.get("id") for i in dados.get("identifier", []) if i.get("type") == "doi"),
            None,
        )
        texto_completo = next(
            (l.get("url") for l in dados.get("link", []) if l.get("type") == "fulltext"),
            None,
        )
        ano = str(dados.get("year", ""))

        artigos.append(
            Artigo(
                titulo=limpar_html(dados.get("title")),
                autores=[a.get("name", "") for a in dados.get("author", []) if a.get("name")],
                ano=int(ano) if ano.isdigit() else None,
                resumo=limpar_html(dados.get("abstract")),
                link=texto_completo or (f"https://doi.org/{doi}" if doi else ""),
                doi=doi,
                fonte="DOAJ",
            )
        )
    return artigos
