# Panda Videos Downloader

## Descrição
Este projeto é um script em Python para baixar vídeos da plataforma "Panda Videos". Ele oferece funcionalidades para listar pastas, listar vídeos, baixar vídeos individuais ou todos os vídeos de uma pasta específica, através de uma interface de linha de comando.

## Funcionalidades

- **Listar Pastas**: Exibe todas as pastas disponíveis na conta.
- **Listar Vídeos**: Mostra todos os vídeos em uma pasta específica.
- **Baixar Vídeo**: Faz o download de um vídeo específico pelo ID.
- **Baixar Todos**: Baixa todos os vídeos de uma pasta.
- **Barra de Progresso**: Exibe o progresso do download com informações como velocidade e tempo estimado.
- **Múltiplos Métodos de Download**: Tenta diferentes abordagens para garantir o download (oficial, direto ou m3u8).
- **Download via m3u8**: Suporte para download de vídeos em streaming usando ffmpeg.
- **Tipagem Estática**: Uso de tipagem para melhorar a detecção de erros.

## Versões do Código

### Versão Original (test_download.py)
A versão original do script fornece funcionalidades básicas para listar e baixar vídeos da plataforma Panda Videos.

### Nova Versão Melhorada (panda_downloader.py + panda_cli.py)
A nova versão do código traz diversas melhorias:

- **Tipagem Estática**: Uso do módulo `typing` para melhorar a detecção de erros.
- **Tratamento de Erros Robusto**: Melhor tratamento de erros e mensagens mais informativas.
- **Métodos Alternativos de Download**: Sistema que tenta múltiplos métodos quando o primeiro falha.
- **Download via m3u8**: Suporte para baixar vídeos em streaming com seleção de qualidade.
- **Interface Aprimorada**: CLI moderna com emojis e exemplos de uso.
- **Código Modular**: Separação entre a biblioteca de funções e a interface de linha de comando.
- **Melhor Controle de Progresso**: Informações mais detalhadas durante o download.

## Estrutura do Código

### panda_downloader.py (Nova Versão)
Biblioteca principal com funções para:

- `verificar_autenticacao`: Testa a validade da chave de API.
- `listar_pastas`: Lista todas as pastas disponíveis na conta.
- `listar_videos_pasta`: Lista vídeos em uma pasta específica.
- `obter_videos_da_pasta_alternativo`: Método alternativo para listar vídeos quando o principal falha.
- `baixar_video_oficial`: Baixa um vídeo usando o endpoint oficial.
- `baixar_video_alternativo`: Tenta baixar um vídeo usando métodos alternativos.
- `baixar_video_m3u8`: Baixa vídeo a partir de um link m3u8 com seleção de qualidade.
- `download_with_progress`: Realiza download com barra de progresso e informações detalhadas.

### panda_cli.py (Nova Interface)
Interface de linha de comando que utiliza a biblioteca `panda_downloader.py`:

- Argumentos de linha de comando mais intuitivos.
- Exemplos de uso incluídos na ajuda do comando.
- Feedbacks mais claros com uso de emojis.
- Estrutura modular com funções específicas para cada comando.

## Como Usar

### Versão Original
```bash
# Listar todas as pastas disponíveis
python test_download.py pastas

# Listar vídeos de uma pasta específica
python test_download.py listar "Nome da Pasta"

# Baixar um vídeo específico
python test_download.py baixar VIDEO_ID --pasta pasta_destino

# Baixar todos os vídeos de uma pasta
python test_download.py todos "Nome da Pasta" --pasta-destino "downloads/Pasta"
```

### Nova Versão
```bash
# Listar todas as pastas disponíveis
python panda_cli.py pastas

# Listar vídeos de uma pasta específica
python panda_cli.py listar "Nome da Pasta"

# Baixar um vídeo específico
python panda_cli.py baixar VIDEO_ID --pasta pasta_destino

# Baixar todos os vídeos de uma pasta
python panda_cli.py todos "Nome da Pasta" --pasta-destino "downloads/Pasta"

# Baixar todos os vídeos usando o ID da pasta
python panda_cli.py todos-id PASTA_ID --pasta-destino "downloads/Pasta"
```

## Pontos Positivos

- **Organização Modular**: Funções claras para cada tarefa, seguindo o princípio de responsabilidade única.
- **Tratamento de Erros**: Verificação de autenticação e manejo de falhas com métodos alternativos.
- **Interface Amigável**: CLI com vários comandos úteis para diferentes necessidades.
- **Tipagem Estática**: Uso de tipos para melhor detecção de erros em tempo de desenvolvimento.
- **Múltiplos Métodos**: Se um método de download falha, o sistema tenta automaticamente outros métodos.
- **Download via m3u8**: Suporte para vídeos em streaming com seleção de qualidade.

## Sugestões de Melhoria Futuras

- Implementar cache de informações para reduzir chamadas repetidas à API.
- Adicionar suporte para download paralelo de vídeos.
- Criar uma interface gráfica utilizando frameworks como Tkinter ou PyQt.
- Implementar sistema de log para melhor debugging.
- Adicionar opção para retomar downloads interrompidos.

## Requisitos

- Python 3.6+
- Bibliotecas: requests, tqdm, python-dotenv, typing-extensions, ffmpeg (executável)

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/panda-videos-downloader.git
cd panda-videos-downloader

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo .env com sua chave API
echo "PANDA_API_KEY=sua-chave-api" > .env
```

## Nota

Este projeto foi atualizado em novembro de 2023 com melhorias significativas na robustez e funcionalidades. 