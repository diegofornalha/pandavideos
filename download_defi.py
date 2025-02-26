import os
import requests
import json
import re
import shutil
import time
import subprocess
from tqdm import tqdm
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter a chave API do ambiente
API_KEY = os.getenv('PANDA_API_KEY')

# URLs base da API do Panda Videos
BASE_URL = 'https://api-v2.pandavideo.com.br'
DOWNLOAD_URL = 'https://download-us01.pandavideo.com:7443'

# Headers para as requisições
headers = {
    'Authorization': API_KEY,
    'Accept': 'application/json'
}

# Diretório base para downloads
BASE_DOWNLOAD_DIR = 'downloads'

def formatar_tamanho(tamanho_bytes):
    """Formata o tamanho em bytes para uma representação legível."""
    for unidade in ['B', 'KB', 'MB', 'GB']:
        if tamanho_bytes < 1024.0 or unidade == 'GB':
            break
        tamanho_bytes /= 1024.0
    return f"{tamanho_bytes:.2f} {unidade}"

def verificar_autenticacao():
    """Verifica se a autenticação com a API está funcionando corretamente."""
    endpoint = f'{BASE_URL}/videos'
    
    print(f"Testando autenticação com a chave API: {API_KEY[:10]}...")
    
    try:
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            print("✅ Autenticação bem-sucedida!")
            return True
        else:
            print(f"❌ Falha na autenticação. Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def encontrar_pasta_por_nome(nome_pasta):
    """Encontra uma pasta pelo nome."""
    endpoint = f'{BASE_URL}/folders'
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        pastas = response.json()
        
        if 'folders' in pastas:
            for pasta in pastas['folders']:
                if pasta.get('name', '').lower() == nome_pasta.lower():
                    return pasta
            
            print(f"❌ Pasta '{nome_pasta}' não encontrada.")
            return None
        else:
            print("Nenhuma pasta encontrada na conta.")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao listar pastas: {e}")
        return None

def listar_videos_pasta(pasta_id, pasta_nome):
    """Lista vídeos de uma pasta específica."""
    endpoint = f'{BASE_URL}/folders/{pasta_id}'
    
    try:
        print(f"\nListando vídeos da pasta: {pasta_nome}")
        
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        pasta_info = response.json()
        
        if 'videos' in pasta_info and pasta_info['videos']:
            print(f"\n=== Vídeos na Pasta {pasta_nome} ===")
            for i, video in enumerate(pasta_info['videos'], 1):
                duracao = video.get('duration', 'N/A')
                titulo = video.get('title', 'Sem título')
                print(f"{i}. {titulo} - Duração: {duracao}")
            
            return pasta_info['videos']
        else:
            print(f"Nenhum vídeo encontrado na pasta {pasta_nome}.")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao listar vídeos da pasta: {e}")
        return []

def verificar_video_ja_baixado(titulo, pasta_destino):
    """Verifica se o vídeo já foi baixado anteriormente."""
    nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)
    
    if os.path.exists(caminho_completo):
        tamanho = os.path.getsize(caminho_completo)
        print(f"⚠️ Vídeo '{titulo}' já existe ({formatar_tamanho(tamanho)})")
        return True
    return False

def baixar_video_m3u8(url, titulo, pasta_destino):
    """Baixa vídeo a partir de um link m3u8."""
    # Verificar se o vídeo já foi baixado
    if verificar_video_ja_baixado(titulo, pasta_destino):
        return True
    
    print(f"🔄 Iniciando download via m3u8: {titulo}")
    
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
                print("❌ Não foi possível encontrar o link do m3u8 na página.")
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
            
            # Selecionar automaticamente a melhor resolução
            resolucao_idx = 0  # Melhor qualidade (geralmente a primeira)
            print(f"✅ Selecionada automaticamente: {resolucoes[resolucao_idx]}")
            
            # Extrair a URL do m3u8 específico da resolução
            playlist_urls = re.findall(r'^[^#].+\.m3u8', m3u8_content, re.MULTILINE)
            if not playlist_urls:
                print("❌ Não foi possível encontrar playlists específicas de resolução.")
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
                print("❌ Não foi possível encontrar segmentos de vídeo.")
                return False
            
            # Criar diretório temporário
            temp_dir = os.path.join(os.getcwd(), "temp")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # Base URL para os segmentos
            base_url = resolucao_url.rsplit('/', 1)[0]
            
            # Baixar todos os segmentos
            print(f"\n🔄 Baixando {len(segmentos)} segmentos...")
            
            # Preparar arquivo de lista para ffmpeg
            with open(os.path.join(temp_dir, 'lista.txt'), 'w') as lista_file:
                # Iniciar tempo para cálculo de velocidade
                inicio_download = time.time()
                total_baixado = 0
                
                # Usar tqdm para barra de progresso
                for i, segmento in enumerate(tqdm(segmentos, desc="Progresso", unit="seg")):
                    if not segmento.startswith('http'):
                        segmento_url = f"{base_url}/{segmento}"
                    else:
                        segmento_url = segmento
                    
                    arquivo_segmento = os.path.join(temp_dir, f"segmento_{i:04d}.ts")
                    
                    # Baixar segmento
                    response = requests.get(segmento_url, headers=headers_web)
                    tamanho_segmento = len(response.content)
                    total_baixado += tamanho_segmento
                    
                    with open(arquivo_segmento, 'wb') as f:
                        f.write(response.content)
                    
                    # Adicionar à lista para o ffmpeg
                    lista_file.write(f"file '{arquivo_segmento}'\n")
                    
                    # Mostrar estatísticas a cada 10 segmentos
                    if (i + 1) % 10 == 0 or i == len(segmentos) - 1:
                        tempo_decorrido = time.time() - inicio_download
                        velocidade = total_baixado / tempo_decorrido if tempo_decorrido > 0 else 0
                        print(f"\n📊 Progresso: {i+1}/{len(segmentos)} segmentos | " 
                              f"Total: {formatar_tamanho(total_baixado)} | "
                              f"Velocidade: {formatar_tamanho(velocidade)}/s")
            
            # Criar pasta de downloads se não existir
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)
            
            # Nome do arquivo final
            nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
            caminho_completo = os.path.join(pasta_destino, nome_arquivo)
            
            # Unir os segmentos com ffmpeg
            print("\n🔄 Unindo segmentos com ffmpeg...")
            try:
                # Verificar se ffmpeg está instalado
                inicio_processamento = time.time()
                ffmpeg_cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', 
                             '-i', os.path.join(temp_dir, 'lista.txt'), 
                             '-c', 'copy', caminho_completo]
                
                result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if result.returncode == 0:
                    tempo_processamento = time.time() - inicio_processamento
                    tamanho_final = os.path.getsize(caminho_completo)
                    
                    print(f"✅ Download concluído: {caminho_completo}")
                    print(f"📊 Tamanho final: {formatar_tamanho(tamanho_final)}")
                    print(f"⏱️ Tempo de processamento: {tempo_processamento:.2f} segundos")
                    
                    # Limpar arquivos temporários
                    shutil.rmtree(temp_dir)
                    return True
                else:
                    print("❌ Erro ao unir os segmentos com ffmpeg.")
                    print(f"Erro: {result.stderr.decode()}")
                    return False
                    
            except Exception as e:
                print(f"❌ Erro ao unir os segmentos: {e}")
                print("Verifique se o ffmpeg está instalado corretamente.")
                return False
        
        else:
            print("❌ Não foi possível identificar as resoluções disponíveis.")
            return False
            
    except Exception as e:
        print(f"❌ Erro no processo de download via m3u8: {e}")
        return False

def baixar_video_alternativo(video_id, pasta_destino):
    """Tenta baixar um vídeo usando métodos alternativos."""
    # Obter informações do vídeo
    endpoint = f'{BASE_URL}/videos/{video_id}'
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        video_info = response.json()
        titulo = video_info.get('title', f'video_{video_id}')
        
        # Verificar se o vídeo já foi baixado
        if verificar_video_ja_baixado(titulo, pasta_destino):
            return True
        
        # Verificar se é possível baixar diretamente
        if 'sources' in video_info and video_info['sources']:
            # Geralmente a primeira fonte é a de melhor qualidade
            download_url = video_info['sources'][0]['url']
            
            print(f"\n🔄 Baixando via fontes diretas: {titulo}")
            
            # Nome do arquivo final
            nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
            caminho_completo = os.path.join(pasta_destino, nome_arquivo)
            
            # Fazer download do vídeo com barra de progresso
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            # Iniciar tempo para cálculo de velocidade
            inicio_download = time.time()
            bytes_baixados = 0
            
            with open(caminho_completo, 'wb') as f, tqdm(
                desc=nome_arquivo,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    tamanho = f.write(chunk)
                    bar.update(tamanho)
                    bytes_baixados += tamanho
                    
                    # Mostrar estatísticas a cada 5MB
                    if bytes_baixados % (5 * 1024 * 1024) < 8192:
                        tempo_decorrido = time.time() - inicio_download
                        velocidade = bytes_baixados / tempo_decorrido if tempo_decorrido > 0 else 0
                        print(f"\n📊 Baixado: {formatar_tamanho(bytes_baixados)}/{formatar_tamanho(total_size)} | "
                              f"Velocidade: {formatar_tamanho(velocidade)}/s")
            
            tempo_total = time.time() - inicio_download
            velocidade_media = total_size / tempo_total if tempo_total > 0 else 0
            
            print(f"✅ Download concluído: {caminho_completo}")
            print(f"📊 Tamanho: {formatar_tamanho(total_size)}")
            print(f"⏱️ Tempo total: {tempo_total:.2f} segundos")
            print(f"🚀 Velocidade média: {formatar_tamanho(velocidade_media)}/s")
            
            return True
        else:
            # Verificar se há um link de playback
            if 'delivery_url' in video_info:
                print(f"🔄 Tentando método m3u8...")
                return baixar_video_m3u8(video_info['delivery_url'], titulo, pasta_destino)
            else:
                # Tentar obter o player URL
                try:
                    player_response = requests.get(f"{BASE_URL}/videos/{video_id}/player", headers=headers)
                    if player_response.status_code == 200:
                        player_info = player_response.json()
                        if 'playerUrl' in player_info:
                            return baixar_video_m3u8(player_info['playerUrl'], titulo, pasta_destino)
                    print(f"❌ Não foi possível encontrar um link de playback para o vídeo: {video_id}")
                    return False
                except Exception as e:
                    print(f"❌ Erro ao obter player URL: {e}")
                    return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao baixar vídeo alternativo {video_id}: {e}")
        return False

def baixar_video_oficial(video_id, pasta_destino):
    """Baixa um vídeo usando o endpoint oficial de download do Panda Videos."""
    # Primeiro, obter informações do vídeo para saber o título
    info_endpoint = f'{BASE_URL}/videos/{video_id}'
    try:
        info_response = requests.get(info_endpoint, headers=headers)
        info_response.raise_for_status()
        
        video_info = info_response.json()
        titulo = video_info.get('title', f'video_{video_id}')
        
        # Verificar se o vídeo já foi baixado
        if verificar_video_ja_baixado(titulo, pasta_destino):
            return True
        
        # Usar o endpoint oficial de download
        download_endpoint = f'{DOWNLOAD_URL}/videos/{video_id}/download'
        print(f"\n🔄 Iniciando download oficial: {titulo}")
        
        # Fazer a requisição POST para iniciar o download
        download_response = requests.post(download_endpoint, headers=headers)
        
        if download_response.status_code == 200:
            # Obter a URL de download da resposta
            download_data = download_response.json()
            if 'url' in download_data:
                download_url = download_data['url']
                
                # Nome do arquivo final
                nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
                caminho_completo = os.path.join(pasta_destino, nome_arquivo)
                
                # Fazer o download do arquivo
                print(f"🔄 URL de download obtida, baixando o vídeo...")
                file_response = requests.get(download_url, stream=True)
                
                # Verificar se houve redirecionamento
                if file_response.history:
                    for resp in file_response.history:
                        if resp.status_code in [301, 302, 303, 307, 308]:
                            print(f"ℹ️ Redirecionamento detectado: {resp.status_code}")
                
                # Verificar o tipo de conteúdo
                content_type = file_response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    print("ℹ️ Resposta em JSON, tentando método alternativo...")
                    return baixar_video_alternativo(video_id, pasta_destino)
                
                total_size = int(file_response.headers.get('content-length', 0))
                
                # Iniciar tempo para cálculo de velocidade
                inicio_download = time.time()
                bytes_baixados = 0
                
                with open(caminho_completo, 'wb') as f, tqdm(
                    desc=nome_arquivo,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in file_response.iter_content(chunk_size=8192):
                        tamanho = f.write(chunk)
                        bar.update(tamanho)
                        bytes_baixados += tamanho
                        
                        # Mostrar estatísticas a cada 5MB
                        if bytes_baixados % (5 * 1024 * 1024) < 8192:
                            tempo_decorrido = time.time() - inicio_download
                            velocidade = bytes_baixados / tempo_decorrido if tempo_decorrido > 0 else 0
                            print(f"\n📊 Baixado: {formatar_tamanho(bytes_baixados)}/{formatar_tamanho(total_size)} | "
                                  f"Velocidade: {formatar_tamanho(velocidade)}/s")
                
                tempo_total = time.time() - inicio_download
                velocidade_media = total_size / tempo_total if tempo_total > 0 else 0
                
                print(f"✅ Download concluído: {caminho_completo}")
                print(f"📊 Tamanho: {formatar_tamanho(total_size)}")
                print(f"⏱️ Tempo total: {tempo_total:.2f} segundos")
                print(f"🚀 Velocidade média: {formatar_tamanho(velocidade_media)}/s")
                
                return True
            else:
                print("⚠️ URL de download não encontrada na resposta.")
                return baixar_video_alternativo(video_id, pasta_destino)
        else:
            print(f"⚠️ Erro ao iniciar o download oficial: {download_response.status_code}")
            
            # Se o download oficial falhar, tentar método alternativo
            print("🔄 Tentando método alternativo de download...")
            return baixar_video_alternativo(video_id, pasta_destino)
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao baixar vídeo pelo método oficial: {e}")
        print("🔄 Tentando método alternativo de download...")
        return baixar_video_alternativo(video_id, pasta_destino)

def baixar_video(video_id, pasta_nome):
    """Função principal para baixar vídeo - cria a pasta específica e tenta o método oficial primeiro."""
    # Criar pasta específica dentro de downloads
    pasta_destino = os.path.join(BASE_DOWNLOAD_DIR, pasta_nome)
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        print(f"📁 Pasta criada: {pasta_destino}")
    
    return baixar_video_oficial(video_id, pasta_destino)

def baixar_todos_videos(videos, pasta_nome):
    """Baixa todos os vídeos da lista fornecida, verificando quais já foram baixados."""
    if not videos:
        print("⚠️ Nenhum vídeo disponível para download.")
        return
    
    # Criar pasta específica dentro de downloads
    pasta_destino = os.path.join(BASE_DOWNLOAD_DIR, pasta_nome)
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        print(f"📁 Pasta criada: {pasta_destino}")
    
    print(f"\n🔄 Iniciando verificação de {len(videos)} vídeos...")
    
    # Verificar quais vídeos já foram baixados
    videos_para_baixar = []
    for video in videos:
        titulo = video.get('title', f"video_{video['id']}")
        if not verificar_video_ja_baixado(titulo, pasta_destino):
            videos_para_baixar.append(video)
    
    if not videos_para_baixar:
        print("✅ Todos os vídeos já foram baixados anteriormente!")
        return
    
    print(f"\n🔄 Iniciando download de {len(videos_para_baixar)} vídeos pendentes...")
    
    for i, video in enumerate(videos_para_baixar, 1):
        print(f"\n🔄 Baixando vídeo {i} de {len(videos_para_baixar)}")
        baixar_video_oficial(video['id'], pasta_destino)
    
    print("\n✅ Todos os downloads foram concluídos!")

def main():
    """Função principal para baixar todos os vídeos da pasta DeFi."""
    print("=== 🎬 Downloader de Vídeos do Panda Videos - Pasta DeFi ===")
    
    # Verificar autenticação antes de continuar
    if not verificar_autenticacao():
        print("\n❌ Falha na autenticação com a API do Panda Videos.")
        print("Por favor, verifique sua chave API e tente novamente.")
        return
    
    # Encontrar a pasta DeFi
    pasta_defi = encontrar_pasta_por_nome("DeFi")
    
    if not pasta_defi:
        print("\n❌ Pasta 'DeFi' não encontrada. Verifique se o nome está correto.")
        return
    
    pasta_id = pasta_defi.get('id')
    pasta_nome = pasta_defi.get('name', 'DeFi')
    
    print(f"\n✅ Pasta encontrada: {pasta_nome} (ID: {pasta_id})")
    
    # Listar vídeos da pasta DeFi
    videos = listar_videos_pasta(pasta_id, pasta_nome)
    
    if not videos:
        print("\n❌ Nenhum vídeo encontrado na pasta DeFi.")
        return
    
    # Baixar todos os vídeos
    baixar_todos_videos(videos, pasta_nome)

if __name__ == "__main__":
    main() 