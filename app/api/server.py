from pathlib import Path

from flask import (
    Flask,
    Response,
    jsonify,
    request,
    send_from_directory,
    stream_with_context,
)

from app.orchestrator.orchestrator import transmitir

THREAD_ID = "chat-1"
STATIC_DIR = Path(__file__).resolve().parents[2] / "static"

app = Flask(__name__, static_folder=STATIC_DIR)


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.post("/api/informacao")
def informacao():
    pergunta = (request.get_json(silent=True) or {}).get("pergunta", "").strip()
    if not pergunta:
        return jsonify(erro="Informe a pergunta."), 400

    def gerar():
        try:
            yield from transmitir(pergunta, THREAD_ID)
        except Exception as e:
            yield f"\n\nFalha ao consultar o agente: {e}"

    return Response(
        stream_with_context(gerar()),
        mimetype="text/plain",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


if __name__ == "__main__":
    app.run(debug=True)
