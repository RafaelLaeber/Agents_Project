import requests

from app.tools.artigos.comum import HEADERS, TIMEOUT, Artigo, limpar_html

URL = "https://inspirehep.net/api/literature"


def buscar(tema: str, limite: int) -> list[Artigo]:
    """Busca artigos no INSPIRE-HEP (física de altas energias e astrofísica)"""

    resp = requests.get(
        URL,
        params={
            "q": tema,
            # Pede o dobro porque os sem cópia no arXiv são descartados abaixo.
            "size": limite * 2,
            # Os mais citados primeiro: traz os trabalhos de referência do tema.
            "sort": "mostcited",
            "fields": "titles,authors.full_name,abstracts,dois,earliest_date,arxiv_eprints",
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()

    artigos = []
    for item in resp.json().get("hits", {}).get("hits", []):
        dados = item.get("metadata", {})

        # O link da revista costuma ser pago; só entra quem tem cópia gratuita no arXiv.
        eprints = dados.get("arxiv_eprints") or []
        if not eprints:
            continue

        titulos = dados.get("titles") or [{}]
        resumos = dados.get("abstracts") or [{}]
        dois = dados.get("dois") or [{}]
        ano = dados.get("earliest_date", "")[:4]

        artigos.append(
            Artigo(
                titulo=limpar_html(titulos[0].get("title")),
                autores=[a.get("full_name", "") for a in dados.get("authors", [])],
                ano=int(ano) if ano.isdigit() else None,
                resumo=limpar_html(resumos[0].get("value")),
                link=f"https://arxiv.org/abs/{eprints[0].get('value')}",
                doi=dois[0].get("value"),
                fonte="INSPIRE-HEP",
            )
        )
        if len(artigos) == limite:
            break
    return artigos
