from langchain.agents import create_agent
from pydantic import BaseModel, Field
from app.tools.artigos import search_articles_tool
from langgraph.checkpoint.memory import InMemorySaver
from app.llm import llm


class ArtigoResumido(BaseModel):
    numero: int = Field(description="Número do artigo na lista devolvida pela ferramenta (começa em 1)")
    resumo_curto: str = Field(description="Resumo do artigo em português, em até 2 frases")


# Resposta estruturada: o front monta os cards com título, autores e link vindos da
# ferramenta, e usa daqui só a introdução e o resumo curto de cada artigo.
class RespostaArtigos(BaseModel):
    introducao: str = Field(description="Uma frase curta em português apresentando os resultados")
    artigos: list[ArtigoResumido] = Field(description="Um item por artigo devolvido, na mesma ordem")


agente_artigo = create_agent(
    model=llm,
    tools=[search_articles_tool],
    response_format=RespostaArtigos,
    system_prompt="""
    Use sempre a ferramenta de busca de artigos para responder. Nunca invente artigos, autores ou resumos.
    Antes de chamar a ferramenta, traduza o assunto para inglês em poucas palavras-chave
    (ex.: "ondas gravitacionais" -> "gravitational waves") e escolha a área mais adequada
    (as opções estão descritas na própria ferramenta).
    Para cada artigo devolvido, escreva um resumo curto em português (até 2 frases),
    usando o número dele na lista.
    Se a ferramenta não retornar artigos, deixe a lista vazia e diga na introdução que não encontrou resultados.
    """,
    checkpointer=InMemorySaver(),
)
