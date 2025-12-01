from contextlib import asynccontextmanager
import base64
import uuid
import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, WebSocket

from source.back.yapper import gerarAudio, transcreverAudio, processarIntencao
from source.back.dbManager import carregarDataframe
from faster_whisper import WhisperModel

# Config

MODEL_SIZE = "large-v3" # Ou "base" se for necessário algo mais rápido
model_whisper = None
df_filmes = None

# Setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    global df_filmes, model_whisper
    print("[SYSTEM] Iniciando virtKino")
    print("[SYSTEM] Carregando Dataframe")
    df_filmes = carregarDataframe()
    print(f"[SYSTEM] Carregando Faster-Whisper")
    model_whisper = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")
    print("[SYSTEM] Conectando com TTS")
    # Gera um áudio para iniciar a conexão.
    await gerarAudio("Sistema virtKino inicializado e pronto.")
    
    os.makedirs("static", exist_ok=True)
    yield
    print("[SYSTEM] Desligando")
    # Limpeza dos audios
    for f in os.listdir("static"):
        if f.startswith("fala_") or f.startswith("rec_"):
            try: os.remove(os.path.join("static", f))
            except: pass

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para o React funcionar
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mounting das pastas para o front-end
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="source/front/virtkino-front/dist/assets"), name="assets")

# Rotas
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """
    Rota inteligente que serve arquivos estáticos se existirem,
    ou o index.html se for uma rota de navegação (React Router).
    """
    # Proteção: Ignora rotas de API ou websocket explicitamente
    if full_path.startswith("api") or full_path.startswith("ws"):
        return None

    # Verifica se o arquivo físico existe dentro da pasta 'dist'
    # Ex: Se pedirem 'idle.png', procura em 'dist/idle.png'
    possible_file = os.path.join("source/front/virtkino-front/dist", full_path)
    
    if os.path.exists(possible_file) and os.path.isfile(possible_file):
        return FileResponse(possible_file)
    
    # Se não for um arquivo físico, retorna o App React (index.html)
    return FileResponse("source/front/virtkino-front/dist/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WEB] Cliente conectado")
    
    try:
        while True:
            # Recebe JSON contendo o áudio em base64
            data = await websocket.receive_json()
            
            if "audio_data" in data:
                # 1. Salva o áudio recebido (webm/wav do navegador)
                audio_bytes = base64.b64decode(data["audio_data"])
                nome_arquivo_rec = f"static/rec_{uuid.uuid4()}.webm"
                
                with open(nome_arquivo_rec, "wb") as f:
                    f.write(audio_bytes)
                
                # 2. Avisa: Processando
                await websocket.send_json({"tipo": "estado", "valor": "thinking"})
                
                # 3. Transcreve (Whisper Local)
                texto_usuario = transcreverAudio(nome_arquivo_rec, model_whisper)
                
                # Limpa arquivo de entrada
                os.remove(nome_arquivo_rec)

                if texto_usuario:
                    # Envia transcrição para o usuário ver
                    await websocket.send_json({"tipo": "transcricao", "texto": texto_usuario})
                    
                    # 4. Lógica (LLM)
                    resposta, debug_info = processarIntencao(texto_usuario, df_filmes)
                    
                    # 3. Gera Áudio
                    arquivo = await gerarAudio(resposta)
                    
                    # 4. Devolve tudo (+ DEBUG INFO)
                    await websocket.send_json({
                        "tipo": "resposta",
                        "texto": resposta,
                        "audio_url": f"/static/{arquivo}",
                        "estado": "speaking",
                        "debug": debug_info # Envia o "Raio-X" pro front
                    })
                else:
                    # Whisper não ouviu nada
                    await websocket.send_json({"tipo": "estado", "valor": "idle"})

    except Exception as e:
        print(f"Erro WS: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)