import csv
import os
from datetime import datetime

# Configuração
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "historico_interacoes.csv")

def _garantir_estrutura_log():
    """
    Função interna de segurança.
    Verifica se a pasta e o arquivo existem.
    Se não existirem, cria a estrutura e o cabeçalho CSV.
    Se existirem, não faz nada (preserva os dados).
    """
    try:
        # Garante que a pasta existe
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)
            print(f"[LOGGER] Pasta '{LOG_DIR}' criada.")

        # Garante que o arquivo .csv existe
        if not os.path.exists(LOG_FILE):
            print(f"[LOGGER] Arquivo de log não encontrado. Criando novo em: {LOG_FILE}")
            with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Escreve o cabeçalho
                writer.writerow([
                    "Timestamp", 
                    "Input Usuario", 
                    "Intencao", 
                    "Dados Tecnicos", 
                    "Output Sistema"
                ])
    except Exception as e:
        print(f"[ERROR] Falha crítica ao garantir estrutura de logs: {e}")

def registrarInteracao(texto_usuario, intencao, dados_tecnicos, resposta_sistema):
    """
    Salva a interação no CSV.
    É seguro chamar a qualquer momento, pois verifica a estrutura antes.
    """
    # Garante que o arquivo exista
    _garantir_estrutura_log()

    try:
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                texto_usuario,
                intencao,
                str(dados_tecnicos),
                resposta_sistema
            ])
            
    except Exception as e:
        print(f"[ERROR] Não foi possível salvar no log: {e}")