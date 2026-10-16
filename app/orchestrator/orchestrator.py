from typing import Iterator, Literal

from langchain_core.messages import AIMessageChunk
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough
from pydantic import BaseModel

from app.agents.artigos import agente_artigo
from app.agents.localidade import agente_cidade
from app.llm import llm

MSG_FORA_ESCOPO = (
    "Não posso ajudar com essa informação. "
    "Pergunte sobre cidades, estados, países ou artigos científicos."
)


# Define o que o roteador deve devolver: um objeto com um campo destino.
# O Literal impede o LLM de inventar algo como "clima" ou "cidades". Se ele tentar, a validação falha.
# Na prática, o resultado é algo como Rota(destino="localidade"), e você lê com .destino.

class Rota(BaseModel):
    destino: Literal["localidade", "artigo", "fora_escopo"]


roteador = (
    # from_messages monta uma conversa com duas mensagens.
    # ("system", ...) é a instrução para o modelo: classificar e descrever cada categoria.
    # ("human", "{pergunta}") é a mensagem do usuário. {pergunta} é uma variável, preenchida quando você 
    # chama roteador.invoke({"pergunta": "..."}).
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Classifique a pergunta do usuário em um destino: "
                "'localidade' (cidades, estados, países, clima, previsão do tempo), "
                "'artigo' (artigos científicos, pesquisas, papers) "
                "ou 'fora_escopo' (qualquer outro assunto)."
            ),
            ("human", "{pergunta}"),
        ]
    )
    # llm.with_structured_output(Rota) cria uma versão do LLM que, em vez de texto livre, devolve um objeto Rota.
    # Por baixo, o LangChain envia o schema para a OpenAI e converte a resposta JSON em Rota.
    | llm.with_structured_output(Rota)
)

AGENTES = {
    "localidade": agente_cidade,
    "artigo": agente_artigo,
}


# O orquestrador trabalha com {"pergunta": "..."}.
# O create_agent espera {"messages": [...]}, uma lista de mensagens.
# A função converte um formato no outro.
# O _ no início do nome é uma convenção de Python para "uso interno deste arquivo".
def _entrada_agente(x: dict) -> dict:
    return {"messages": [{"role": "user", "content": x["pergunta"]}]}


# RunnableLambda(_entrada_agente): converte {"pergunta": ...} em {"messages": [...]}.
# agente: roda o subagente, que chama tools e gera a resposta. Ele devolve o estado final, 
# {"messages": [todas as mensagens da conversa]}.
# RunnableLambda(lambda r: r["messages"][-1].content): pega a última mensagem ([-1]), 
# que é a resposta final da IA, e devolve só o texto (.content).
def _como_chain(agente):
    # create_agent devolve um Runnable; só adapta entrada e saída.
    return (
        RunnableLambda(_entrada_agente)
        | agente
        | RunnableLambda(lambda resposta: resposta["messages"][-1].content)
    )


# Chain completa (uso com .invoke): roteia e responde.
# {"pergunta": str} -> str
orquestrador = RunnablePassthrough.assign(rota=roteador) | RunnableBranch(
    *[
        (lambda x, d=destino: x["rota"].destino == d, _como_chain(agente))
        for destino, agente in AGENTES.items()
    ],
    RunnableLambda(lambda _: MSG_FORA_ESCOPO),
)



#Extrair e transmitir o texto de um chunk de mensagem. O chunk pode ser uma string, ou uma lista de strings e dicts.
def _texto(content) -> str:

    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        return "".join(
            b if isinstance(b, str) else b.get("text", "")
            for b in content
            if isinstance(b, (str, dict))
        )
    return ""


def transmitir(pergunta: str, thread_id: str) -> Iterator[str]:
    """Roteia pela chain e transmite os tokens do subagente escolhido."""
    destino = roteador.invoke({"pergunta": pergunta}).destino
    agente = AGENTES.get(destino)
    if agente is None:
        yield MSG_FORA_ESCOPO
        return

    for chunk, _ in agente.stream(
        _entrada_agente({"pergunta": pergunta}),
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessageChunk):
            texto = _texto(chunk.content)
            if texto:
                yield texto