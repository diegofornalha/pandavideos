import os
import requests
import json
import re
import shutil
import time
import subprocess
from tqdm import tqdm
from dotenv import load_dotenv
from typing import Optional, List, Dict, Tuple, Any

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter a chave API do ambiente
API_KEY: Optional[str] = os.getenv('PANDA_API_KEY')
if API_KEY is None:
    raise ValueError("PANDA_API_KEY não está definida no ambiente.")

# URLs base da API do Panda Videos
BASE_URL = 'https://api-v2.pandavideo.com.br'
DOWNLOAD_URL = 'https://download-us01.pandavideo.com:7443'

# Headers para as requisições
headers = {
    'Authorization': API_KEY,  # Sem o prefixo 'Bearer'
    'Accept': 'application/json'
}

def download_with_progress(download_url: str, output_path: str, description: str) -> bool:
    """Faz download de um arquivo com barra de progresso."""
    try:
        head_response = requests.head(download_url, timeout=10)
        total_size = int(head_response.headers.get('content-length', 0))
        print(f"Tamanho total do arquivo: {total_size} bytes")
        start_time = time.time()
        
        response = requests.get(download_url, stream=True, timeout=60)
        with open(output_path, 'wb') as f, tqdm(
            desc=description,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    bytes_written = f.write(chunk)
                    bar.update(bytes_written)
        elapsed = time.time() - start_time
        print(f"\n✅ Download concluído em {elapsed:.2f} segundos")
        if total_size > 0:
            print(f"🚀 Velocidade média: {total_size/elapsed:.2f} B/s")
        return True
    except Exception as e:
        print(f"❌ Erro durante o download: {e}")
        return False

def verificar_autenticacao() -> bool:
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

def listar_pastas() -> List[Dict[str, Any]]:
    """Lista todas as pastas disponíveis na conta."""
    endpoint = f'{BASE_URL}/folders'
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        folders = data.get('folders', [])
        if folders:
            print("\n=== Pastas Disponíveis ===")
            for i, pasta in enumerate(folders, 1):
                nome = pasta.get('name', 'Sem nome')
                pasta_id = pasta.get('id', 'Sem ID')
                print(f"{i}. ID: {pasta_id} - Nome: {nome}")
        else:
            print("Nenhuma pasta encontrada na conta.")
        return folders
    except requests.exceptions.RequestException as e:
        print(f"Erro ao listar pastas: {e}")
        return []

def selecionar_pasta(pastas: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
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

def listar_videos_pasta(pasta_id: str, pasta_nome: str) -> List[Dict[str, Any]]:
    """Lista vídeos de uma pasta específica."""
    endpoint = f'{BASE_URL}/folders/{pasta_id}'
    try:
        print(f"\nListando vídeos da pasta: {pasta_nome} (ID: {pasta_id})")
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            data = response.json()
            videos = data.get('videos', [])
            if videos:
                print(f"\n=== Vídeos na Pasta {pasta_nome} ===")
                for i, video in enumerate(videos, 1):
                    duracao = video.get('duration', 'N/A')
                    titulo = video.get('title', 'Sem título')
                    print(f"{i}. ID: {video.get('id')} - Título: {titulo} - Duração: {duracao}")
                return videos
            else:
                print(f"Nenhum vídeo encontrado na pasta {pasta_nome}.")
                return obter_videos_da_pasta_alternativo(pasta_id, pasta_nome)
        else:
            print(f"Erro ao acessar a pasta: {response.status_code}")
            print(f"Resposta: {response.text}")
            print("Tentando método alternativo para listar vídeos...")
            return obter_videos_da_pasta_alternativo(pasta_id, pasta_nome)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao listar vídeos da pasta: {e}")
        return obter_videos_da_pasta_alternativo(pasta_id, pasta_nome)

def obter_videos_da_pasta_alternativo(pasta_id: str, pasta_nome: str) -> List[Dict[str, Any]]:
    """Obtém vídeos da pasta específica por método alternativo."""
    print(f"\nMétodo alternativo: obtendo vídeos da pasta {pasta_nome}")
    try:
        all_videos_endpoint = f'{BASE_URL}/videos'
        response = requests.get(all_videos_endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        all_videos = data.get('videos', [])
        videos_na_pasta = [video for video in all_videos if video.get('folder_id') == pasta_id]
        if videos_na_pasta:
            print(f"\n=== Vídeos na Pasta {pasta_nome} ===")
            for i, video in enumerate(videos_na_pasta, 1):
                duracao = video.get('duration', 'N/A')
                titulo = video.get('title', 'Sem título')
                print(f"{i}. ID: {video.get('id')} - Título: {titulo} - Duração: {duracao}")
        else:
            print(f"Nenhum vídeo encontrado na pasta {pasta_nome}.")
        return videos_na_pasta
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter vídeos: {e}")
        return []

def baixar_video_oficial(video_id: str, pasta_destino: str = 'downloads') -> bool:
    """Baixa um vídeo usando o endpoint oficial de download do Panda Videos."""
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
    info_endpoint = f'{BASE_URL}/videos/{video_id}'
    try:
        info_response = requests.get(info_endpoint, headers=headers)
        info_response.raise_for_status()
        video_info = info_response.json()
        titulo = video_info.get('title', f'video_{video_id}')
        nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)
        
        download_endpoint = f'{DOWNLOAD_URL}/videos/{video_id}/download'
        print(f"\nIniciando download oficial do vídeo: {titulo}")
        print(f"Fazendo requisição para: {download_endpoint}")
        download_response = requests.post(download_endpoint, headers=headers, timeout=30, allow_redirects=False)
        print(f"Status da resposta: {download_response.status_code}")
        
        # Caso haja redirecionamento
        if download_response.status_code in [301, 302, 303, 307, 308]:
            download_url = download_response.headers.get('Location')
            print(f"Redirecionamento detectado para: {download_url}")
            if download_url:
                return download_with_progress(download_url, caminho_completo, nome_arquivo)
            else:
                print("❌ URL de redirecionamento não encontrada nos cabeçalhos.")
                return baixar_video_alternativo(video_id, pasta_destino)
        
        elif download_response.status_code == 200:
            content_type = download_response.headers.get('Content-Type', '')
            print(f"Tipo de conteúdo: {content_type}")
            
            if 'application/json' in content_type:
                # Se a resposta for JSON, extrair URL de download
                try:
                    download_data = download_response.json()
                    download_url = download_data.get('url')
                    if download_url:
                        print("URL de download obtida, baixando o vídeo...")
                        return download_with_progress(download_url, caminho_completo, nome_arquivo)
                    else:
                        print("URL de download não encontrada na resposta.")
                        print(f"Resposta: {download_data}")
                        return baixar_video_alternativo(video_id, pasta_destino)
                except json.JSONDecodeError as e:
                    print(f"❌ Erro ao decodificar JSON da resposta: {e}")
                    return baixar_video_alternativo(video_id, pasta_destino)
            else:
                # Se a resposta já contém o arquivo, salvar diretamente
                print("🔄 A resposta contém os dados do arquivo. Salvando diretamente...")
                return download_with_progress(download_response.url, caminho_completo, nome_arquivo)
        else:
            print(f"Erro ao iniciar o download oficial: {download_response.status_code}")
            print(f"Resposta: {download_response.text}")
            print("Tentando método alternativo de download...")
            return baixar_video_alternativo(video_id, pasta_destino)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar vídeo pelo método oficial: {e}")
        print("Tentando método alternativo de download...")
        return baixar_video_alternativo(video_id, pasta_destino)

def baixar_video_alternativo(video_id: str, pasta_destino: str = 'downloads') -> bool:
    """Tenta baixar um vídeo usando métodos alternativos quando o oficial falha."""
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
    endpoint = f'{BASE_URL}/videos/{video_id}'
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        video_info = response.json()
        titulo = video_info.get('title', f'video_{video_id}')
        nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)
        
        if 'sources' in video_info and video_info['sources']:
            download_url = video_info['sources'][0].get('url')
            if download_url:
                print(f"\nBaixando via fontes diretas: {titulo}")
                return download_with_progress(download_url, caminho_completo, nome_arquivo)
            else:
                print("Link direto não disponível em 'sources'.")
        print("Tentando método m3u8...")
        if 'delivery_url' in video_info:
            return baixar_video_m3u8(video_info['delivery_url'], titulo, pasta_destino)
        else:
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

def baixar_video_m3u8(url: str, titulo: str, pasta_destino: str = 'downloads') -> bool:
    """Baixa vídeo a partir de um link m3u8."""
    print(f"Iniciando download via m3u8 para: {titulo}")
    headers_web = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://dashboard.pandavideo.com.br/',
    }
    try:
        response = requests.get(url, headers=headers_web)
        content = response.text
        if '<html' in content.lower():
            m3u8_urls = re.findall(r'https://[^"\']+\.m3u8', content)
            if not m3u8_urls:
                print("Não foi possível encontrar o link do m3u8 na página.")
                return False
            m3u8_url = m3u8_urls[0]
        else:
            m3u8_url = url
        
        response = requests.get(m3u8_url, headers=headers_web)
        m3u8_content = response.text
        
        resolucoes = re.findall(r'RESOLUTION=(\d+x\d+)', m3u8_content)
        if resolucoes:
            print("\nResoluções disponíveis:")
            for i, res in enumerate(resolucoes, 1):
                print(f"{i}. {res}")
            escolha = input("\nEscolha o número da resolução desejada (ou ENTER para a melhor qualidade): ")
            resolucao_idx = int(escolha) - 1 if escolha.strip().isdigit() and 1 <= int(escolha) <= len(resolucoes) else 0
            playlist_urls = re.findall(r'^[^#].+\.m3u8', m3u8_content, re.MULTILINE)
            if not playlist_urls:
                print("Não foi possível encontrar playlists específicas de resolução.")
                return False
            resolucao_url = playlist_urls[resolucao_idx]
            if not resolucao_url.startswith('http'):
                base_url = m3u8_url.rsplit('/', 1)[0]
                resolucao_url = f"{base_url}/{resolucao_url}"
            
            response = requests.get(resolucao_url, headers=headers_web)
            segmentos_content = response.text
            segmentos = re.findall(r'^[^#].+\.ts', segmentos_content, re.MULTILINE)
            if not segmentos:
                print("Não foi possível encontrar segmentos de vídeo.")
                return False
            
            temp_dir = os.path.join(os.getcwd(), "temp")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            base_segment_url = resolucao_url.rsplit('/', 1)[0]
            lista_segmentos_path = os.path.join(temp_dir, 'lista.txt')
            print(f"\nBaixando {len(segmentos)} segmentos...")
            with open(lista_segmentos_path, 'w') as lista_file:
                for i, segmento in enumerate(tqdm(segmentos, desc="Segmentos")):
                    segmento_url = segmento if segmento.startswith('http') else f"{base_segment_url}/{segmento}"
                    segmento_path = os.path.join(temp_dir, f"segmento_{i:04d}.ts")
                    seg_response = requests.get(segmento_url, headers=headers_web)
                    with open(segmento_path, 'wb') as seg_file:
                        seg_file.write(seg_response.content)
                    lista_file.write(f"file '{segmento_path}'\n")
            
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)
            nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
            caminho_completo = os.path.join(pasta_destino, nome_arquivo)
            
            print("\nUnindo segmentos com ffmpeg...")
            ffmpeg_cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', lista_segmentos_path,
                '-c', 'copy', caminho_completo
            ]
            result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                print(f"Download concluído: {caminho_completo}")
                shutil.rmtree(temp_dir)
                return True
            else:
                print("Erro ao unir os segmentos com ffmpeg.")
                print(f"Erro: {result.stderr.decode()}")
                return False
        else:
            print("Não foi possível identificar as resoluções disponíveis.")
            return False
    except Exception as e:
        print(f"Erro no processo de download via m3u8: {e}")
        return False

def baixar_video(video_id: str, pasta_destino: str = 'downloads') -> bool:
    """Função principal para baixar vídeo - tenta o método oficial primeiro."""
    return baixar_video_oficial(video_id, pasta_destino)

def baixar_todos_videos(videos: List[Dict[str, Any]], pasta_destino: str = 'downloads') -> None:
    """Baixa todos os vídeos da lista fornecida."""
    if not videos:
        print("Nenhum vídeo disponível para download.")
        return
    print(f"\nIniciando download de {len(videos)} vídeos...")
    for i, video in enumerate(videos, 1):
        print(f"\nBaixando vídeo {i} de {len(videos)}")
        baixar_video(video['id'], pasta_destino)
    print("\nTodos os downloads foram concluídos!")

def main() -> None:
    print("=== Downloader de Vídeos do Panda Videos ===")
    if not verificar_autenticacao():
        print("\nFalha na autenticação com a API do Panda Videos.")
        print("Por favor, verifique sua chave API e tente novamente.")
        return
    pastas = listar_pastas()
    if not pastas:
        print("\nNão foi possível listar as pastas. Verifique sua conexão e permissões.")
        return
    pasta_id, pasta_nome = selecionar_pasta(pastas)
    if not pasta_id:
        print("\nOperação cancelada pelo usuário.")
        return
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