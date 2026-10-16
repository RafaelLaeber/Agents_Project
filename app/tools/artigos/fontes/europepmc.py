import requests

from app.tools.artigos.comum import HEADERS, TIMEOUT, Artigo, limpar_html

URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

def buscar(tema: str, limite: int) -> list[Artigo]:
    """Busca artigos na Europe PMC"""

    resp = requests.get(
        URL,
        # OPEN_ACCESS:y traz só artigos com texto completo gratuito no Europe PMC.
        params={
            "query": f"({tema}) AND OPEN_ACCESS:y",
            "format": "json",
            "pageSize": limite,
            "resultType": "core",
        },
        headers = HEADERS,
        timeout = TIMEOUT,
    )
    resp.raise_for_status()

    artigos = []

    for item in resp.json().get("resultList", {}).get("result", []):
            # O link do DOI pode cair na página paga da editora; o do PMC é a cópia gratuita.
            pmcid = item.get("pmcid")
            if not pmcid:
                continue
            doi = item.get("doi")
            link = f"https://europepmc.org/articles/{pmcid}"

            ano = item.get("pubYear", "")
            autores = item.get("authorString", "").rstrip(".").split(",")

            artigos.append(
                Artigo(
                    titulo=limpar_html(item.get("title")),
                    autores=[a.strip() for a in autores if a.strip()],
                    ano=int(ano) if ano.isdigit() else None,
                    resumo=limpar_html(item.get("abstractText")),
                    link=link,
                    doi=doi,
                    fonte="Europe PMC",
                )
            )
    return artigos