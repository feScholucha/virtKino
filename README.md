# virtKino: Recomendador de Filmes Conversacional
<img src="static/idle.png" alt="Kino" width="60%">\
## Sobre o Projeto
O virtKino é um sistema de recomendação de filmes interativo e didático que utiliza um avatar "animado" como interface de comunicação verbal.\
O objetivo é desmistificar o funcionamento de IAs generativas e Sistemas de Recomendação, expondo o "raciocínio" da máquina em tempo real através de um Painel de Debug.

## Como Funciona (Arquitetura)

Percepção (Ouvido): O navegador captura o áudio e envia para o backend, onde o modelo [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (rodando na GPU) transcreve a fala.

Interpretação (Cérebro): O modelo de linguagem Llama 3 (via Ollama) analisa o texto, classifica a intenção (conversa vs. pedido de filme) e extrai filtros de busca (ex: {"genero": "Terror", "ano": 1980}).

Busca (Memória): Um algoritmo em Python filtra o dataset [TMDB 5000](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata), pontuando filmes por relevância de metadados e sinopse.

Resposta (Voz): O sistema gera uma resposta personalizada (RAG) e a sintetiza em voz neural usando a biblioteca Edge-TTS (A única parte que precisa se comunicar externamente).

## Pré-requisitos:
Para rodar este projeto localmente, você precisará de um ambiente Linux ou WSL2 com suporte a GPU NVIDIA com tecnologia CUDA.
- Python 3.10.x
- Node.js & NPM (para o Frontend)
- Ollama (para rodar o LLM localmente)
- Placa de Vídeo NVIDIA (com drivers CUDA instalados)
- Microfone conectado ao computador e dispositivo de saída de som (opcional)

## Instalação e Setup

A instalação do Toolkit CUDA utilizado se encontra abaixo:

```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.3.2/local_installers/cuda-repo-wsl-ubuntu-12-3-local_12.3.2-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-3-local_12.3.2-1_amd64.deb
sudo cp /var/cuda-repo-wsl-ubuntu-12-3-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-3

echo 'export PATH=/usr/local/cuda-12.3/bin${PATH:+:${PATH}}' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.3/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}' >> ~/.bashrc
source ~/.bashrc
```

Instale também os requisitos pedidos do [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)

Instalação do Ollama e o modelo Llama 3 (8B):

```bash
curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
ollama pull llama3:8b
```
Clone o Repositório:

```bash
git clone https://github.com/feScholucha/virtKino
cd virtKino
```
Instale o dataset [TMDB 5000](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) na pasta de dataset

Em um terminal, vá para a pasta do front-end e compile o dist:
```bash
cd source/front/virtkino-front
npm install
npm run build
```
Em outro terminal, instale os requirements e ative o servidor local
```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python3 server.py
```

Se o servidor está funcionando corretamente, em outro terminal, instale o tunel da cloudflare e o execute se precisar transmitir o site fora do localhost

```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

cloudflared tunnel --url http://localhost:8000
```

## Estrutura do Código:

- server.py: O servidor FastAPI que orquestra tudo (WebSocket, API, Arquivos Estáticos)
- source/back/parserLLM.py: Módulo que conversa com o Ollama para classificar intenções e extrair JSON
- source/back/dbManager.py: Módulo Pandas que carrega o dataset e executa o algoritmo de recomendação
- source/back/yapper.py: Módulo responsável pela síntese de fala (Edge-TTS) e transcrição (Whisper) e pela conversa com o usuário
- source/front/virtkino-front/: Código fonte do frontend em React (Vite)