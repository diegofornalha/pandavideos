import os
import requests
import json
import re
import shutil
import time
from tqdm import tqdm
from dotenv import load_dotenv
import subprocess

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter a chave API do ambiente
API_KEY = os.getenv('PANDA_API_KEY')

# URLs base da API do Panda Videos
BASE_URL = 'https://api-v2.pandavideo.com.br'
DOWNLOAD_URL = 'https://download-us01.pandavideo.com:7443'

# Headers para as requisições
headers = {
    'Authorization': API_KEY,  # Sem o prefixo 'Bearer'
    'Accept': 'application/json'
}

def verificar_autenticacao():
    """Verifica se a autenticação com a API está funcionando corretamente."""
    endpoint = f'{BASE_URL}/videos'
    
    print(f"Testando autenticação com a chave API: {API_KEY[:10]}...")
    
    try:
        response = requests.get(endpoint, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Autenticação bem-sucedida!")
            return True
        else:
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"Erro: {e}")
        return False

def listar_pastas():
    """Lista todas as pastas disponíveis na conta."""
    endpoint = f'{BASE_URL}/folders'
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        pastas = response.json()
        
        if 'folders' in pastas:
            print("\n=== Pastas Disponíveis ===")
            for i, pasta in enumerate(pastas['folders'], 1):
                nome = pasta.get('name', 'Sem nome')
                pasta_id = pasta.get('id', 'Sem ID')
                print(f"{i}. ID: {pasta_id} - Nome: {nome}")
            
            return pastas['folders']
        else:
            print("Nenhuma pasta encontrada na conta.")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Erro ao listar pastas: {e}")
        return []

def selecionar_pasta(pastas):
    """Permite ao usuário selecionar uma pasta da lista."""
    if not pastas:
        print("Não há pastas disponíveis para seleção.")
        return None, None
    
    while True:
        escolha = input("\nDigite o número da pasta que deseja acessar (ou 'q' para sair): ")
        
        if escolha.lower() == 'q':
            return None, None
        
        try:
            indice = int(escolha) - 1
            if 0 <= indice < len(pastas):
                pasta_id = pastas[indice].get('id')
                pasta_nome = pastas[indice].get('name', 'Sem nome')
                print(f"\nPasta selecionada: {pasta_nome} (ID: {pasta_id})")
                return pasta_id, pasta_nome
            else:
                print("Número inválido. Por favor, tente novamente.")
        except ValueError:
            print("Entrada inválida. Digite um número ou 'q' para sair.")

def listar_videos_pasta(pasta_id, pasta_nome):
    """Lista vídeos de uma pasta específica."""
    endpoint = f'{BASE_URL}/folders/{pasta_id}'
    
    try:
        print(f"\nListando vídeos da pasta: {pasta_nome} (ID: {pasta_id})")
        
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            pasta_info = response.json()
            
            if 'videos' in pasta_info and pasta_info['videos']:
                print(f"\n=== Vídeos na Pasta {pasta_nome} ===")
                for i, video in enumerate(pasta_info['videos'], 1):
                    duracao = video.get('duration', 'N/A')
                    titulo = video.get('title', 'Sem título')
                    print(f"{i}. ID: {video['id']} - Título: {titulo} - Duração: {duracao}")
                
                return pasta_info['videos']
            else:
                print(f"Nenhum vídeo encontrado na pasta {pasta_nome}.")
                return obter_videos_da_pasta_alternativo(pasta_id, pasta_nome)
        else:
            print(f"Erro ao acessar a pasta: {response.status_code}")
            print(f"Resposta: {response.text}")
            
            # Tentar método alternativo
            print("Tentando método alternativo para listar vídeos...")
            return obter_videos_da_pasta_alternativo(pasta_id, pasta_nome)
            
    except requests.exceptions.RequestException as e:
        print(f"Erro ao listar vídeos da pasta: {e}")
        return obter_videos_da_pasta_alternativo(pasta_id, pasta_nome)

def obter_videos_da_pasta_alternativo(pasta_id, pasta_nome):
    """Obtém vídeos da pasta específica por método alternativo."""
    print(f"\nMétodo alternativo: obtendo vídeos da pasta {pasta_nome}")
    
    # Método alternativo: obter todos os vídeos e filtrar pela pasta
    try:
        # Obter todos os vídeos
        all_videos_endpoint = f'{BASE_URL}/videos'
        response = requests.get(all_videos_endpoint, headers=headers)
        response.raise_for_status()
        
        all_videos = response.json()
        
        if 'videos' not in all_videos:
            print("Nenhum vídeo encontrado na conta.")
            return []
        
        # Filtrar vídeos por pasta
        videos_na_pasta = []
        for video in all_videos['videos']:
            if video.get('folder_id') == pasta_id:
                videos_na_pasta.append(video)
        
        if videos_na_pasta:
            print(f"\n=== Vídeos na Pasta {pasta_nome} ===")
            for i, video in enumerate(videos_na_pasta, 1):
                duracao = video.get('duration', 'N/A')
                titulo = video.get('title', 'Sem título')
                print(f"{i}. ID: {video['id']} - Título: {titulo} - Duração: {duracao}")
            
            return videos_na_pasta
        else:
            print(f"Nenhum vídeo encontrado na pasta {pasta_nome}.")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter vídeos: {e}")
        return []

def baixar_video_oficial(video_id, pasta_destino='downloads'):
    """Baixa um vídeo usando o endpoint oficial de download do Panda Videos."""
    # Criar pasta de downloads se não existir
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
    
    # Primeiro, obter informações do vídeo para saber o título
    info_endpoint = f'{BASE_URL}/videos/{video_id}'
    try:
        info_response = requests.get(info_endpoint, headers=headers)
        info_response.raise_for_status()
        
        video_info = info_response.json()
        titulo = video_info.get('title', f'video_{video_id}')
        nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)
        
        # Usar o endpoint oficial de download
        download_endpoint = f'{DOWNLOAD_URL}/videos/{video_id}/download'
        print(f"\nIniciando download oficial do vídeo: {titulo}")
        
        # Fazer a requisição POST para iniciar o download
        download_response = requests.post(download_endpoint, headers=headers)
        
        if download_response.status_code == 200:
            # Obter a URL de download da resposta
            download_data = download_response.json()
            if 'url' in download_data:
                download_url = download_data['url']
                
                # Fazer o download do arquivo
                print(f"URL de download obtida, baixando o vídeo...")
                file_response = requests.get(download_url, stream=True)
                total_size = int(file_response.headers.get('content-length', 0))
                
                with open(caminho_completo, 'wb') as f, tqdm(
                    desc=nome_arquivo,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in file_response.iter_content(chunk_size=1024):
                        size = f.write(chunk)
                        bar.update(size)
                
                print(f"Download concluído: {caminho_completo}")
                return True
            else:
                print("URL de download não encontrada na resposta.")
                print(f"Resposta: {download_data}")
                return baixar_video_alternativo(video_id, pasta_destino)
        else:
            print(f"Erro ao iniciar o download oficial: {download_response.status_code}")
            print(f"Resposta: {download_response.text}")
            
            # Se o download oficial falhar, tentar método alternativo
            print("Tentando método alternativo de download...")
            return baixar_video_alternativo(video_id, pasta_destino)
    
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar vídeo pelo método oficial: {e}")
        print("Tentando método alternativo de download...")
        return baixar_video_alternativo(video_id, pasta_destino)

def baixar_video_alternativo(video_id, pasta_destino='downloads'):
    """Tenta baixar um vídeo usando métodos alternativos quando o oficial falha."""
    # Criar pasta de downloads se não existir
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
    
    # Obter informações do vídeo
    endpoint = f'{BASE_URL}/videos/{video_id}'
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        video_info = response.json()
        
        titulo = video_info.get('title', f'video_{video_id}')
        nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)
        
        # Verificar se é possível baixar diretamente
        if 'sources' in video_info and video_info['sources']:
            # Geralmente a primeira fonte é a de melhor qualidade
            download_url = video_info['sources'][0]['url']
            
            print(f"\nBaixando via fontes diretas: {titulo}")
            
            # Fazer download do vídeo com barra de progresso
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(caminho_completo, 'wb') as f, tqdm(
                desc=nome_arquivo,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=1024):
                    size = f.write(chunk)
                    bar.update(size)
            
            print(f"Download concluído: {caminho_completo}")
            return True
        else:
            print(f"Não foi possível encontrar o link de download direto para o vídeo.")
            
            # Verificar se há um link de playback
            if 'delivery_url' in video_info:
                print(f"Tentando método m3u8...")
                return baixar_video_m3u8(video_info['delivery_url'], titulo, pasta_destino)
            else:
                # Tentar obter o player URL
                try:
                    player_response = requests.get(f"{BASE_URL}/videos/{video_id}/player", headers=headers)
                    if player_response.status_code == 200:
                        player_info = player_response.json()
                        if 'playerUrl' in player_info:
                            return baixar_video_m3u8(player_info['playerUrl'], titulo, pasta_destino)
                    print(f"Não foi possível encontrar um link de playback para o vídeo: {video_id}")
                    return False
                except Exception as e:
                    print(f"Erro ao obter player URL: {e}")
                    return False
    
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar vídeo alternativo {video_id}: {e}")
        return False

def baixar_video_m3u8(url, titulo, pasta_destino='downloads'):
    """Baixa vídeo a partir de um link m3u8."""
    print(f"Iniciando download via m3u8 para: {titulo}")
    
    # URL pode ser do player - precisamos extrair o link do m3u8
    try:
        headers_web = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://dashboard.pandavideo.com.br/',
        }
        
        # Tentar obter o conteúdo da página ou do m3u8
        response = requests.get(url, headers=headers_web)
        content = response.text
        
        # Se é uma página HTML, procurar pelo link do m3u8
        if '<html' in content.lower():
            m3u8_urls = re.findall(r'https://[^"\']+\.m3u8', content)
            if not m3u8_urls:
                print("Não foi possível encontrar o link do m3u8 na página.")
                return False
            m3u8_url = m3u8_urls[0]
        else:
            # Se já é um m3u8, usar diretamente
            m3u8_url = url
        
        # Obter o conteúdo do m3u8
        response = requests.get(m3u8_url, headers=headers_web)
        m3u8_content = response.text
        
        # Identificar as resoluções disponíveis
        resolucoes = re.findall(r'RESOLUTION=(\d+x\d+)', m3u8_content)
        if resolucoes:
            print("\nResoluções disponíveis:")
            for i, res in enumerate(resolucoes, 1):
                print(f"{i}. {res}")
            
            escolha = input("\nEscolha o número da resolução desejada (ou ENTER para a melhor qualidade): ")
            if escolha.strip() and escolha.isdigit() and 1 <= int(escolha) <= len(resolucoes):
                resolucao_idx = int(escolha) - 1
            else:
                resolucao_idx = 0  # Melhor qualidade (geralmente a primeira)
            
            # Extrair a URL do m3u8 específico da resolução
            playlist_urls = re.findall(r'^[^#].+\.m3u8', m3u8_content, re.MULTILINE)
            if not playlist_urls:
                print("Não foi possível encontrar playlists específicas de resolução.")
                return False
                
            resolucao_url = playlist_urls[resolucao_idx]
            if not resolucao_url.startswith('http'):
                # URL relativa - precisa construir a URL completa
                base_url = m3u8_url.rsplit('/', 1)[0]
                resolucao_url = f"{base_url}/{resolucao_url}"
            
            # Obter os segmentos de vídeo
            response = requests.get(resolucao_url, headers=headers_web)
            segmentos_content = response.text
            
            # Extrair os segmentos
            segmentos = re.findall(r'^[^#].+\.ts', segmentos_content, re.MULTILINE)
            if not segmentos:
                print("Não foi possível encontrar segmentos de vídeo.")
                return False
            
            # Criar diretório temporário
            temp_dir = os.path.join(os.getcwd(), "temp")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # Base URL para os segmentos
            base_url = resolucao_url.rsplit('/', 1)[0]
            
            # Baixar todos os segmentos
            print(f"\nBaixando {len(segmentos)} segmentos...")
            with open(os.path.join(temp_dir, 'lista.txt'), 'w') as lista_file:
                for i, segmento in enumerate(tqdm(segmentos)):
                    if not segmento.startswith('http'):
                        segmento_url = f"{base_url}/{segmento}"
                    else:
                        segmento_url = segmento
                    
                    arquivo_segmento = os.path.join(temp_dir, f"segmento_{i:04d}.ts")
                    
                    # Baixar segmento
                    response = requests.get(segmento_url, headers=headers_web)
                    with open(arquivo_segmento, 'wb') as f:
                        f.write(response.content)
                    
                    # Adicionar à lista para o ffmpeg
                    lista_file.write(f"file '{arquivo_segmento}'\n")
            
            # Criar pasta de downloads se não existir
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)
            
            # Nome do arquivo final
            nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
            caminho_completo = os.path.join(pasta_destino, nome_arquivo)
            
            # Unir os segmentos com ffmpeg
            print("\nUnindo segmentos com ffmpeg...")
            try:
                # Verificar se ffmpeg está instalado
                ffmpeg_cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', 
                             '-i', os.path.join(temp_dir, 'lista.txt'), 
                             '-c', 'copy', caminho_completo]
                
                result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if result.returncode == 0:
                    print(f"Download concluído: {caminho_completo}")
                    # Limpar arquivos temporários
                    shutil.rmtree(temp_dir)
                    return True
                else:
                    print("Erro ao unir os segmentos com ffmpeg.")
                    print(f"Erro: {result.stderr.decode()}")
                    return False
                    
            except Exception as e:
                print(f"Erro ao unir os segmentos: {e}")
                print("Verifique se o ffmpeg está instalado corretamente.")
                return False
        
        else:
            print("Não foi possível identificar as resoluções disponíveis.")
            return False
            
    except Exception as e:
        print(f"Erro no processo de download via m3u8: {e}")
        return False

def baixar_video(video_id, pasta_destino='downloads'):
    """Função principal para baixar vídeo - tenta o método oficial primeiro."""
    return baixar_video_oficial(video_id, pasta_destino)

def baixar_todos_videos(videos):
    """Baixa todos os vídeos da lista fornecida."""
    if not videos:
        print("Nenhum vídeo disponível para download.")
        return
    
    print(f"\nIniciando download de {len(videos)} vídeos...")
    
    for i, video in enumerate(videos, 1):
        print(f"\nBaixando vídeo {i} de {len(videos)}")
        baixar_video(video['id'])
    
    print("\nTodos os downloads foram concluídos!")

def main():
    print("=== Downloader de Vídeos do Panda Videos ===")
    
    # Verificar autenticação antes de continuar
    if not verificar_autenticacao():
        print("\nFalha na autenticação com a API do Panda Videos.")
        print("Por favor, verifique sua chave API e tente novamente.")
        return
    
    # Listar pastas disponíveis
    pastas = listar_pastas()
    
    if not pastas:
        print("\nNão foi possível listar as pastas. Verifique sua conexão e permissões.")
        return
    
    # Selecionar uma pasta
    pasta_id, pasta_nome = selecionar_pasta(pastas)
    
    if not pasta_id:
        print("\nOperação cancelada pelo usuário.")
        return
    
    # Listar vídeos da pasta selecionada
    videos = listar_videos_pasta(pasta_id, pasta_nome)
    
    if not videos:
        return
    
    print("\nOpções:")
    print("1. Baixar um vídeo específico")
    print("2. Baixar todos os vídeos da pasta")
    
    opcao = input("\nEscolha uma opção (1 ou 2): ")
    
    if opcao == '1':
        while True:
            escolha = input("\nDigite o número do vídeo que deseja baixar (ou 'q' para sair): ")
            
            if escolha.lower() == 'q':
                break
            
            try:
                indice = int(escolha) - 1
                if 0 <= indice < len(videos):
                    video_id = videos[indice]['id']
                    baixar_video(video_id)
                else:
                    print("Número inválido. Por favor, tente novamente.")
            except ValueError:
                print("Entrada inválida. Digite um número ou 'q' para sair.")
    
    elif opcao == '2':
        baixar_todos_videos(videos)
    
    else:
        print("Opção inválida!")

if __name__ == "__main__":
    main() 