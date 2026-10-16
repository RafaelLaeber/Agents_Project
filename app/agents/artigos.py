from langchain.agents import create_agent
from app.tools.artigos import search_articles_tool
from langgraph.checkpoint.memory import InMemorySaver
from app.llm import llm


agente_artigo = create_agent(
    model=llm,
    tools=[search_articles_tool],
    system_prompt="""
    Use sempre a ferramenta de busca de artigos para responder. Nunca invente artigos, autores ou resumos.
    Antes de chamar a ferramenta, traduza o assunto para inglês e escolha a área mais adequada
    (as opções estão descritas na própria ferramenta).
    Apresente os 5 artigos retornados, com título, autores, ano, fonte e link,
    e resuma cada resumo em português em até 5 frases.
    Se a ferramenta não retornar artigos, diga que não encontrou resultados.
    """,
    checkpointer=InMemorySaver(),
)
