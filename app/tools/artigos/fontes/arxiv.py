import threading
import time
import xml.etree.ElementTree as ET

import requests

from app.tools.artigos.comum import HEADERS, TIMEOUT, Artigo, limpar_html

URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

# O arXiv pede no máximo uma requisição a cada 3 segundos.
INTERVALO = 3.0
_trava = threading.Lock()
_ultima_chamada = 0.0


def _esperar_vez() -> None:
    global _ultima_chamada
    with _trava:
        espera = INTERVALO - (time.monotonic() - _ultima_chamada)
        if espera > 0:
            time.sleep(espera)
        _ultima_chamada = time.monotonic()


def buscar(tema: str, limite: int) -> list[Artigo]:
    _esperar_vez()
    consulta = " AND ".join(f"all:{palavra}" for palavra in tema.split())
    resp = requests.get(
        URL,
        params={"search_query": consulta, "max_results": limite, "sortBy": "relevance"},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()

    artigos = []
    for entrada in ET.fromstring(resp.content).findall("atom:entry", NS):
        publicado = entrada.findtext("atom:published", "", NS)
        artigos.append(
            Artigo(
                titulo=limpar_html(entrada.findtext("atom:title", "", NS)),
                autores=[a.findtext("atom:name", "", NS) for a in entrada.findall("atom:author", NS)],
                ano=int(publicado[:4]) if publicado[:4].isdigit() else None,
                resumo=limpar_html(entrada.findtext("atom:summary", "", NS)),
                link=entrada.findtext("atom:id", "", NS),
                doi=entrada.findtext("arxiv:doi", None, NS),
                fonte="arXiv",
            )
        )
    return artigos
