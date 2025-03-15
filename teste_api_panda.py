#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a conexão com a API do Panda Video
com suporte a múltiplas tentativas
"""

import os
import time
import requests
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações
FOLDER_ID = "9efa86d7-ea1c-40cd-b445-094c53677846"
API_KEY = os.getenv('PANDA_API_KEY')
MAX_TENTATIVAS = 3
TEMPO_ESPERA = 3  # segundos

print(f"Testando API com a chave: {API_KEY[:10]}...")

# Cabeçalhos para requisições
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}


def fazer_requisicao(url, metodo="GET", dados=None, tentativas=MAX_TENTATIVAS):
    """
    Faz uma requisição à API com suporte a múltiplas tentativas
    """
    for tentativa in range(1, tentativas + 1):
        try:
            if metodo.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif metodo.upper() == "POST":
                response = requests.post(
                    url, headers=headers, json=dados, timeout=30
                )
            else:
                return None, f"Método {metodo} não suportado"
                
            response.raise_for_status()
            return response.json(), None
            
        except requests.exceptions.RequestException as e:
            erro = f"Tentativa {tentativa}/{tentativas}: {e}"
            print(f"⚠️ {erro}")
            
            if tentativa < tentativas:
                tempo = TEMPO_ESPERA * tentativa
                print(f"Aguardando {tempo} segundos para tentar novamente...")
                time.sleep(tempo)
            
    return None, f"Falha após {tentativas} tentativas"


def testar_listar_pastas():
    """Testa a listagem de pastas"""
    url = f"https://api.pandavideo.com.br/v2/folders/{FOLDER_ID}/folders"
    
    print(f"\nTentando listar subpastas da pasta: {FOLDER_ID}")
    pastas, erro = fazer_requisicao(url)
    
    if erro:
        print(f"❌ Erro ao listar pastas: {erro}")
        return False
    
    print(f"✅ Sucesso! Encontradas {len(pastas)} pastas.")
    
    if pastas:
        print("\nPrimeiras 5 pastas encontradas:")
        for i, pasta in enumerate(pastas[:5], 1):
            print(
                f"  {i}. {pasta.get('name', 'Sem nome')} "
                f"(ID: {pasta.get('id')})"
            )
    
    return True


def testar_listar_videos():
    """Testa a listagem de vídeos"""
    url = f"https://api.pandavideo.com.br/v2/folders/{FOLDER_ID}/videos"
    
    print(f"\nTentando listar vídeos da pasta: {FOLDER_ID}")
    videos, erro = fazer_requisicao(url)
    
    if erro:
        print(f"❌ Erro ao listar vídeos: {erro}")
        return False
    
    print(f"✅ Sucesso! Encontrados {len(videos)} vídeos.")
    
    if videos:
        print("\nPrimeiros 5 vídeos encontrados:")
        for i, video in enumerate(videos[:5], 1):
            print(
                f"  {i}. {video.get('name', 'Sem título')} "
                f"(ID: {video.get('id')})"
            )
    
    return True


def testar_info_conta():
    """Testa obter informações da conta"""
    url = "https://api.pandavideo.com.br/v2/account"
    
    print("\nTentando obter informações da conta")
    info, erro = fazer_requisicao(url)
    
    if erro:
        print(f"❌ Erro ao obter informações da conta: {erro}")
        return False
    
    print(f"✅ Sucesso! Conta: {info.get('name', 'Nome não disponível')}")
    return True


if __name__ == "__main__":
    print("=== Teste de Conexão com a API do Panda Video ===\n")
    
    # Testa informações da conta
    conta_ok = testar_info_conta()
    
    # Testa listar pastas
    pastas_ok = testar_listar_pastas()
    
    # Testa listar vídeos
    videos_ok = testar_listar_videos()
    
    # Resultado final
    print("\n=== Resultado Final ===")
    print(f"Informações da conta: {'✅ OK' if conta_ok else '❌ Falhou'}")
    print(f"Listar pastas: {'✅ OK' if pastas_ok else '❌ Falhou'}")
    print(f"Listar vídeos: {'✅ OK' if videos_ok else '❌ Falhou'}")
    
    if conta_ok and pastas_ok and videos_ok:
        print("\n✅✅✅ A API está funcionando corretamente! ✅✅✅")
    else:
        print(
            "\n❌❌❌ Há problemas com a API. Verifique os erros acima. ❌❌❌"
        ) 