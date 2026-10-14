from urllib.parse import quote

import requests



#Agente de previsão do tempo
def _geocodificar(city: str) -> dict | None:
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "pt"},
        timeout=10,
    ).json()
    results = geo.get("results")
    return results[0] if results else None


def get_weather_tool(city: str) -> str:
    """
    Retorna o clima atual (agora) de uma cidade usando a API Open-Meteo.
    """

    place = _geocodificar(city)
    if not place:
        return f"Cidade '{city}' não encontrada."

    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        },
        timeout=10,
    ).json()["current"]

    return (
        f"{place['name']}, {place.get('country', '')} "
        f"(latitude {place['latitude']}, longitude {place['longitude']}): "
        f"{weather['temperature_2m']}°C, "
        f"umidade {weather['relative_humidity_2m']}%, "
        f"vento {weather['wind_speed_10m']} km/h."
    )


def get_forecast_tool(city: str, days: int = 7) -> str:
    """
    Retorna a previsão do tempo dos próximos dias (de 1 a 16) de uma cidade
    usando a API Open-Meteo. Use para perguntas sobre o clima futuro.
    """

    place = _geocodificar(city)
    if not place:
        return f"Cidade '{city}' não encontrada."

    days = max(1, min(days, 16))
    daily = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "daily": "temperature_2m_min,temperature_2m_max,wind_speed_10m_max,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": days,
        },
        timeout=10,
    ).json()["daily"]

    linhas = []
    for i, dia in enumerate(daily["time"]):
        linhas.append(
            f"{dia}: mín {daily['temperature_2m_min'][i]}°C, "
            f"máx {daily['temperature_2m_max'][i]}°C, "
            f"vento máx {daily['wind_speed_10m_max'][i]} km/h, "
            f"chance de chuva {daily['precipitation_probability_max'][i]}%"
        )

    return f"Previsão para {place['name']}, {place.get('country', '')}:\n" + "\n".join(linhas)


def get_locality_summary_tool(locality: str) -> str:
    """
    Retorna um resumo sobre uma cidade, estado ou país usando a Wikipedia em português.
    """

    resp = requests.get(
        f"https://pt.wikipedia.org/api/rest_v1/page/summary/{quote(locality)}",
        headers={"User-Agent": "agentes-langchain/1.0"},
        params={"redirect": "true"},
        timeout=10,
    )

    if resp.status_code == 404:
        return f"Nenhum resumo encontrado para '{locality}'."
    resp.raise_for_status()

    return resp.json().get("extract", f"Nenhum resumo encontrado para '{locality}'.")





#Agente de Artigo Científico

def search_articles_tool(topic: str) -> str:
    """
    Busca artigos científicos sobre um assunto usando a API OpenAlex.
    Retorna título, autores, ano, resumo e link de até 2 artigos.
    """

    resp = requests.get(
        "https://api.openalex.org/works",
        headers={"User-Agent": "agentes-langchain/1.0"},
        params={
            "search": topic,
            "per-page": 2,
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

