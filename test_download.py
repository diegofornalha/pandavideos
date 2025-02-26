import os
import requests
import time
import json
import argparse
from tqdm import tqdm
from panda_video_downloader import verificar_autenticacao, BASE_URL, DOWNLOAD_URL, headers, baixar_video_alternativo

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
    print(f"🔄 Iniciando download oficial...")
    download_endpoint = f'{DOWNLOAD_URL}/videos/{video_id}/download'

    try:
        print(f"Fazendo requisição para: {download_endpoint}")
        download_response = requests.post(download_endpoint, headers=headers, timeout=30, allow_redirects=False)
        print(f"Status da resposta: {download_response.status_code}")
        
        # Verificar se é um redirecionamento
        if download_response.status_code in [301, 302, 303, 307, 308]:
            download_url = download_response.headers.get('Location')
            print(f"Redirecionamento detectado para: {download_url}")
            
            if download_url:
                # Fazer o download do arquivo com barra de progresso
                print(f"🔄 Iniciando download do arquivo via redirecionamento...")
                inicio = time.time()
                
                # Obter informações sobre o tamanho do arquivo
                try:
                    file_head_response = requests.head(download_url)
                    total_size = int(file_head_response.headers.get('content-length', 0))
                    print(f"Tamanho total do arquivo: {formatar_tamanho(total_size)}")
                except Exception as e:
                    print(f"⚠️ Erro ao obter tamanho do arquivo: {e}")
                    total_size = 0
                
                # Iniciar o download com stream para usar a barra de progresso
                file_response = requests.get(download_url, stream=True, timeout=60)
                
                # Configurar a barra de progresso
                with open(caminho_completo, 'wb') as f, tqdm(
                    desc=f"Baixando {nome_arquivo}",
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
                ) as bar:
                    bytes_baixados = 0
                    for chunk in file_response.iter_content(chunk_size=8192):
                        if chunk:
                            size = f.write(chunk)
                            bar.update(size)
                            bytes_baixados += size
                            
                            # Mostrar estatísticas a cada 5MB
                            if bytes_baixados % (5 * 1024 * 1024) < 8192:
                                tempo_decorrido = time.time() - inicio
                                velocidade = bytes_baixados / tempo_decorrido if tempo_decorrido > 0 else 0
                                print(f"\n📊 Progresso: {formatar_tamanho(bytes_baixados)}/{formatar_tamanho(total_size)} "
                                      f"({bytes_baixados/total_size*100:.1f}%) - "
                                      f"Velocidade: {formatar_tamanho(velocidade)}/s")
                
                tempo_total = time.time() - inicio
                print(f"\n✅ Download concluído em {tempo_total:.2f} segundos")
                if total_size > 0:
                    print(f"🚀 Velocidade média: {formatar_tamanho(total_size/tempo_total)}/s")
                return True
            else:
                print("❌ URL de redirecionamento não encontrada nos cabeçalhos.")
                return False
        elif download_response.status_code == 200:
            # Verificar se a resposta é um JSON
            content_type = download_response.headers.get('Content-Type', '')
            print(f"Tipo de conteúdo: {content_type}")
            
            if 'application/json' in content_type:
                # Tentar obter a URL de download da resposta JSON
                try:
                    download_data = download_response.json()
                    print(f"Resposta JSON recebida: {json.dumps(download_data, indent=2)}")
                    
                    if 'url' in download_data:
                        download_url = download_data['url']
                        print(f"URL de download obtida: {download_url}")
                        
                        # Fazer o download do arquivo com barra de progresso
                        print(f"🔄 Iniciando download do arquivo...")
                        inicio = time.time()
                        
                        # Obter informações sobre o tamanho do arquivo
                        file_head_response = requests.head(download_url)
                        total_size = int(file_head_response.headers.get('content-length', 0))
                        print(f"Tamanho total do arquivo: {formatar_tamanho(total_size)}")
                        
                        # Iniciar o download com stream para usar a barra de progresso
                        file_response = requests.get(download_url, stream=True, timeout=60)
                        
                        # Configurar a barra de progresso
                        with open(caminho_completo, 'wb') as f, tqdm(
                            desc=f"Baixando {nome_arquivo}",
                            total=total_size,
                            unit='B',
                            unit_scale=True,
                            unit_divisor=1024,
                            bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
                        ) as bar:
                            bytes_baixados = 0
                            for chunk in file_response.iter_content(chunk_size=8192):
                                if chunk:
                                    size = f.write(chunk)
                                    bar.update(size)
                                    bytes_baixados += size
                                    
                                    # Mostrar estatísticas a cada 5MB
                                    if bytes_baixados % (5 * 1024 * 1024) < 8192:
                                        tempo_decorrido = time.time() - inicio
                                        velocidade = bytes_baixados / tempo_decorrido if tempo_decorrido > 0 else 0
                                        print(f"\n📊 Progresso: {formatar_tamanho(bytes_baixados)}/{formatar_tamanho(total_size)} "
                                              f"({bytes_baixados/total_size*100:.1f}%) - "
                                              f"Velocidade: {formatar_tamanho(velocidade)}/s")
                        
                        tempo_total = time.time() - inicio
                        print(f"\n✅ Download concluído em {tempo_total:.2f} segundos")
                        print(f"🚀 Velocidade média: {formatar_tamanho(total_size/tempo_total)}/s")
                        return True
                    else:
                        print("❌ URL de download não encontrada na resposta JSON.")
                        print(f"Resposta completa: {download_data}")
                        return False
                except json.JSONDecodeError as e:
                    print(f"❌ Erro ao decodificar JSON da resposta: {e}")
                    print(f"Conteúdo da resposta: {download_response.text[:500]}...")
                    return False
            else:
                # A resposta pode ser o próprio arquivo
                print("🔄 A resposta parece ser o próprio arquivo de vídeo. Salvando diretamente...")
                inicio = time.time()
                
                total_size = int(download_response.headers.get('content-length', 0))
                print(f"Tamanho total do arquivo: {formatar_tamanho(total_size)}")
                
                with open(caminho_completo, 'wb') as f, tqdm(
                    desc=f"Baixando {nome_arquivo}",
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
                ) as bar:
                    bytes_baixados = 0
                    for chunk in download_response.iter_content(chunk_size=8192):
                        if chunk:
                            size = f.write(chunk)
                            bar.update(size)
                            bytes_baixados += size
                            
                            # Mostrar estatísticas a cada 5MB
                            if bytes_baixados % (5 * 1024 * 1024) < 8192:
                                tempo_decorrido = time.time() - inicio
                                velocidade = bytes_baixados / tempo_decorrido if tempo_decorrido > 0 else 0
                                print(f"\n📊 Progresso: {formatar_tamanho(bytes_baixados)}/{formatar_tamanho(total_size)} "
                                      f"({bytes_baixados/total_size*100:.1f}%) - "
                                      f"Velocidade: {formatar_tamanho(velocidade)}/s")
                
                tempo_total = time.time() - inicio
                print(f"\n✅ Download concluído em {tempo_total:.2f} segundos")
                if total_size > 0:
                    print(f"🚀 Velocidade média: {formatar_tamanho(total_size/tempo_total)}/s")
                return True
        else:
            print(f"❌ Erro ao iniciar o download oficial: {download_response.status_code}")
            print(f"Resposta: {download_response.text[:500]}...")
            return False
    except Exception as e:
        print(f"❌ Exceção durante o download oficial: {e}")
        return False

    # Se o método oficial falhar, tentar o método alternativo
    print("\n=== MÉTODO 2: Download Alternativo ===")
    print("🔄 Tentando método alternativo de download...")
    try:
        return baixar_video_alternativo(video_id, pasta_destino)
    except Exception as e:
        print(f"❌ Exceção durante o download alternativo: {e}")
        return False

def baixar_todos_videos(videos, pasta_destino):
    """Baixa todos os vídeos da lista fornecida, verificando quais já foram baixados."""
    if not videos:
        print("⚠️ Nenhum vídeo disponível para download.")
        return
    
    # Criar pasta de downloads se não existir
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
    
    sucessos = 0
    falhas = 0
    
    for i, video in enumerate(videos_para_baixar, 1):
        print(f"\n🔄 Baixando vídeo {i} de {len(videos_para_baixar)}: {video.get('title', 'Sem título')}")
        if baixar_video(video['id'], pasta_destino):
            sucessos += 1
        else:
            falhas += 1
    
    print("\n=== RESULTADO FINAL ===")
    print(f"✅ Downloads concluídos: {sucessos}")
    if falhas > 0:
        print(f"❌ Downloads com falha: {falhas}")
    
    # Verificar arquivos na pasta
    print(f"\n📁 Arquivos na pasta {pasta_destino}:")
    arquivos = os.listdir(pasta_destino)
    if not arquivos:
        print("Nenhum arquivo encontrado na pasta de downloads.")
    else:
        print(f"Encontrados {len(arquivos)} arquivo(s):")
        for arquivo in arquivos:
            caminho_arquivo = os.path.join(pasta_destino, arquivo)
            tamanho = os.path.getsize(caminho_arquivo)
            print(f"- {arquivo} ({formatar_tamanho(tamanho)})")

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
            pasta_destino = args.pasta_destino if args.pasta_destino else os.path.join('downloads', pasta_nome)
            
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
            pasta_destino = args.pasta_destino if args.pasta_destino else os.path.join('downloads', pasta_nome)
            
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