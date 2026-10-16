import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from typing import Literal

from langchain.tools import tool

from app.tools.artigos.comum import Artigo
from app.tools.artigos.fontes import arxiv, doaj, eric, europepmc, hal, inspire

logger = logging.getLogger(__name__)

QUANTIDADE = 5   # artigos devolvidos ao agente
POR_FONTE = 5    # artigos pedidos a cada repositório

Area = Literal["geral", "fisica", "exatas", "saude", "humanas", "educacao"]

# Em cada área, da fonte mais forte para a mais fraca. A ordem importa:
# a intercalação pega o 1º resultado de cada fonte nessa sequência.
# Todas as fontes devolvem só artigos com texto completo gratuito.
# O Crossref ficou de fora: não tem filtro confiável de acesso aberto.
FONTES = {
    "geral": [doaj, hal, europepmc],
    "fisica": [inspire, arxiv, doaj],
    "exatas": [arxiv, doaj, hal],
    "saude": [europepmc, doaj],
    "humanas": [hal, doaj],
    "educacao": [eric, doaj, hal],
}


def _consultar_fontes(tema: str, fontes: list) -> list[list[Artigo]]:
    """Consulta as fontes em paralelo. Uma fonte que falha é ignorada."""
    resultados = {}
    with ThreadPoolExecutor(max_workers=len(fontes)) as executor:
        futuros = {executor.submit(fonte.buscar, tema, POR_FONTE): fonte for fonte in fontes}
        for futuro in as_completed(futuros):
            fonte = futuros[futuro]
            try:
                resultados[fonte] = futuro.result()
            except Exception as e:
                logger.warning("Fonte %s falhou: %s", fonte.__name__, e)
    # Mantém a ordem de prioridade definida em FONTES.
    return [resultados[f] for f in fontes if f in resultados]


def _chave(artigo: Artigo) -> str:
    if artigo.doi:
        return artigo.doi.lower()
    return re.sub(r"[^a-z0-9]", "", artigo.titulo.lower())


def _intercalar_sem_repetir(listas: list[list[Artigo]]) -> list[Artigo]:
    """Pega o 1º de cada fonte, depois o 2º de cada uma... e remove duplicatas."""
    vistos = {}
    for posicao in range(max((len(lista) for lista in listas), default=0)):
        for lista in listas:
            if posicao >= len(lista):
                continue
            artigo = lista[posicao]
            chave = _chave(artigo)
            if chave not in vistos:
                vistos[chave] = artigo
            elif not vistos[chave].resumo and artigo.resumo:
                vistos[chave] = artigo
    return list(vistos.values())


def _formatar(numero: int, artigo: Artigo) -> str:
    autores = ", ".join(artigo.autores[:5]) + (" et al." if len(artigo.autores) > 5 else "")
    resumo = artigo.resumo
    if len(resumo) > 700:
        resumo = resumo[:700] + "..."
    return (
        f"{numero}. Título: {artigo.titulo}\n"
        f"Autores: {autores or 'não informado'}\n"
        f"Ano: {artigo.ano or 'não informado'}\n"
        f"Fonte: {artigo.fonte}\n"
        f"Resumo: {resumo or 'não disponível'}\n"
        f"Link: {artigo.link}"
    )


# content_and_artifact: a tool devolve (texto, dados). O LLM lê só o texto;
# os dados ficam no ToolMessage.artifact para o front montar os cards.
@tool(response_format="content_and_artifact")
def search_articles_tool(topic: str, area: Area = "geral") -> tuple[str, list[dict]]:
    """
    Busca artigos científicos em vários repositórios abertos.
    O tema deve estar em inglês e ser curto: de 2 a 5 palavras-chave, sem pontuação
    (ex.: "gravitational waves", "gestational diabetes treatment").
    Escolha a área:
    - "fisica": física, astronomia, astrofísica, cosmologia
    - "exatas": computação, matemática, estatística, engenharia
    - "saude": medicina, biologia, saúde pública
    - "humanas": sociologia, história, direito, economia, filosofia, ciências sociais
    - "educacao": ensino, aprendizagem, políticas educacionais
    - "geral": qualquer outro assunto ou quando a área não for clara
    """

    # Pontuação vira sintaxe de busca em algumas APIs (":" é campo na DOAJ, por ex.).
    topic = re.sub(r"[^\w\s-]", " ", topic).strip()
    listas = _consultar_fontes(topic, FONTES[area])
    artigos = _intercalar_sem_repetir(listas)
    if not artigos:
        return f"Nenhum artigo encontrado para '{topic}'.", []

    # Com resumo primeiro; o sort é estável, então a ordem de relevância se mantém.
    artigos.sort(key=lambda a: not a.resumo)
    escolhidos = artigos[:QUANTIDADE]
    texto = "\n\n".join(_formatar(i, a) for i, a in enumerate(escolhidos, start=1))
    return texto, [asdict(a) for a in escolhidos]
