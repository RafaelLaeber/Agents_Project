import html
import re
from dataclasses import dataclass

HEADERS = {"User-Agent": "agentes-langchain/1.0"}
TIMEOUT = 10 #seconds

@dataclass
class Artigo:
    titulo: str
    autores: list[str]
    ano: int | None
    resumo: str
    link: str
    doi: str | None
    fonte: str


def limpar_html(texto: str | None) -> str:
    """Remove tags HTML/XML e espaços repetidos (Crossref e Europe PMC mandam resumos com tags)"""

    if not texto:
        return ""
    sem_tags = re.sub(r"<[^>]+>", " ", texto)
    return re.sub(r"\s+", " ", html.unescape(sem_tags)).strip()