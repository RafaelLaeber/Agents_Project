from langchain.tools import tool
import requests

# Artigos de cidades grandes passam de 100 mil caracteres. O limite evita
# mandar o artigo inteiro ao modelo (custo e tempo de resposta).
MAX_CARACTERES = 20000


@tool
def get_locality_info_tool(locality: str) -> str:
    """
    Retorna o artigo completo da Wikipedia em português sobre uma cidade, estado ou país
    (história, geografia, clima, economia, cultura etc.).
    """

    resp = requests.get(
        "https://pt.wikipedia.org/w/api.php",
        headers={"User-Agent": "agentes-langchain/1.0"},
        params={
            "action": "query",
            "prop": "extracts",
            "explaintext": 1,
            "redirects": 1,
            "titles": locality,
            "format": "json",
            "formatversion": 2,
        },
        timeout=15,
    )
    resp.raise_for_status()

    pagina = resp.json()["query"]["pages"][0]
    texto = pagina.get("extract", "")
    if pagina.get("missing") or not texto:
        return f"Nenhuma informação encontrada para '{locality}'."

    if len(texto) > MAX_CARACTERES:
        texto = texto[:MAX_CARACTERES] + "\n\n[artigo truncado]"

    return texto
