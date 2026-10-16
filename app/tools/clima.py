from langchain.tools import tool
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

@tool
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

@tool
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
