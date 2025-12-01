import { useState, useEffect, useRef } from 'react';
import './App.css';
import DebugPanel from './DebugPanel';

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${protocol}//${window.location.host}/ws`;
const BASE_URL = ""; // Áudio é Relativo a origem

function App() {
  const [socket, setSocket] = useState(null);
  const [status, setStatus] = useState("OFFLINE"); // idle, listening, thinking, speaking
  const [chatText, setChatText] = useState("...");
  const [debugData, setDebugData] = useState(null);
  const [isRecording, setIsRecording] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioPlayerRef = useRef(new Audio());

  // WebSocket
  useEffect(() => {
    let wsInstance = null;
    let reconnectTimeout = null;

    const connect = () => {
      wsInstance = new WebSocket(WS_URL);

      wsInstance.onopen = () => {
        console.log("WS Conectado");
        setStatus("idle");
      };

      wsInstance.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.tipo === "estado") {
          setStatus(data.valor);
        }

        if (data.tipo === "transcricao") {
          setChatText(`Você: "${data.texto}"`);
        }

        if (data.tipo === "resposta") {
          setChatText(`virtKino: "${data.texto}"`);
          if (data.debug) setDebugData(data.debug);

          const audioUrl = `${BASE_URL}${data.audio_url}?t=${Date.now()}`;
          playAudio(audioUrl);
        }
      };

      wsInstance.onclose = () => {
        console.log("WS Fechado. Tentando reconectar em 3s...");
        setStatus("OFFLINE");
        // Tenta reconectar SEM recarregar a página
        reconnectTimeout = setTimeout(connect, 3000);
      };

      wsInstance.onerror = (err) => {
        console.error("Erro no WebSocket:", err);
        wsInstance.close(); // Força o fechamento para disparar o onclose e tentar reconectar
      };

      setSocket(wsInstance);
    };

    connect();

    // Cleanup
    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsInstance) {
        // Remove o listener onclose para não tentar reconectar enquanto desmonta o componente
        wsInstance.onclose = null;
        wsInstance.close();
      }
    };
  }, []);

  // Output de Audio
  const playAudio = (url) => {
    setStatus("speaking");
    audioPlayerRef.current.src = url;
    audioPlayerRef.current.play().catch(e => console.error("Erro play:", e));

    audioPlayerRef.current.onended = () => {
      setStatus("idle");
    };
  };

  // Input de Audio
  const startRecording = async () => {
    if (status !== 'idle' && status !== 'OFFLINE') return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        sendAudio(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setStatus("listening");
      setChatText("...");

    } catch (err) {
      alert("Erro Microfone: " + err.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      // O status muda para 'thinking' quando o WS responder
    }
  };

  const sendAudio = (blob) => {
    const reader = new FileReader();
    reader.readAsDataURL(blob);
    reader.onloadend = () => {
      const base64Audio = reader.result.split(',')[1];
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ audio_data: base64Audio }));
      }
    };
  };

  // Render

  // Labels bonitas para o status
  const statusLabels = {
    idle: "PRONTO",
    listening: "OUVINDO...",
    thinking: "PROCESSANDO...",
    speaking: "FALANDO...",
    OFFLINE: "DESCONECTADO"
  };

  return (
    <div className="container">
      {/* Lado Esquerdo: Avatar */}
      <div className={`main-interface state-${status}`}>
        <div className="avatar-container">
          <img
            src={`/${status === 'OFFLINE' ? 'idle' : status}.png`}
            alt="Avatar"
            className="avatar-img"
            onError={(e) => {
              // Fallback
              if (!e.target.src.includes("idle.png")) {
                e.target.src = '/idle.png';
              } else {
                // Se até o idle.png falhou, desiste ou põe uma imagem transparente de placeholder
                console.error("Imagem crítica não encontrada!");
                e.target.onerror = null; // Remove o listener para parar o loop
              }
            }}
          />
        </div>

        <div className={`status-badge ${status !== 'idle' ? 'active' : ''}`}>
          {statusLabels[status] || status}
        </div>

        <div className="chat-box">{chatText}</div>

        <button
          className={`btn-ptt ${isRecording ? 'recording' : ''}`}
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          onTouchStart={(e) => { e.preventDefault(); startRecording(); }}
          onTouchEnd={(e) => { e.preventDefault(); stopRecording(); }}
          disabled={status === 'OFFLINE' || status === 'thinking' || status === 'speaking'}
        >
           
        </button>
        <p style={{ fontSize: '0.8rem', color: '#666' }}>Segure para falar</p>
      </div>

      {/* Lado Direito: Debug */}
      <DebugPanel data={debugData} />
    </div>
  );
}

export default App;