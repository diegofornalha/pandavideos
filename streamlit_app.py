import streamlit as st
import os
import requests
import json
import re
import shutil
import time
import subprocess
from tqdm import tqdm
from dotenv import load_dotenv
import pandas as pd
import tempfile
import base64

# Configuração da página Streamlit
st.set_page_config(
    page_title="Panda Videos Downloader",
    page_icon="🐼",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Função para criar um link de download
def get_download_link(file_path, link_text):
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{link_text}</a>'
    return href

# Função para verificar autenticação
def verificar_autenticacao():
    """Verifica se a autenticação com a API está funcionando corretamente."""
    endpoint = f'{BASE_URL}/videos'
    
    try:
        with st.spinner('Verificando autenticação...'):
            response = requests.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                st.success("✅ Autenticação bem-sucedida!")
                return True
            else:
                st.error(f"❌ Falha na autenticação: {response.status_code}")
                st.code(response.text)
                return False
                
    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        return False

# Função para listar pastas
def listar_pastas():
    """Lista todas as pastas disponíveis na conta."""
    endpoint = f'{BASE_URL}/folders'
    
    try:
        with st.spinner('Carregando pastas...'):
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            
            pastas = response.json()
            
            if 'folders' in pastas and pastas['folders']:
                return pastas['folders']
            else:
                st.warning("Nenhuma pasta encontrada na conta.")
                return []
                
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao listar pastas: {e}")
        return []

# Função para listar vídeos de uma pasta
def listar_videos_pasta(pasta_id, pasta_nome):
    """Lista vídeos de uma pasta específica."""
    endpoint = f'{BASE_URL}/folders/{pasta_id}'
    
    try:
        with st.spinner(f'Carregando vídeos da pasta "{pasta_nome}"...'):
            response = requests.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                pasta_info = response.json()
                
                if 'videos' in pasta_info and pasta_info['videos']:
                    return pasta_info['videos']
                else:
                    st.info(f"Nenhum vídeo encontrado na pasta {pasta_nome}.")
                    return obter_videos_da_pasta_alternativo(pasta_id, pasta_nome)
            else:
                st.warning(f"Erro ao acessar a pasta: {response.status_code}")
                st.code(response.text)
                
                # Tentar método alternativo
                st.info("Tentando método alternativo para listar vídeos...")
                return obter_videos_da_pasta_alternativo(pasta_id, pasta_nome)
                
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao listar vídeos da pasta: {e}")
        return obter_videos_da_pasta_alternativo(pasta_id, pasta_nome)

# Função para obter vídeos por método alternativo
def obter_videos_da_pasta_alternativo(pasta_id, pasta_nome):
    """Obtém vídeos da pasta específica por método alternativo."""
    
    # Método alternativo: obter todos os vídeos e filtrar pela pasta
    try:
        with st.spinner('Buscando vídeos por método alternativo...'):
            # Obter todos os vídeos
            all_videos_endpoint = f'{BASE_URL}/videos'
            response = requests.get(all_videos_endpoint, headers=headers)
            response.raise_for_status()
            
            all_videos = response.json()
            
            if 'videos' not in all_videos:
                st.warning("Nenhum vídeo encontrado na conta.")
                return []
            
            # Filtrar vídeos por pasta
            videos_na_pasta = []
            for video in all_videos['videos']:
                if video.get('folder_id') == pasta_id:
                    videos_na_pasta.append(video)
            
            if videos_na_pasta:
                return videos_na_pasta
            else:
                st.warning(f"Nenhum vídeo encontrado na pasta {pasta_nome}.")
                return []
                
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao obter vídeos: {e}")
        return []

# Função para baixar vídeo oficial
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
        
        # Fazer a requisição POST para iniciar o download
        download_response = requests.post(download_endpoint, headers=headers)
        
        if download_response.status_code == 200:
            # Obter a URL de download da resposta
            download_data = download_response.json()
            if 'url' in download_data:
                download_url = download_data['url']
                
                # Fazer o download do arquivo
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                file_response = requests.get(download_url, stream=True)
                total_size = int(file_response.headers.get('content-length', 0))
                
                with open(caminho_completo, 'wb') as f:
                    downloaded = 0
                    for chunk in file_response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = int(100 * downloaded / total_size)
                            progress_bar.progress(progress / 100)
                            status_text.text(f"Baixando: {progress}% concluído")
                
                status_text.text("Download concluído!")
                return caminho_completo
            else:
                st.warning("URL de download não encontrada na resposta.")
                st.code(download_data)
                return baixar_video_alternativo(video_id, pasta_destino)
        else:
            st.warning(f"Erro ao iniciar o download oficial: {download_response.status_code}")
            st.code(download_response.text)
            
            # Se o download oficial falhar, tentar método alternativo
            st.info("Tentando método alternativo de download...")
            return baixar_video_alternativo(video_id, pasta_destino)
    
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao baixar vídeo pelo método oficial: {e}")
        st.info("Tentando método alternativo de download...")
        return baixar_video_alternativo(video_id, pasta_destino)

# Função para baixar vídeo por método alternativo
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
            
            st.info(f"Baixando via fontes diretas: {titulo}")
            
            # Fazer download do vídeo com barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(caminho_completo, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = int(100 * downloaded / total_size)
                        progress_bar.progress(progress / 100)
                        status_text.text(f"Baixando: {progress}% concluído")
            
            status_text.text("Download concluído!")
            return caminho_completo
        else:
            st.warning(f"Não foi possível encontrar o link de download direto para o vídeo.")
            
            # Verificar se há um link de playback
            if 'delivery_url' in video_info:
                st.info(f"Tentando método m3u8...")
                return baixar_video_m3u8(video_info['delivery_url'], titulo, pasta_destino)
            else:
                # Tentar obter o player URL
                try:
                    player_response = requests.get(f"{BASE_URL}/videos/{video_id}/player", headers=headers)
                    if player_response.status_code == 200:
                        player_info = player_response.json()
                        if 'playerUrl' in player_info:
                            return baixar_video_m3u8(player_info['playerUrl'], titulo, pasta_destino)
                    st.error(f"Não foi possível encontrar um link de playback para o vídeo: {video_id}")
                    return None
                except Exception as e:
                    st.error(f"Erro ao obter player URL: {e}")
                    return None
    
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao baixar vídeo alternativo {video_id}: {e}")
        return None

# Função para baixar vídeo via m3u8
def baixar_video_m3u8(url, titulo, pasta_destino='downloads'):
    """Baixa vídeo a partir de um link m3u8."""
    st.info(f"Iniciando download via m3u8 para: {titulo}")
    
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
                st.error("Não foi possível encontrar o link do m3u8 na página.")
                return None
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
            # No Streamlit, vamos selecionar automaticamente a melhor resolução
            resolucao_idx = 0  # Melhor qualidade (geralmente a primeira)
            
            # Extrair a URL do m3u8 específico da resolução
            playlist_urls = re.findall(r'^[^#].+\.m3u8', m3u8_content, re.MULTILINE)
            if not playlist_urls:
                st.error("Não foi possível encontrar playlists específicas de resolução.")
                return None
                
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
                st.error("Não foi possível encontrar segmentos de vídeo.")
                return None
            
            # Criar diretório temporário
            temp_dir = tempfile.mkdtemp()
            
            # Base URL para os segmentos
            base_url = resolucao_url.rsplit('/', 1)[0]
            
            # Baixar todos os segmentos
            st.text(f"Baixando {len(segmentos)} segmentos...")
            progress_bar = st.progress(0)
            
            with open(os.path.join(temp_dir, 'lista.txt'), 'w') as lista_file:
                for i, segmento in enumerate(segmentos):
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
                    
                    # Atualizar barra de progresso
                    progress_bar.progress((i + 1) / len(segmentos))
            
            # Criar pasta de downloads se não existir
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)
            
            # Nome do arquivo final
            nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
            caminho_completo = os.path.join(pasta_destino, nome_arquivo)
            
            # Unir os segmentos com ffmpeg
            st.text("Unindo segmentos com ffmpeg...")
            try:
                # Verificar se ffmpeg está instalado
                ffmpeg_cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', 
                             '-i', os.path.join(temp_dir, 'lista.txt'), 
                             '-c', 'copy', caminho_completo]
                
                result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if result.returncode == 0:
                    st.success(f"Download concluído: {caminho_completo}")
                    # Limpar arquivos temporários
                    shutil.rmtree(temp_dir)
                    return caminho_completo
                else:
                    st.error("Erro ao unir os segmentos com ffmpeg.")
                    st.code(result.stderr.decode())
                    return None
                    
            except Exception as e:
                st.error(f"Erro ao unir os segmentos: {e}")
                st.warning("Verifique se o ffmpeg está instalado corretamente.")
                return None
        
        else:
            st.error("Não foi possível identificar as resoluções disponíveis.")
            return None
            
    except Exception as e:
        st.error(f"Erro no processo de download via m3u8: {e}")
        return None

# Função principal para baixar vídeo
def baixar_video(video_id, pasta_destino='downloads'):
    """Função principal para baixar vídeo - tenta o método oficial primeiro."""
    return baixar_video_oficial(video_id, pasta_destino)

# Interface principal do Streamlit
def main():
    st.title("🐼 Panda Videos Downloader")
    st.markdown("---")
    
    # Sidebar para configurações
    st.sidebar.title("Configurações")
    
    # Mostrar a chave API (parcialmente oculta)
    if API_KEY:
        api_key_masked = API_KEY[:5] + "..." + API_KEY[-5:] if len(API_KEY) > 10 else "***"
        st.sidebar.success(f"API Key: {api_key_masked}")
    else:
        st.sidebar.error("API Key não encontrada!")
        st.sidebar.info("Crie um arquivo .env com a variável PANDA_API_KEY")
        return
    
    # Pasta de destino para downloads
    pasta_destino = st.sidebar.text_input("Pasta de destino", "downloads")
    
    # Opção para baixar todos os vídeos automaticamente
    baixar_todos_automaticamente = st.sidebar.checkbox("Baixar todos os vídeos automaticamente", value=False)
    
    # Verificar autenticação automaticamente
    if not verificar_autenticacao():
        st.stop()
    
    # Carregar pastas
    pastas = listar_pastas()
    
    if not pastas:
        st.warning("Não foi possível listar as pastas. Verifique sua conexão e permissões.")
        st.stop()
    
    # Criar DataFrame para exibir as pastas
    pastas_df = pd.DataFrame([
        {"ID": pasta.get('id'), "Nome": pasta.get('name', 'Sem nome')}
        for pasta in pastas
    ])
    
    # Exibir pastas em uma tabela
    st.subheader("📁 Pastas Disponíveis")
    st.dataframe(pastas_df, use_container_width=True)
    
    # Selecionar pasta
    pasta_selecionada = st.selectbox(
        "Selecione uma pasta:",
        options=range(len(pastas)),
        format_func=lambda i: pastas[i].get('name', 'Sem nome')
    )
    
    pasta_id = pastas[pasta_selecionada].get('id')
    pasta_nome = pastas[pasta_selecionada].get('name', 'Sem nome')
    
    if st.button(f"Listar Vídeos da Pasta: {pasta_nome}"):
        # Listar vídeos da pasta selecionada
        videos = listar_videos_pasta(pasta_id, pasta_nome)
        
        if not videos:
            st.warning(f"Nenhum vídeo encontrado na pasta {pasta_nome}.")
            st.stop()
        
        # Salvar os vídeos na sessão para uso posterior
        st.session_state.videos = videos
        
        # Criar DataFrame para exibir os vídeos
        videos_df = pd.DataFrame([
            {
                "ID": video.get('id'),
                "Título": video.get('title', 'Sem título'),
                "Duração": video.get('duration', 'N/A'),
                "Criado em": video.get('created_at', 'N/A')
            }
            for video in videos
        ])
        
        # Exibir vídeos em uma tabela
        st.subheader(f"🎬 Vídeos na Pasta: {pasta_nome}")
        st.dataframe(videos_df, use_container_width=True)
        
        # Se a opção de baixar todos automaticamente estiver ativada
        if baixar_todos_automaticamente:
            st.session_state.download_all = True
        # Caso contrário, mostrar as opções de download normais
        else:
            # Opções de download
            st.subheader("⬇️ Opções de Download")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Baixar Todos os Vídeos"):
                    st.session_state.download_all = True
            
            with col2:
                video_indices = range(len(videos))
                video_selecionado = st.selectbox(
                    "Selecione um vídeo para baixar:",
                    options=video_indices,
                    format_func=lambda i: videos[i].get('title', f"Vídeo {i+1}")
                )
                
                if st.button("Baixar Vídeo Selecionado"):
                    st.session_state.download_single = video_selecionado
    
    # Processar downloads
    if hasattr(st.session_state, 'videos'):
        videos = st.session_state.videos
        
        # Download de todos os vídeos
        if hasattr(st.session_state, 'download_all') and st.session_state.download_all:
            st.subheader("📥 Baixando Todos os Vídeos")
            
            # Criar pasta de downloads
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)
            
            # Baixar cada vídeo
            arquivos_baixados = []
            for i, video in enumerate(videos):
                st.text(f"Baixando vídeo {i+1} de {len(videos)}: {video.get('title', 'Sem título')}")
                
                caminho_arquivo = baixar_video(video['id'], pasta_destino)
                if caminho_arquivo:
                    arquivos_baixados.append(caminho_arquivo)
            
            # Exibir resultados
            if arquivos_baixados:
                st.success(f"✅ {len(arquivos_baixados)} vídeos baixados com sucesso!")
                
                # Exibir links para os arquivos baixados
                st.subheader("📋 Arquivos Baixados")
                for arquivo in arquivos_baixados:
                    st.markdown(get_download_link(arquivo, f"📥 {os.path.basename(arquivo)}"), unsafe_allow_html=True)
            else:
                st.error("❌ Nenhum vídeo foi baixado com sucesso.")
            
            # Limpar flag de download
            st.session_state.download_all = False
        
        # Download de um único vídeo
        if hasattr(st.session_state, 'download_single'):
            video_idx = st.session_state.download_single
            video = videos[video_idx]
            
            st.subheader(f"📥 Baixando: {video.get('title', 'Sem título')}")
            
            # Criar pasta de downloads
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)
            
            # Baixar o vídeo
            caminho_arquivo = baixar_video(video['id'], pasta_destino)
            
            # Exibir resultado
            if caminho_arquivo:
                st.success(f"✅ Vídeo baixado com sucesso!")
                st.markdown(get_download_link(caminho_arquivo, f"📥 {os.path.basename(caminho_arquivo)}"), unsafe_allow_html=True)
            else:
                st.error("❌ Não foi possível baixar o vídeo.")
            
            # Limpar flag de download
            del st.session_state.download_single

# Executar a aplicação
if __name__ == "__main__":
    main() 