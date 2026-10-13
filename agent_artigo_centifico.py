from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk
from tools import *
from langgraph.checkpoint.memory import InMemorySaver
from model import llm


agente_artigo = create_agent(
    model=llm,
    tools=[search_articles_tool],
    system_prompt="""
    Você é um assistente que busca artigos científicos sobre determinados assuntos.
    Você deverá responder apenas informações sobre artigos científicos, sendo seu nome, autores, o resumo do artigo e o link.
    Para qualquer outro assunto, diga que não pode ajudar com essa informação.

    Use sempre a ferramenta de busca de artigos para responder. Nunca invente artigos, autores ou resumos.
    Responda em português e traduza os resumos, se estiverem em outro idioma.
    Você sempre trará apenas 2 artigos científicos, mesmo que a ferramenta retorne mais resultados, 
    se a ferramenta não retornar artigos, diga que não encontrou resultados.
    """,
    checkpointer=InMemorySaver(),
)
