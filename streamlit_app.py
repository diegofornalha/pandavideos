import streamlit as st
import os
import pandas as pd
import io
import time
from panda_downloader import (
    verificar_autenticacao, 
    listar_pastas,
    listar_videos_pasta, 
    baixar_video, 
    baixar_todos_videos,
    baixar_video_oficial,
    identificar_subpastas,
    headers,
    BASE_URL,
    API_KEY,
    formatar_tamanho
)
from dotenv import load_dotenv
import requests

# Configurações da página
st.set_page_config(
    page_title="Panda Video Downloader",
    page_icon="🐼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        margin-top: 0;
        margin-bottom: 1rem;
        text-align: center;
    }
    .success-message {
        color: #00CC66;
        font-weight: bold;
    }
    .error-message {
        color: #FF4B4B;
        font-weight: bold;
    }
    .info-box {
        background-color: #F0F2F6;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares adaptadas para Streamlit
def verificar_autenticacao_st():
    """Verificar autenticação com feedback no Streamlit"""
    with st.spinner("Verificando autenticação com a API do Panda Videos..."):
        if API_KEY is None:
            st.error("🔑 API KEY não está definida! Configure o arquivo .env com sua PANDA_API_KEY")
            return False
        
        endpoint = f'{BASE_URL}/videos'
        try:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                st.success("✅ Autenticação realizada com sucesso!")
                return True
            else:
                st.error(f"❌ Falha na autenticação. Status: {response.status_code}")
                st.error(f"Resposta: {response.text}")
                return False
        except Exception as e:
            st.error(f"❌ Erro na autenticação: {e}")
            return False

def baixar_video_st(video_id, pasta_destino="downloads", status_container=None):
    """Versão adaptada para Streamlit do download de vídeo"""
    if status_container is None:
        status_container = st.empty()
    
    # Obter informações do vídeo
    endpoint = f'{BASE_URL}/videos/{video_id}'
    try:
        response = requests.get(endpoint, headers=headers)
        if response.status_code != 200:
            status_container.error(f"❌ Erro ao obter informações do vídeo: {response.status_code}")
            return False
        
        video_info = response.json()
        titulo = video_info.get('title', f'video_{video_id}')
        
        # Criar diretório se não existir
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
            status_container.info(f"📁 Pasta criada: {pasta_destino}")
        
        # Tentar baixar o vídeo
        status_container.info(f"🔄 Iniciando download do vídeo: {titulo}")
        resultado = baixar_video(video_id, pasta_destino)
        
        if resultado:
            nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
            caminho_completo = os.path.join(pasta_destino, nome_arquivo)
            if os.path.exists(caminho_completo):
                tamanho = os.path.getsize(caminho_completo)
                status_container.success(f"✅ Download concluído: {nome_arquivo} ({formatar_tamanho(tamanho)})")
            else:
                status_container.success(f"✅ Download concluído, mas não foi possível encontrar o arquivo localmente.")
            return True
        else:
            status_container.error(f"❌ Falha no download do vídeo {titulo}")
            return False
            
    except Exception as e:
        status_container.error(f"❌ Erro: {e}")
        return False

def baixar_todos_videos_st(videos, pasta_destino="downloads"):
    """Versão adaptada para Streamlit do download de múltiplos vídeos"""
    if not videos:
        st.warning("⚠️ Nenhum vídeo disponível para download.")
        return
    
    # Criar diretório se não existir
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        st.info(f"📁 Pasta criada: {pasta_destino}")
    
    # Verificar vídeos já baixados
    st.info(f"🔍 Verificando {len(videos)} vídeos...")
    videos_para_baixar = []
    for video in videos:
        titulo = video.get('title', f"video_{video['id']}")
        nome_arquivo = f"{titulo.replace(' ', '_')}.mp4"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)
        
        if os.path.exists(caminho_completo):
            tamanho = os.path.getsize(caminho_completo)
            st.info(f"⚠️ Vídeo '{titulo}' já existe ({formatar_tamanho(tamanho)})")
        else:
            videos_para_baixar.append(video)
    
    if not videos_para_baixar:
        st.success("✅ Todos os vídeos já foram baixados anteriormente!")
        return
    
    # Baixar vídeos pendentes
    st.info(f"🔄 Iniciando download de {len(videos_para_baixar)} vídeos pendentes...")
    
    # Barra de progresso geral
    progresso_geral = st.progress(0)
    status_atual = st.empty()
    
    sucessos = 0
    falhas = 0
    videos_com_falha = []
    
    for i, video in enumerate(videos_para_baixar):
        titulo = video.get('title', 'Sem título')
        status_atual.info(f"🔄 Baixando vídeo {i+1} de {len(videos_para_baixar)}: {titulo}")
        
        # Container para status deste vídeo específico
        status_container = st.empty()
        
        if baixar_video_st(video['id'], pasta_destino, status_container):
            sucessos += 1
        else:
            falhas += 1
            videos_com_falha.append(video)
        
        # Atualizar barra de progresso
        progresso_geral.progress((i + 1) / len(videos_para_baixar))
    
    # Resultado final
    st.markdown("## Resultado Final")
    st.success(f"✅ Downloads concluídos: {sucessos}")
    
    if falhas > 0:
        st.error(f"❌ Downloads com falha: {falhas}")
        for video in videos_com_falha:
            st.error(f"  - {video.get('title', 'Sem título')} (ID: {video['id']})")
    
    # Exibir arquivos na pasta
    arquivos = os.listdir(pasta_destino)
    if arquivos:
        st.markdown(f"## 📁 Arquivos na pasta {pasta_destino}")
        
        dados_arquivos = []
        tamanho_total = 0
        
        for arquivo in arquivos:
            if arquivo.endswith('.mp4'):
                caminho_arquivo = os.path.join(pasta_destino, arquivo)
                tamanho = os.path.getsize(caminho_arquivo)
                tamanho_total += tamanho
                dados_arquivos.append({
                    "Arquivo": arquivo,
                    "Tamanho": formatar_tamanho(tamanho)
                })
        
        # Exibir tabela de arquivos
        if dados_arquivos:
            st.table(pd.DataFrame(dados_arquivos))
            st.info(f"Tamanho total: {formatar_tamanho(tamanho_total)}")
        else:
            st.info("Nenhum arquivo MP4 encontrado na pasta de downloads.")

# Páginas da aplicação
def pagina_inicio():
    st.markdown('<h1 class="main-header">🐼 Panda Video Downloader</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Baixe vídeos da plataforma Panda Videos</p>', unsafe_allow_html=True)
    
    # Verificar autenticação
    if not verificar_autenticacao_st():
        st.stop()
    
    st.markdown("## 📁 Opções Disponíveis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🔍 Listar Pastas")
        st.button("Ver Pastas", on_click=lambda: st.session_state.update({"pagina": "listar_pastas"}))
    
    with col2:
        st.info("📥 Baixar Video por ID")
        st.button("Baixar Video", on_click=lambda: st.session_state.update({"pagina": "baixar_video"}))
    
    with col3:
        st.info("🗂️ Gerenciar Subpastas")
        st.button("Gerenciar Módulos", on_click=lambda: st.session_state.update({"pagina": "subpastas"}))
    
    # Informações adicionais
    st.markdown("## 📋 Sobre o Aplicativo")
    
    with st.expander("Como usar"):
        st.markdown("""
        ### Instruções de Uso
        
        1. **Ver Pastas**: Lista todas as pastas disponíveis na sua conta e permite baixar vídeos de uma pasta específica.
        2. **Baixar Video**: Permite baixar um vídeo específico através do seu ID.
        3. **Gerenciar Módulos**: Identifica subpastas/módulos de um curso e permite baixar todos os vídeos de um curso completo.
        
        ### Pré-requisitos
        
        - Uma chave de API válida do Panda Videos configurada no arquivo `.env`
        - Conexão com a internet
        - Espaço em disco suficiente para os downloads
        """)

def pagina_listar_pastas():
    st.markdown("# 📁 Pastas Disponíveis")
    st.button("← Voltar", on_click=lambda: st.session_state.update({"pagina": "inicio"}))
    
    # Listar pastas
    with st.spinner("Carregando pastas..."):
        pastas = listar_pastas(exibir=False)
    
    if not pastas:
        st.warning("Nenhuma pasta encontrada na conta.")
        return
    
    # Exibir pastas como tabela
    dados_pastas = []
    for i, pasta in enumerate(pastas, 1):
        dados_pastas.append({
            "Número": i,
            "Nome": pasta.get('name', 'Sem nome'),
            "ID": pasta.get('id', 'Sem ID')
        })
    
    # Criar dataframe e exibir
    df_pastas = pd.DataFrame(dados_pastas)
    st.dataframe(df_pastas)
    
    # Seleção de pasta
    pasta_selecionada = st.selectbox(
        "Selecione uma pasta para visualizar vídeos:", 
        options=range(len(pastas)),
        format_func=lambda i: f"{pastas[i].get('name', 'Sem nome')} (ID: {pastas[i].get('id', 'Sem ID')})"
    )
    
    if st.button("Listar Vídeos"):
        pasta_id = pastas[pasta_selecionada].get('id')
        pasta_nome = pastas[pasta_selecionada].get('name', 'Sem nome')
        
        st.session_state.pasta_atual = {
            "id": pasta_id,
            "nome": pasta_nome
        }
        
        st.session_state.pagina = "listar_videos"

def pagina_listar_videos():
    if "pasta_atual" not in st.session_state:
        st.error("Nenhuma pasta selecionada. Voltando para a lista de pastas.")
        st.button("Ir para Lista de Pastas", on_click=lambda: st.session_state.update({"pagina": "listar_pastas"}))
        return
    
    pasta_id = st.session_state.pasta_atual["id"]
    pasta_nome = st.session_state.pasta_atual["nome"]
    
    st.markdown(f"# 🎬 Vídeos da Pasta: {pasta_nome}")
    st.button("← Voltar para Pastas", on_click=lambda: st.session_state.update({"pagina": "listar_pastas"}))
    
    # Listar vídeos
    with st.spinner(f"Carregando vídeos da pasta {pasta_nome}..."):
        videos = listar_videos_pasta(pasta_id, pasta_nome)
    
    if not videos:
        st.warning(f"Nenhum vídeo encontrado na pasta '{pasta_nome}'")
        return
    
    # Exibir vídeos como tabela
    dados_videos = []
    for i, video in enumerate(videos, 1):
        dados_videos.append({
            "Número": i,
            "Título": video.get('title', 'Sem título'),
            "Duração": video.get('duration', 'N/A'),
            "ID": video.get('id', 'Sem ID')
        })
    
    # Criar dataframe e exibir
    df_videos = pd.DataFrame(dados_videos)
    st.dataframe(df_videos)
    
    # Opções de download
    st.markdown("## Opções de Download")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Baixar Um Vídeo")
        video_selecionado = st.selectbox(
            "Selecione um vídeo para baixar:", 
            options=range(len(videos)),
            format_func=lambda i: f"{videos[i].get('title', 'Sem título')} (Duração: {videos[i].get('duration', 'N/A')})"
        )
        
        pasta_destino_individual = st.text_input("Pasta de destino (individual):", value="downloads")
        
        if st.button("Baixar Vídeo Selecionado"):
            video_id = videos[video_selecionado].get('id')
            if video_id:
                baixar_video_st(video_id, pasta_destino_individual)
            else:
                st.error("ID do vídeo não encontrado.")
    
    with col2:
        st.markdown("### Baixar Todos os Vídeos")
        pasta_destino_todos = st.text_input(
            "Pasta de destino (todos):", 
            value=f"downloads/{pasta_nome.replace(' ', '_')}"
        )
        
        if st.button("Baixar Todos os Vídeos"):
            baixar_todos_videos_st(videos, pasta_destino_todos)

def pagina_baixar_video():
    st.markdown("# 📥 Baixar Vídeo por ID")
    st.button("← Voltar", on_click=lambda: st.session_state.update({"pagina": "inicio"}))
    
    video_id = st.text_input("ID do Vídeo:", placeholder="Insira o ID do vídeo aqui")
    pasta_destino = st.text_input("Pasta de destino:", value="downloads")
    
    if st.button("Baixar Vídeo", disabled=not video_id):
        if not video_id.strip():
            st.error("Por favor, insira um ID de vídeo válido.")
        else:
            baixar_video_st(video_id.strip(), pasta_destino)

def pagina_subpastas():
    st.markdown("# 🗂️ Subpastas / Módulos")
    st.button("← Voltar", on_click=lambda: st.session_state.update({"pagina": "inicio"}))
    
    st.info("Esta funcionalidade permite identificar e baixar vídeos de módulos/subpastas de um curso completo.")
    
    # Listar pastas para seleção
    with st.expander("Selecionar da lista de pastas"):
        with st.spinner("Carregando pastas..."):
            pastas = listar_pastas(exibir=False)
        
        if not pastas:
            st.warning("Nenhuma pasta encontrada na conta.")
        else:
            pasta_selecionada = st.selectbox(
                "Selecione a pasta principal/curso:", 
                options=range(len(pastas)),
                format_func=lambda i: f"{pastas[i].get('name', 'Sem nome')} (ID: {pastas[i].get('id', 'Sem ID')})"
            )
            
            if st.button("Usar Esta Pasta"):
                pasta_id = pastas[pasta_selecionada].get('id')
                st.session_state.pasta_id_subpastas = pasta_id
    
    # Inserir ID manualmente
    col1, col2 = st.columns(2)
    with col1:
        pasta_id_manual = st.text_input("Ou insira o ID da pasta principal/curso manualmente:")
        if st.button("Usar Este ID", disabled=not pasta_id_manual):
            st.session_state.pasta_id_subpastas = pasta_id_manual
    
    with col2:
        padrao_regex = st.text_input("Padrão de regex para filtrar subpastas (opcional):", 
                                   placeholder="Ex: Módulo.*")
    
    # Se foi selecionada uma pasta, mostrar opções para identificar subpastas
    if "pasta_id_subpastas" in st.session_state:
        pasta_id = st.session_state.pasta_id_subpastas
        
        st.markdown(f"## Identificando subpastas para ID: {pasta_id}")
        
        # Pasta de destino para downloads
        pasta_destino_base = st.text_input("Pasta base para downloads:", value="downloads/curso")
        
        if st.button("Identificar Subpastas"):
            with st.spinner("Identificando subpastas..."):
                subpastas = identificar_subpastas(pasta_id, padrao_regex)
            
            if not subpastas:
                st.warning("Nenhuma subpasta encontrada com o padrão especificado.")
            else:
                # Exibir subpastas encontradas
                st.success(f"Encontradas {len(subpastas)} subpastas/módulos!")
                
                dados_subpastas = []
                for i, subpasta in enumerate(subpastas, 1):
                    dados_subpastas.append({
                        "Número": i,
                        "Nome": subpasta['name'],
                        "ID": subpasta['id']
                    })
                
                st.dataframe(pd.DataFrame(dados_subpastas))
                
                # Opção para baixar todos os vídeos das subpastas
                if st.button("Baixar Vídeos de Todas as Subpastas"):
                    # Garantir que a pasta base existe
                    if not os.path.exists(pasta_destino_base):
                        os.makedirs(pasta_destino_base)
                        st.info(f"Pasta base criada: {pasta_destino_base}")
                    
                    st.info(f"Iniciando download de vídeos de todas as subpastas para: {pasta_destino_base}")
                    
                    # Barra de progresso para as subpastas
                    progresso_subpastas = st.progress(0)
                    
                    for i, subpasta in enumerate(subpastas):
                        subpasta_id = subpasta['id']
                        subpasta_nome = subpasta['name']
                        
                        # Criar pasta específica para esta subpasta
                        pasta_destino = os.path.join(pasta_destino_base, subpasta_nome.replace(' ', '_'))
                        if not os.path.exists(pasta_destino):
                            os.makedirs(pasta_destino)
                        
                        st.markdown(f"### Processando subpasta: {subpasta_nome}")
                        videos = listar_videos_pasta(subpasta_id, subpasta_nome)
                        
                        if videos:
                            st.info(f"Baixando {len(videos)} vídeos da subpasta '{subpasta_nome}' para '{pasta_destino}'")
                            baixar_todos_videos_st(videos, pasta_destino)
                        else:
                            st.warning(f"Nenhum vídeo encontrado na subpasta '{subpasta_nome}'")
                        
                        # Atualizar progresso
                        progresso_subpastas.progress((i + 1) / len(subpastas))

# Principal
def main():
    # Inicializar estado da sessão
    if "pagina" not in st.session_state:
        st.session_state.pagina = "inicio"
    
    # Navegação entre páginas
    if st.session_state.pagina == "inicio":
        pagina_inicio()
    elif st.session_state.pagina == "listar_pastas":
        pagina_listar_pastas()
    elif st.session_state.pagina == "listar_videos":
        pagina_listar_videos()
    elif st.session_state.pagina == "baixar_video":
        pagina_baixar_video()
    elif st.session_state.pagina == "subpastas":
        pagina_subpastas()

if __name__ == "__main__":
    main()
