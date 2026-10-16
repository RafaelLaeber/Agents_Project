import requests

from app.tools.artigos.comum import HEADERS, TIMEOUT, Artigo, limpar_html

URL = "https://api.archives-ouvertes.fr/search/"


def buscar(tema: str, limite: int) -> list[Artigo]:
    """Busca artigos no HAL (arquivo aberto francês, todas as áreas)"""

    resp = requests.get(
        URL,
        params={
            "q": tema,
            "wt": "json",
            "rows": limite,
            "fq": [
                "docType_s:ART",          # só artigos de revista (não teses, pôsteres...)
                "submitType_s:file",      # com o arquivo do artigo depositado
                "openAccess_bool:true",   # e liberado para leitura
            ],
            "fl": "title_s,authFullName_s,producedDateY_i,abstract_s,uri_s,doiId_s,fileMain_s",
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()

    artigos = []
    for item in resp.json().get("response", {}).get("docs", []):
        # Título e resumo vêm como lista (um item por idioma).
        titulos = item.get("title_s") or [""]
        resumos = item.get("abstract_s") or [""]

        artigos.append(
            Artigo(
                titulo=limpar_html(titulos[0]),
                autores=item.get("authFullName_s", []),
                ano=item.get("producedDateY_i"),
                resumo=limpar_html(resumos[0]),
                link=item.get("fileMain_s") or item.get("uri_s", ""),
                doi=item.get("doiId_s"),
                fonte="HAL",
            )
        )
    return artigos
