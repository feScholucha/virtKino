import pandas as pd
import numpy as np
import json
import os

def carregarGeneros(filepath = "configs/genres.json"):
    """
    Carrega o mapeamento de gêneros de um arquivo JSON externo.\\
    Se falhar, retorna um dicionário vazio.
    """
    if not os.path.exists(filepath):
        print(f"[WARN] Arquivo '{filepath}' não encontrado! O filtro de gêneros irá falhar!")
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            print("[INFO] Mapa de gêneros carregado")
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Falha ao ler '{filepath}': {e}")
        return {}

def parse_json_col(x, key='name'):
    try:
        data = json.loads(x)
        return [item[key] for item in data]
    except:
        return []
    
def carregarDataframe(filepath: str = 'dataset/tmdb_5000_movies.csv'):
    """
    Carrega o dataset TMDB 5000 e processa as colunas JSON.\\
    Retorna o Dataframe preparado
    """
    # Carregando Dataset
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"[ERROR] Dataset TMDB 5000 não encontrado!")
        return pd.DataFrame()

    # Extração de Ano
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['year'] = df['release_date'].dt.year
    
    # Processamento de Gêneros e Palavras Chave
    print("[INFO] Processando metadados do dataset")
    df['genres_list'] = df['genres'].apply(parse_json_col)
    df['keywords_list'] = df['keywords'].apply(parse_json_col)
    
    # Coluna soup para busca fácil de palavras
    df['soup'] = df['title'] + ' ' + \
                 df['genres_list'].apply(lambda x: ' '.join(x)) + ' ' + \
                 df['keywords_list'].apply(lambda x: ' '.join(x)) + ' ' + \
                 df['overview'].fillna('')
    
    print(f"[INFO] Dataset TMDB carregado: {len(df)} filmes.")
    return df

def filtrarFilmes(df_filmes: pd.DataFrame, filtros: dict, verbose = False) -> pd.DataFrame:
    """
    Recomendador de Filmes score-wise por critérios
    """
    if df_filmes.empty: return df_filmes
    
    candidatos = df_filmes.copy()
    candidatos['score'] = 0.0

    print(f"[Recomendador] Critérios Originais: {filtros}")

    # Pontua os candidatos que batem os generos
    if 'genero' in filtros and filtros['genero']:
        # Transforma em lowercase
        genero_input = filtros['genero'].lower().strip()
        # Transforma na tradução se disponível
        genero_alvo = carregarGeneros().get(genero_input, genero_input)
        if verbose and genero_input is not genero_alvo: print(f"[INFO] Gênero traduzido: '{genero_input}' => '{genero_alvo}'")
        # Verifica se o gênero alvo está na lista de gêneros do filme
        matches = candidatos['genres_list'].apply(lambda lista: 1 if any(g.lower() == genero_alvo.lower() for g in lista) else 0) # type: ignore
        candidatos['score'] += matches * 500 

    # Pontua os candidatos que batem as palavras-chaves, generos (de novo), etc.
    if 'palavras_chave' in filtros and filtros['palavras_chave']:
        regex = '|'.join(filtros['palavras_chave'])
        # Busca na soup
        matches = candidatos['soup'].str.contains(regex, case=False, na=False).astype(int)
        candidatos['score'] += matches * 1000

    # Pontua os candidatos por sua popularidade
    # Apenas aqueles que já receberam alguma pontuação podem receber este boost
    mask_relevancia = candidatos['score'] > 0
    candidatos.loc[mask_relevancia, 'score'] += np.log1p(candidatos.loc[mask_relevancia, 'popularity']) * 2
    candidatos = candidatos.sort_values(by='score', ascending=False)
    
    # Output
    if not candidatos.empty:
        print(f"Top 5 Scores: \n{candidatos[['title', 'score']].head(5)}")
    return candidatos.head(5)

if __name__ == "__main__":
    print("[DEBUG] Teste da database")
    df = carregarDataframe()
    filtros_teste = {'genero': 'Qualquer Um', 'palavras_chave': ['story'], 'ano_minimo': 1990}    
    filmes_encontrados = filtrarFilmes(df, filtros_teste, verbose=True)
    print("\n[DEBUG] Resultados do Teste de Filtragem")
    if not filmes_encontrados.empty:
        print(filmes_encontrados[['title', 'year', 'overview', "keywords_list"]].head())
    else:
        print("[DEBUG] Nenhum filme encontrado com esses critérios.")