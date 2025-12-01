import ollama
import json

def extrairFiltros(texto_usuario: str, max_retries: int = 2) -> dict:
    """
    Extrai tags da mensagem do usuário usando um modelo LLM
    """
    prompt_sistema = """
    Você é um assistente especializado em recomendação de filmes chamado virtKino.
    Sua tarefa é analisar o texto do usuário (em Português) e extrair critérios de busca para um banco de dados em INGLÊS.
    
    Você DEVE responder APENAS com um objeto JSON válido.
    
    REGRAS DE TRADUÇÃO OBRIGATÓRIAS:
    1. "genero": Mantenha em Português (ex: "Ação", "Terror"). Nosso sistema traduzirá depois.
    2. "palavras_chave": TRADUZA OBRIGATORIAMENTE PARA INGLÊS. O banco de dados só entende inglês.
       Exemplo: Se o usuário pedir "robôs", você deve enviar ["robots", "androids"].
       Exemplo: Se pedir "praia", envie ["beach"].
    
    O JSON deve conter:
    - "genero": string (PT-BR).
    - "palavras_chave": lista de strings (EM INGLÊS).
    - "ano_minimo": inteiro.
    - "ano_maximo": inteiro.

    Exemplos:
    - User: "filme de terror com zumbis"
      JSON: {"genero": "Terror", "palavras_chave": ["zombies", "undead"]}
    - User: "comédia romântica anos 90"
      JSON: {"genero": "Comédia", "palavras_chave": ["romance", "love"], "ano_minimo": 1990, "ano_maximo": 1999}
    """

    messages = [
        {'role': 'system', 'content': prompt_sistema},
        {'role': 'user', 'content': texto_usuario}
    ]

    print(f"[INFO] Enviando para o LLM: '{texto_usuario}'")
    for attempt in range(max_retries):
        try:
            response = ollama.chat(model='llama3:8b', messages=messages, format='json')
            content_str = response['message']['content']
            # Decoding do json como validação
            filtros = json.loads(content_str)
            
            print("[INFO] LLM retornou um JSON válido:", filtros)
            return filtros
        # Caso o modelo erre, dá um retry
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[WARN] Erro de JSON na tentativa {attempt + 1}: {e}")
            print(f"[WARN] Resposta inválida do LLM: {content_str}")
            if attempt < max_retries - 1:
                print("[INFO] Tentando auto-correção...")
                messages.append({'role': 'assistant', 'content': content_str})
                messages.append({
                    'role': 'user', 
                    'content': 'Sua resposta anterior não foi um JSON válido. Por favor, corrija-a e retorne APENAS o JSON.'
                })
            continue

    print("[ERROR] Falha ao obter um JSON válido após múltiplas tentativas.")
    return {}

def classificarIntencao(texto_usuario: str) -> str:
    """
    Classifica a intenção do usuário como 'filme' ou 'conversa'.
    """
    prompt_sistema = """
    Sua única tarefa é classificar a intenção do usuário.
    Responda APENAS com UMA palavra: 'filme' ou 'conversa'.

    - Responda 'filme' se o usuário estiver pedindo uma recomendação de filme, procurando por um filme, ou falando sobre que tipo de filme ele quer assistir.
    - Responda 'conversa' para todo o resto (saudações, despedidas, perguntas aleatórias, como você está, etc.).
    - Se o usuário estiver perguntando sobre sua opinião do que você acha do filme ou de um filme, responda 'conversa'.

    Exemplos:
    Usuário: "Oi, tudo bem?" -> conversa
    Usuário: "Me recomenda um filme de ação" -> filme
    Usuário: "Qual a capital do Brasil?" -> conversa
    Usuário: "Quero algo de terror bem antigo" -> filme
    Usuário: "Obrigado!" -> conversa
    Usuário: "O que você acha deste filme?" -> conversa
    """
    try:
        response = ollama.chat(
            model='llama3:8b',
            messages=[
                {'role': 'system', 'content': prompt_sistema},
                {'role': 'user', 'content': texto_usuario}
            ]
        )
        # Limpa a resposta para garantir apenas uma palavra
        intencao = response['message']['content'].strip().lower()
        
        if intencao == "filme":
            return "filme"
        else:
            return "conversa"

    except Exception as e:
        print(f"[WARN] Erro ao classificar intenção: {e}")
        return "conversa" # Fallback, apenas tenta conversar

if __name__ == "__main__":
    print("[DEBUG] Teste do parser")
    extrairFiltros("me recomende uma ficção científica com robôs que não seja muito antiga")