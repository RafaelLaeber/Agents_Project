from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk
from tools import *
from langgraph.checkpoint.memory import InMemorySaver
from model import llm


agente_cidade = create_agent(
    model=llm,
    tools=[get_weather_tool, get_locality_summary_tool],
    system_prompt="""
    Você é um assistente que fornece qualquer informação sobre cidades, estados ou países.
    Você deveria responder apenas informações sobre cidades, estados ou países . 
    Para qualquer outro assunto que não seja sobre isso, diga que não pode ajudar com essa informação.

    Use as ferramentas para clima e a de resumo para mandar resumo ou pesquisar sobre qualquer informação de alguma cidade, estado ou país. 
    Se não tiver ferramenta para a informação pedida, diga que não tem acesso a esse dado.
    """,
    checkpointer=InMemorySaver(),
)
