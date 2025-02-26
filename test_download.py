import os
import requests
import time
import json
from tqdm import tqdm
from panda_video_downloader import verificar_autenticacao, BASE_URL, DOWNLOAD_URL, headers, baixar_video_alternativo

# Verificar autenticação
print("Testando autenticação com a chave API: panda-59e2...")
autenticado = verificar_autenticacao()

if not autenticado:
    print("Falha na autenticação")
    exit(1)

# ID do vídeo a ser baixado (M2 Aula 1 - O universo do DEFI.mp4)
video_id = "196653a7-39e6-425a-a5bd-53b1b8a0c2ae"
pasta_destino = "downloads"

# Criar pasta de downloads se não existir
if not os.path.exists(pasta_destino):
    os.makedirs(pasta_destino)
    print(f"Pasta '{pasta_destino}' criada.")

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
    
    print(f"Título do vídeo: {titulo}")
    print(f"Nome do arquivo: {nome_arquivo}")
    print(f"Caminho completo: {caminho_completo}")
except Exception as e:
    print(f"Erro ao obter informações do vídeo: {e}")
    exit(1)

# Função para formatar tamanho em bytes para formato legível
def formatar_tamanho(tamanho_bytes):
    for unidade in ['B', 'KB', 'MB', 'GB']:
        if tamanho_bytes < 1024.0:
            return f"{tamanho_bytes:.2f} {unidade}"
        tamanho_bytes /= 1024.0
    return f"{tamanho_bytes:.2f} TB"

# Tentar download oficial primeiro
print("\n=== MÉTODO 1: Download Oficial ===")
print(f"Iniciando download oficial...")
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
            print(f"Iniciando download do arquivo via redirecionamento...")
            inicio = time.time()
            
            # Obter informações sobre o tamanho do arquivo
            try:
                file_head_response = requests.head(download_url)
                total_size = int(file_head_response.headers.get('content-length', 0))
                print(f"Tamanho total do arquivo: {formatar_tamanho(total_size)}")
            except Exception as e:
                print(f"Erro ao obter tamanho do arquivo: {e}")
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
                            print(f"\nProgresso: {formatar_tamanho(bytes_baixados)}/{formatar_tamanho(total_size)} "
                                  f"({bytes_baixados/total_size*100:.1f}%) - "
                                  f"Velocidade: {formatar_tamanho(velocidade)}/s")
            
            tempo_total = time.time() - inicio
            print(f"\nDownload concluído em {tempo_total:.2f} segundos")
            if total_size > 0:
                print(f"Velocidade média: {formatar_tamanho(total_size/tempo_total)}/s")
            sucesso = True
        else:
            print("URL de redirecionamento não encontrada nos cabeçalhos.")
            sucesso = False
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
                    print(f"Iniciando download do arquivo...")
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
                                    print(f"\nProgresso: {formatar_tamanho(bytes_baixados)}/{formatar_tamanho(total_size)} "
                                          f"({bytes_baixados/total_size*100:.1f}%) - "
                                          f"Velocidade: {formatar_tamanho(velocidade)}/s")
                    
                    tempo_total = time.time() - inicio
                    print(f"\nDownload concluído em {tempo_total:.2f} segundos")
                    print(f"Velocidade média: {formatar_tamanho(total_size/tempo_total)}/s")
                    sucesso = True
                else:
                    print("URL de download não encontrada na resposta JSON.")
                    print(f"Resposta completa: {download_data}")
                    sucesso = False
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON da resposta: {e}")
                print(f"Conteúdo da resposta: {download_response.text[:500]}...")
                sucesso = False
        else:
            # A resposta pode ser o próprio arquivo
            print("A resposta parece ser o próprio arquivo de vídeo. Salvando diretamente...")
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
                            print(f"\nProgresso: {formatar_tamanho(bytes_baixados)}/{formatar_tamanho(total_size)} "
                                  f"({bytes_baixados/total_size*100:.1f}%) - "
                                  f"Velocidade: {formatar_tamanho(velocidade)}/s")
            
            tempo_total = time.time() - inicio
            print(f"\nDownload concluído em {tempo_total:.2f} segundos")
            if total_size > 0:
                print(f"Velocidade média: {formatar_tamanho(total_size/tempo_total)}/s")
            sucesso = True
    else:
        print(f"Erro ao iniciar o download oficial: {download_response.status_code}")
        print(f"Resposta: {download_response.text[:500]}...")
        sucesso = False
except Exception as e:
    print(f"Exceção durante o download oficial: {e}")
    sucesso = False

# Se o método oficial falhar, tentar o método alternativo
if not sucesso:
    print("\n=== MÉTODO 2: Download Alternativo ===")
    print("Tentando método alternativo de download...")
    try:
        sucesso = baixar_video_alternativo(video_id, pasta_destino)
    except Exception as e:
        print(f"Exceção durante o download alternativo: {e}")
        sucesso = False

# Verificar resultado
print("\n=== RESULTADO FINAL ===")
if sucesso:
    print("Download concluído com sucesso!")
else:
    print("Falha no download do vídeo.")

# Verificar se o arquivo foi criado
print(f"\nVerificando arquivos na pasta {pasta_destino}:")
arquivos = os.listdir(pasta_destino)
if not arquivos:
    print("Nenhum arquivo encontrado na pasta de downloads.")
else:
    print(f"Encontrados {len(arquivos)} arquivo(s):")
    for arquivo in arquivos:
        caminho_arquivo = os.path.join(pasta_destino, arquivo)
        tamanho = os.path.getsize(caminho_arquivo)
        print(f"- {arquivo} ({formatar_tamanho(tamanho)})")
    
# Verificar tamanho do arquivo específico
if os.path.exists(caminho_completo):
    tamanho = os.path.getsize(caminho_completo)
    print(f"\nArquivo baixado: {nome_arquivo}")
    print(f"Tamanho do arquivo: {formatar_tamanho(tamanho)}")
    print(f"Caminho completo: {caminho_completo}")
else:
    print(f"\nO arquivo {nome_arquivo} não foi encontrado no caminho esperado.") 