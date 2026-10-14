from flask import (
    Flask,
    Response,
    jsonify,
    request,
    send_from_directory,
    stream_with_context,
)
from langchain_core.messages import AIMessageChunk

from agent_artigo_centifico import agente_artigo 
from agent_inf_localidade import agente_cidade

app = Flask(__name__)

AGENTES = {
    "cidade": (agente_cidade, "cidade-1"),
    "artigo": (agente_artigo, "artigo-1"),
}


def _extrair_texto(content) -> str:
    """O content do chunk pode ser str ou lista de blocos; devolve só o texto."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            bloco if isinstance(bloco, str) else bloco.get("text", "")
            for bloco in content
            if isinstance(bloco, (str, dict))
        )
    return ""


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.post("/api/informacao")
def informacao():
    pergunta = (request.get_json(silent=True) or {}).get("pergunta", "").strip()
    if not pergunta:
        return jsonify(erro="Informe a pergunta."), 400

    nome = request.args.get("agente", "cidade")
    if nome not in AGENTES:
        return jsonify(erro=f"Agente '{nome}' não existe."), 400

    agent, thread_id = AGENTES[nome]

    def gerar():
        try:
            for chunk, _ in agent.stream(
                {"messages": [{"role": "user", "content": pergunta}]},
                config={"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessageChunk):
                    texto = _extrair_texto(chunk.content)
                    if texto:
                        yield texto
        except Exception as e:
            yield f"\n\nFalha ao consultar o agente: {e}"

    return Response(
        stream_with_context(gerar()),
        mimetype="text/plain",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


if __name__ == "__main__":
    app.run(debug=True)
