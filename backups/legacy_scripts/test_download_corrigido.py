import os
import requests
import time
import json
import argparse
import sys
from tqdm import tqdm

# Definições de URLs e Headers
BASE_URL = 'https://api-v2.pandavideo.com.br'
DOWNLOAD_URL = 'https://download-us01.pandavideo.com:7443'
API_KEY = os.getenv('PANDA_API_KEY', 'panda-59e2')

# Headers para as requisições
headers = {
    'Authorization': API_KEY,
    'Accept': 'application/json'
}

# Função para formatar tamanho em bytes para formato legível
def formatar_tamanho(tamanho_bytes):
    for unidade in ['B', 'KB', 'MB', 'GB']:
        if tamanho_bytes < 1024.0:
            return f"{tamanho_bytes:.2f} {unidade}"
        tamanho_bytes /= 1024.0
    return f"{tamanho_bytes:.2f} TB"

def verificar_video_ja_baixado(titulo, pasta_destino):
    """Verifica se o vídeo já foi baixado anteriormente."""
    nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)
    
    if os.path.exists(caminho_completo):
        tamanho = os.path.getsize(caminho_completo)
        print(f"⚠️ Vídeo '{titulo}' já existe ({formatar_tamanho(tamanho)})")
        return True
    return False

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

def encontrar_pasta_por_id(pasta_id):
    """Encontra uma pasta pelo ID."""
    endpoint = f'{BASE_URL}/folders'
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        pastas = response.json()
        
        if 'folders' in pastas:
            for pasta in pastas['folders']:
                if pasta.get('id', '') == pasta_id:
                    return pasta
            
            print(f"❌ Pasta com ID '{pasta_id}' não encontrada.")
            return None
        else:
            print("Nenhuma pasta encontrada na conta.")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao listar pastas: {e}")
        return None

def listar_pastas():
    """Lista todas as pastas disponíveis."""
    endpoint = f'{BASE_URL}/folders'
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        pastas = response.json()
        
        if 'folders' in pastas and pastas['folders']:
            print("\n=== Pastas Disponíveis ===")
            for i, pasta in enumerate(pastas['folders'], 1):
                nome = pasta.get('name', 'Sem nome')
                pasta_id = pasta.get('id', 'Sem ID')
                print(f"{i}. {nome} (ID: {pasta_id})")
            return pastas['folders']
        else:
            print("Nenhuma pasta encontrada.")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao listar pastas: {e}")
        return []

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

def download_with_progress(download_url, caminho_completo, nome_arquivo):
    """
    Faz download do arquivo a partir da URL com barra de progresso.
    """
    try:
        # Obter tamanho do arquivo
        head_response = requests.head(download_url, timeout=10)
        total_size = int(head_response.headers.get('content-length', 0))
        print(f"Tamanho total do arquivo: {formatar_tamanho(total_size)}")
        
        inicio = time.time()
        file_response = requests.get(download_url, stream=True, timeout=60)
        
        with open(caminho_completo, 'wb') as f, tqdm(
            desc=f"Baixando {nome_arquivo}",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        ) as bar:
            for chunk in file_response.iter_content(chunk_size=8192):
                if chunk:
                    tamanho_escrito = f.write(chunk)
                    bar.update(tamanho_escrito)
        
        tempo_total = time.time() - inicio
        print(f"\n✅ Download concluído em {tempo_total:.2f} segundos")
        if total_size > 0:
            print(f"🚀 Velocidade média: {formatar_tamanho(total_size/tempo_total)}/s")
        return True
    except Exception as e:
        print(f"❌ Erro durante o download: {e}")
        return False

def save_response_stream(response, caminho_completo, nome_arquivo):
    """
    Salva o stream de uma resposta que já contém os dados do arquivo.
    """
    try:
        total_size = int(response.headers.get('content-length', 0))
        print(f"Tamanho total do arquivo: {formatar_tamanho(total_size)}")
        
        inicio = time.time()
        
        with open(caminho_completo, 'wb') as f, tqdm(
            desc=f"Baixando {nome_arquivo}",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tamanho_escrito = f.write(chunk)
                    bar.update(tamanho_escrito)
            
        tempo_total = time.time() - inicio
        print(f"\n✅ Download concluído em {tempo_total:.2f} segundos")
        if total_size > 0:
            print(f"🚀 Velocidade média: {formatar_tamanho(total_size/tempo_total)}/s")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar o arquivo: {e}")
        return False

def baixar_video_alternativo(video_id, pasta_destino):
    """Tenta baixar um vídeo usando métodos alternativos quando o oficial falha."""
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
        
        # Verifica se o vídeo já foi baixado
        if verificar_video_ja_baixado(titulo, pasta_destino):
            return True
        
        if 'sources' in video_info and video_info['sources']:
            download_url = video_info['sources'][0].get('url')
            if download_url:
                print(f"\nBaixando via fontes diretas: {titulo}")
                return download_with_progress(download_url, caminho_completo, nome_arquivo)
            else:
                print("Link direto não disponível em 'sources'.")
        
        print("Método alternativo falhou.")
        return False
    except Exception as e:
        print(f"❌ Erro ao baixar vídeo alternativo {video_id}: {e}")
        return False

def baixar_video(video_id, pasta_destino):
    """Baixa um vídeo específico para a pasta de destino."""
    # Criar pasta de downloads se não existir
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        print(f"📁 Pasta '{pasta_destino}' criada.")
    else:
        print(f"📁 Pasta '{pasta_destino}' já existe.")

    # Obter informações do vídeo
    print(f"\nObtendo informações do vídeo {video_id}...")
    info_endpoint = f'{BASE_URL}/videos/{video_id}'
    try:
        info_response = requests.get(info_endpoint, headers=headers)
        info_response.raise_for_status()
        
        video_info = info_response.json()
        titulo = video_info.get('title', f'video_{video_id}')
        nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)
        
        # Verificar se o vídeo já foi baixado
        if verificar_video_ja_baixado(titulo, pasta_destino):
            return True
        
        print(f"Título do vídeo: {titulo}")
        print(f"Nome do arquivo: {nome_arquivo}")
        print(f"Caminho completo: {caminho_completo}")
    except Exception as e:
        print(f"❌ Erro ao obter informações do vídeo: {e}")
        return False

    # Tentar download oficial primeiro
    print("\n=== MÉTODO 1: Download Oficial ===")
    download_endpoint = f'{DOWNLOAD_URL}/videos/{video_id}/download'
    try:
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
                return False
        
        elif download_response.status_code == 200:
            content_type = download_response.headers.get('Content-Type', '')
            print(f"Tipo de conteúdo: {content_type}")
            
            if 'application/json' in content_type:
                # Se a resposta for JSON, extrair URL de download
                try:
                    download_data = download_response.json()
                    print(f"Resposta JSON recebida: {json.dumps(download_data, indent=2)}")
                    download_url = download_data.get('url')
                    if download_url:
                        print(f"URL de download obtida: {download_url}")
                        return download_with_progress(download_url, caminho_completo, nome_arquivo)
                    else:
                        print("❌ URL de download não encontrada na resposta JSON.")
                        return False
                except json.JSONDecodeError as e:
                    print(f"❌ Erro ao decodificar JSON da resposta: {e}")
                    return False
            else:
                # Se a resposta já contém o arquivo, salvar diretamente
                print("🔄 A resposta contém os dados do arquivo. Salvando diretamente...")
                return save_response_stream(download_response, caminho_completo, nome_arquivo)
        else:
            print(f"❌ Erro ao iniciar o download oficial: {download_response.status_code}")
            print(f"Resposta: {download_response.text[:500]}...")
            return False
    except Exception as e:
        print(f"❌ Exceção durante o download oficial: {e}")
        # Se o método oficial falhar, tentar o método alternativo
        print("\n=== MÉTODO 2: Download Alternativo ===")
        print("🔄 Tentando método alternativo de download...")
        try:
            return baixar_video_alternativo(video_id, pasta_destino)
        except Exception as e_alt:
            print(f"❌ Exceção durante o download alternativo: {e_alt}")
            return False

def baixar_todos_videos(videos, pasta_destino):
    """Baixa todos os vídeos da lista fornecida, verificando quais já foram baixados."""
    if not videos:
        print("⚠️ Nenhum vídeo disponível para download.")
        return
    
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        print(f"📁 Pasta criada: {pasta_destino}")
    
    print(f"\n🔄 Iniciando verificação de {len(videos)} vídeos...")
    videos_para_baixar = []
    for video in videos:
        titulo = video.get('title', f"video_{video['id']}")
        if not verificar_video_ja_baixado(titulo, pasta_destino):
            videos_para_baixar.append(video)
    
    if not videos_para_baixar:
        print("✅ Todos os vídeos já foram baixados anteriormente!")
        return
    
    print(f"\n🔄 Iniciando download de {len(videos_para_baixar)} vídeos pendentes...")
    sucessos = 0
    falhas = 0
    videos_com_falha = []
    
    for i, video in enumerate(videos_para_baixar, 1):
        titulo = video.get('title', 'Sem título')
        print(f"\n🔄 Baixando vídeo {i} de {len(videos_para_baixar)}: {titulo}")
        if baixar_video(video['id'], pasta_destino):
            sucessos += 1
        else:
            falhas += 1
            videos_com_falha.append(video)
    
    # Tentar novamente os vídeos que falharam (até 3 tentativas)
    if videos_com_falha:
        print(f"\n⚠️ {len(videos_com_falha)} vídeos falharam no download. Tentando novamente...")
        
        for tentativa in range(2):  # 2 tentativas adicionais
            if not videos_com_falha:
                break
                
            print(f"\n🔄 Tentativa {tentativa + 2} para {len(videos_com_falha)} vídeos...")
            videos_ainda_com_falha = []
            
            for i, video in enumerate(videos_com_falha, 1):
                titulo = video.get('title', 'Sem título')
                print(f"\n🔄 Tentativa {tentativa + 2} - Baixando vídeo {i} de {len(videos_com_falha)}: {titulo}")
                
                # Esperar um pouco antes de tentar novamente
                time.sleep(3)
                
                if baixar_video(video['id'], pasta_destino):
                    sucessos += 1
                    falhas -= 1
                else:
                    videos_ainda_com_falha.append(video)
            
            videos_com_falha = videos_ainda_com_falha
    
    print("\n=== RESULTADO FINAL ===")
    print(f"✅ Downloads concluídos: {sucessos}")
    if falhas > 0:
        print(f"❌ Downloads com falha: {falhas}")
        for video in videos_com_falha:
            print(f"  - {video.get('title', 'Sem título')} (ID: {video['id']})")
    
    # Verificar arquivos na pasta
    print(f"\n📁 Arquivos na pasta {pasta_destino}:")
    arquivos = os.listdir(pasta_destino)
    if not arquivos:
        print("Nenhum arquivo encontrado na pasta de downloads.")
    else:
        print(f"Encontrados {len(arquivos)} arquivo(s):")
        tamanho_total = 0
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(pasta_destino, arquivo)
            tamanho = os.path.getsize(caminho_arquivo)
            tamanho_total += tamanho
            print(f"- {arquivo} ({formatar_tamanho(tamanho)})")
        print(f"\nTamanho total: {formatar_tamanho(tamanho_total)}")

def main():
    """Função principal com interface de linha de comando."""
    parser = argparse.ArgumentParser(description='Downloader de Vídeos do Panda Videos')
    
    # Definir os subcomandos
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponíveis')
    
    # Comando para baixar um vídeo específico
    baixar_parser = subparsers.add_parser('baixar', help='Baixar um vídeo específico')
    baixar_parser.add_argument('video_id', help='ID do vídeo a ser baixado')
    baixar_parser.add_argument('--pasta', '-p', default='downloads', help='Pasta de destino (padrão: downloads)')
    
    # Comando para listar pastas
    subparsers.add_parser('pastas', help='Listar todas as pastas disponíveis')
    
    # Comando para listar vídeos de uma pasta
    listar_parser = subparsers.add_parser('listar', help='Listar vídeos de uma pasta específica')
    listar_parser.add_argument('pasta_nome', help='Nome da pasta')
    
    # Comando para baixar todos os vídeos de uma pasta
    todos_parser = subparsers.add_parser('todos', help='Baixar todos os vídeos de uma pasta')
    todos_parser.add_argument('pasta_nome', help='Nome da pasta')
    todos_parser.add_argument('--pasta-destino', '-p', default=None, 
                             help='Pasta de destino (padrão: nome da pasta dentro de downloads)')
    
    # Comando para baixar todos os vídeos de uma pasta usando o ID da pasta
    todos_id_parser = subparsers.add_parser('todos-id', help='Baixar todos os vídeos de uma pasta usando o ID da pasta')
    todos_id_parser.add_argument('pasta_id', help='ID da pasta')
    todos_id_parser.add_argument('--pasta-destino', '-p', default=None, 
                             help='Pasta de destino (padrão: nome da pasta dentro de downloads)')
    
    # Analisar argumentos
    args = parser.parse_args()
    
    # Verificar autenticação antes de continuar
    print("🔑 Testando autenticação com a API do Panda Videos...")
    autenticado = verificar_autenticacao()
    
    if not autenticado:
        print("❌ Falha na autenticação")
        exit(1)
    
    # Executar o comando apropriado
    if args.comando == 'baixar':
        pasta_destino = args.pasta
        print(f"\n🔄 Baixando vídeo {args.video_id} para a pasta {pasta_destino}...")
        sucesso = baixar_video(args.video_id, pasta_destino)
        
        print("\n=== RESULTADO FINAL ===")
        if sucesso:
            print("✅ Download concluído com sucesso!")
        else:
            print("❌ Falha ao baixar o vídeo.")
            
    elif args.comando == 'pastas':
        listar_pastas()
        
    elif args.comando == 'listar':
        pasta = encontrar_pasta_por_nome(args.pasta_nome)
        if pasta:
            pasta_id = pasta.get('id')
            pasta_nome = pasta.get('name')
            listar_videos_pasta(pasta_id, pasta_nome)
            
    elif args.comando == 'todos':
        pasta = encontrar_pasta_por_nome(args.pasta_nome)
        if pasta:
            pasta_id = pasta.get('id')
            pasta_nome = pasta.get('name')
            
            # Definir pasta de destino
            pasta_destino = args.pasta_destino if args.pasta_destino else os.path.join('downloads', pasta_nome.replace(' ', '_'))
            
            # Listar vídeos da pasta
            videos = listar_videos_pasta(pasta_id, pasta_nome)
            
            if videos:
                # Baixar todos os vídeos
                baixar_todos_videos(videos, pasta_destino)
    
    elif args.comando == 'todos-id':
        pasta_id = args.pasta_id
        pasta = encontrar_pasta_por_id(pasta_id)
        
        if pasta:
            pasta_nome = pasta.get('name')
            
            # Definir pasta de destino
            pasta_destino = args.pasta_destino if args.pasta_destino else os.path.join('downloads', pasta_nome.replace(' ', '_'))
            
            # Listar vídeos da pasta
            videos = listar_videos_pasta(pasta_id, pasta_nome)
            
            if videos:
                # Baixar todos os vídeos
                baixar_todos_videos(videos, pasta_destino)
    else:
        # Se nenhum comando for especificado, mostrar ajuda
        parser.print_help()

if __name__ == "__main__":
    main() 