#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para baixar todos os vídeos de uma pasta específica do Panda Video,
incluindo suporte para subpastas de forma recursiva.
Autor: Claude | Data: 2023
"""

import os
import time
import requests
import sys
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações
FOLDER_ID_PRINCIPAL = "9efa86d7-ea1c-40cd-b445-094c53677846"
API_KEY = os.getenv('PANDA_API_KEY')
# Alterado para pasta downloads
OUTPUT_DIR = os.path.join(os.getcwd(), "downloads")  
# Subpasta de foco
FOCO_SUBPASTA = "Acelerador Cripto"  
# Nível máximo de subpastas para evitar recursão infinita
MAX_NIVEL_RECURSAO = 10  

# Verifica se a chave API existe
if not API_KEY:
    API_KEY = input("Por favor, insira sua chave API do Panda Video: ")

# Cria o diretório de saída se não existir
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cabeçalhos para requisições
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}


def listar_subpastas(folder_id):
    """
    Lista todas as subpastas de uma pasta específica
    """
    url = f"https://api.pandavideo.com.br/v2/folders/{folder_id}/folders"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        subpastas = response.json()
        return subpastas
    except requests.exceptions.RequestException as e:
        print(f"Erro ao listar subpastas: {e}")
        return []


def listar_videos_na_pasta(folder_id):
    """
    Lista todos os vídeos na pasta especificada
    """
    url = f"https://api.pandavideo.com.br/v2/folders/{folder_id}/videos"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        videos = response.json()
        print(f"Encontrados {len(videos)} vídeos na pasta.")
        return videos
    except requests.exceptions.RequestException as e:
        print(f"Erro ao listar vídeos: {e}")
        return []


def baixar_video(video_id, titulo, caminho_pasta=None):
    """
    Inicia e acompanha o download de um vídeo específico
    """
    download_url = (
        f"https://download-us01.pandavideo.com:7443/videos/{video_id}/download"
    )
    
    # Define o diretório de saída (padrão ou específico da subpasta)
    saida = OUTPUT_DIR
    if caminho_pasta:
        saida = os.path.join(OUTPUT_DIR, caminho_pasta)
        # Cria toda a estrutura de pastas se não existir
        os.makedirs(saida, exist_ok=True)
    
    try:
        print(f"Iniciando download de: {titulo}")
        
        # Inicia o download
        response = requests.post(download_url, headers=headers)
        response.raise_for_status()
        
        # Verifica se há um URL de download na resposta
        download_data = response.json()
        
        if "url" in download_data:
            # Download direto do arquivo
            video_response = requests.get(download_data["url"], stream=True)
            video_response.raise_for_status()
            
            # Sanitiza o nome do arquivo
            safe_titulo = "".join(
                c for c in titulo if c.isalnum() or c in (' ', '.', '_', '-')
            ).rstrip()
            filename = f"{safe_titulo}_{video_id}.mp4"
            filepath = os.path.join(saida, filename)
            
            # Verifica se o arquivo já existe
            if os.path.exists(filepath):
                print(f"\nO arquivo já existe: {filename}")
                return True
                
            # Download com progresso
            total_size = int(video_response.headers.get('content-length', 0))
            block_size = 1024  # 1 Kibibyte
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for data in video_response.iter_content(block_size):
                    f.write(data)
                    downloaded += len(data)
                    # Mostra progresso
                    done = int(50 * downloaded / total_size)
                    print(
                        f"\r[{'=' * done}{' ' * (50-done)}] "
                        f"{downloaded/total_size*100:.2f}%", 
                        end=''
                    )
            
            print(f"\nVídeo baixado com sucesso: {filename}")
            print(f"Salvo em: {saida}")
            return True
        else:
            print(
                f"Não foi possível obter o URL de download para o vídeo: "
                f"{video_id}"
            )
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar vídeo {video_id}: {e}")
        return False


def processar_pasta_recursivamente(folder_id, caminho_atual="", nivel=0):
    """
    Processa uma pasta e suas subpastas de forma recursiva
    """
    # Evita recursão infinita
    if nivel > MAX_NIVEL_RECURSAO:
        print(f"Atingido nível máximo de recursão ({MAX_NIVEL_RECURSAO})")
        return 0, 0, 0
    
    # Obtém informações da pasta atual (para obter o nome)
    pasta_info = None
    if nivel > 0:  # Não precisamos fazer isso para a pasta raiz
        url = f"https://api.pandavideo.com.br/v2/folders/{folder_id}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            pasta_info = response.json()
        except Exception:
            # Se falhar em obter o nome, usamos o ID
            pasta_info = {"name": folder_id}
    
    # Define o nome da pasta atual
    nome_pasta = pasta_info.get("name", folder_id) if pasta_info else "raiz"
    
    # Define o caminho completo
    if caminho_atual:
        caminho_completo = os.path.join(caminho_atual, nome_pasta)
    else:
        caminho_completo = nome_pasta
    
    # Exibe informação sobre a pasta sendo processada
    identacao = "  " * nivel
    print(f"\n{identacao}=== Processando pasta: {nome_pasta} ===")
    print(f"{identacao}Caminho: {caminho_completo}")
    
    # Primeiro processa os vídeos nesta pasta
    baixados_pasta = 0
    falhas_pasta = 0
    total_pasta = 0
    
    videos = listar_videos_na_pasta(folder_id)
    total_videos = len(videos)
    
    for i, video in enumerate(videos, 1):
        video_titulo = video.get('name', 'Sem título')
        print(
            f"{identacao}[{i}/{total_videos}] Processando vídeo: {video_titulo}"
        )
        
        sucesso = baixar_video(
            video.get('id'), 
            video_titulo,
            caminho_completo
        )
        
        if sucesso:
            baixados_pasta += 1
        else:
            falhas_pasta += 1
        
        # Aguarda um pouco entre os downloads
        if i < total_videos:
            print(f"{identacao}Aguardando 2 segundos antes do próximo vídeo...")
            time.sleep(2)
    
    total_pasta = total_videos
    
    # Agora processa as subpastas
    subpastas = listar_subpastas(folder_id)
    
    baixados_subpastas = 0
    falhas_subpastas = 0
    total_subpastas = 0
    
    for subpasta in subpastas:
        subpasta_id = subpasta.get('id')
        
        # Chamada recursiva para processar subpasta
        baixados_sub, falhas_sub, total_sub = processar_pasta_recursivamente(
            subpasta_id, 
            caminho_completo,
            nivel + 1
        )
        
        baixados_subpastas += baixados_sub
        falhas_subpastas += falhas_sub
        total_subpastas += total_sub
        
        # Pausa entre subpastas
        print(f"{identacao}Aguardando 3 segundos antes da próxima subpasta...")
        time.sleep(3)
    
    # Soma os resultados desta pasta e suas subpastas
    total_baixados = baixados_pasta + baixados_subpastas
    total_falhas = falhas_pasta + falhas_subpastas
    total_geral = total_pasta + total_subpastas
    
    # Exibe relatório para esta pasta
    print(f"\n{identacao}=== Resumo da pasta {nome_pasta} ===")
    print(f"{identacao}Vídeos nesta pasta: {total_pasta}")
    print(f"{identacao}Vídeos em subpastas: {total_subpastas}")
    print(f"{identacao}Total de vídeos: {total_geral}")
    print(f"{identacao}Baixados com sucesso: {total_baixados}")
    print(f"{identacao}Falhas: {total_falhas}")
    
    return total_baixados, total_falhas, total_geral


def focar_pasta_acelerador_cripto():
    """
    Encontra e processa primeiro a pasta 'Acelerador Cripto'
    """
    subpastas = listar_subpastas(FOLDER_ID_PRINCIPAL)
    
    for pasta in subpastas:
        pasta_nome = pasta.get('name', '')
        
        if FOCO_SUBPASTA.lower() in pasta_nome.lower():
            pasta_id = pasta.get('id')
            print(f"\n>>> PROCESSANDO PASTA PRIORITÁRIA: {pasta_nome} <<<")
            
            return processar_pasta_recursivamente(pasta_id, "")
    
    print(f"Pasta '{FOCO_SUBPASTA}' não encontrada.")
    return 0, 0, 0


def main():
    """
    Função principal que coordena o download de todos os vídeos
    """
    print(f"=== Download de Vídeos do Panda Video para {OUTPUT_DIR} ===")
    print("Os vídeos serão organizados mantendo a estrutura de pastas original")
    
    # Primeiro processa a pasta de foco
    baixados_foco, falhas_foco, total_foco = focar_pasta_acelerador_cripto()
    
    # Depois processa a pasta principal para garantir todas as subpastas
    print("\nIniciando processamento completo da pasta principal...")
    baixados_total, falhas_total, total_geral = processar_pasta_recursivamente(
        FOLDER_ID_PRINCIPAL
    )
    
    print("\n=== Resumo Geral ===")
    print(f"Total de vídeos processados: {total_geral}")
    print(f"Baixados com sucesso: {baixados_total}")
    print(f"Falhas: {falhas_total}")
    print(f"Os vídeos foram salvos em: {OUTPUT_DIR}")
    print("Mantendo a estrutura de pastas original do Panda Video")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nErro não esperado: {e}")
        sys.exit(1) 