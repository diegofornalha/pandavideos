#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from panda_downloader import (
    verificar_autenticacao,
    listar_pastas,
    listar_videos_pasta,
    baixar_video,
    baixar_todos_videos
)

def formatar_tamanho(tamanho_bytes):
    """Formata o tamanho em bytes para um formato legível."""
    for unidade in ['B', 'KB', 'MB', 'GB']:
        if tamanho_bytes < 1024.0:
            return f"{tamanho_bytes:.2f} {unidade}"
        tamanho_bytes /= 1024.0
    return f"{tamanho_bytes:.2f} TB"

def comando_baixar(args):
    """Executa o comando para baixar um vídeo específico."""
    print(f"🎬 Baixando vídeo ID: {args.video_id}")
    if not os.path.exists(args.pasta):
        os.makedirs(args.pasta)
    resultado = baixar_video(args.video_id, args.pasta)
    if resultado:
        print("✅ Download concluído com sucesso!")
    else:
        print("❌ Falha no download. Verifique os erros acima.")
        sys.exit(1)

def comando_listar_pastas(args):
    """Executa o comando para listar todas as pastas disponíveis."""
    listar_pastas()

def comando_listar_videos(args):
    """Executa o comando para listar vídeos de uma pasta específica."""
    # Encontrar ID da pasta pelo nome
    pastas = listar_pastas()
    pasta_id = None
    pasta_nome = None
    
    for pasta in pastas:
        if pasta.get('name', '').lower() == args.pasta_nome.lower():
            pasta_id = pasta.get('id')
            pasta_nome = pasta.get('name')
            break
    
    if pasta_id:
        videos = listar_videos_pasta(pasta_id, pasta_nome)
        if not videos:
            print(f"⚠️ Nenhum vídeo encontrado na pasta '{pasta_nome}'")
            sys.exit(1)
    else:
        print(f"❌ Pasta '{args.pasta_nome}' não encontrada")
        sys.exit(1)

def comando_baixar_todos(args):
    """Executa o comando para baixar todos os vídeos de uma pasta."""
    # Encontrar ID da pasta pelo nome
    pastas = listar_pastas()
    pasta_id = None
    pasta_nome = None
    
    for pasta in pastas:
        if pasta.get('name', '').lower() == args.pasta_nome.lower():
            pasta_id = pasta.get('id')
            pasta_nome = pasta.get('name')
            break
    
    if pasta_id:
        # Definir pasta de destino
        pasta_destino = args.pasta_destino
        if not pasta_destino:
            # Se não especificado, criar uma pasta com o nome da pasta original
            pasta_destino = os.path.join('downloads', pasta_nome.replace(' ', '_'))
        
        # Garantir que a pasta de destino existe
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
        
        # Listar e baixar os vídeos
        videos = listar_videos_pasta(pasta_id, pasta_nome)
        if videos:
            print(f"📁 Baixando {len(videos)} vídeos da pasta '{pasta_nome}' para '{pasta_destino}'")
            baixar_todos_videos(videos, pasta_destino)
        else:
            print(f"⚠️ Nenhum vídeo encontrado na pasta '{pasta_nome}'")
            sys.exit(1)
    else:
        print(f"❌ Pasta '{args.pasta_nome}' não encontrada")
        sys.exit(1)

def comando_baixar_todos_id(args):
    """Executa o comando para baixar todos os vídeos de uma pasta usando ID."""
    pasta_id = args.pasta_id
    
    # Obter nome da pasta (para exibição)
    pastas = listar_pastas()
    pasta_nome = None
    for pasta in pastas:
        if pasta.get('id') == pasta_id:
            pasta_nome = pasta.get('name')
            break
    
    if not pasta_nome:
        pasta_nome = f"Pasta_{pasta_id}"  # Nome genérico caso não encontre
    
    # Definir pasta de destino
    pasta_destino = args.pasta_destino
    if not pasta_destino:
        # Se não especificado, criar uma pasta com o nome da pasta original
        pasta_destino = os.path.join('downloads', pasta_nome.replace(' ', '_'))
    
    # Garantir que a pasta de destino existe
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
    
    # Listar e baixar os vídeos
    videos = listar_videos_pasta(pasta_id, pasta_nome)
    if videos:
        print(f"📁 Baixando {len(videos)} vídeos da pasta '{pasta_nome}' para '{pasta_destino}'")
        baixar_todos_videos(videos, pasta_destino)
    else:
        print(f"⚠️ Nenhum vídeo encontrado na pasta ID '{pasta_id}'")
        sys.exit(1)

def main():
    """Função principal com interface de linha de comando."""
    parser = argparse.ArgumentParser(
        description='🐼 Downloader de Vídeos do Panda Videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos de uso:
  python panda_cli.py pastas                    # Lista todas as pastas disponíveis
  python panda_cli.py listar "Nome da Pasta"    # Lista vídeos de uma pasta específica
  python panda_cli.py baixar abc123             # Baixa o vídeo com ID abc123
  python panda_cli.py todos "Nome da Pasta"     # Baixa todos os vídeos da pasta
  python panda_cli.py todos-id abc123           # Baixa todos os vídeos da pasta com ID abc123
'''
    )
    
    # Definir os subcomandos
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponíveis')
    subparsers.required = True
    
    # Comando para baixar um vídeo específico
    baixar_parser = subparsers.add_parser('baixar', help='Baixar um vídeo específico')
    baixar_parser.add_argument('video_id', help='ID do vídeo a ser baixado')
    baixar_parser.add_argument('--pasta', '-p', default='downloads', help='Pasta de destino (padrão: downloads)')
    baixar_parser.set_defaults(func=comando_baixar)
    
    # Comando para listar pastas
    pastas_parser = subparsers.add_parser('pastas', help='Listar todas as pastas disponíveis')
    pastas_parser.set_defaults(func=comando_listar_pastas)
    
    # Comando para listar vídeos de uma pasta
    listar_parser = subparsers.add_parser('listar', help='Listar vídeos de uma pasta específica')
    listar_parser.add_argument('pasta_nome', help='Nome da pasta')
    listar_parser.set_defaults(func=comando_listar_videos)
    
    # Comando para baixar todos os vídeos de uma pasta
    todos_parser = subparsers.add_parser('todos', help='Baixar todos os vídeos de uma pasta')
    todos_parser.add_argument('pasta_nome', help='Nome da pasta')
    todos_parser.add_argument('--pasta-destino', '-p', default=None, 
                             help='Pasta de destino (padrão: nome da pasta dentro de downloads)')
    todos_parser.set_defaults(func=comando_baixar_todos)
    
    # Comando para baixar todos os vídeos de uma pasta usando o ID da pasta
    todos_id_parser = subparsers.add_parser('todos-id', help='Baixar todos os vídeos de uma pasta usando o ID da pasta')
    todos_id_parser.add_argument('pasta_id', help='ID da pasta')
    todos_id_parser.add_argument('--pasta-destino', '-p', default=None, 
                             help='Pasta de destino (padrão: nome da pasta dentro de downloads)')
    todos_id_parser.set_defaults(func=comando_baixar_todos_id)
    
    # Analisar argumentos
    args = parser.parse_args()
    
    # Verificar autenticação antes de continuar
    print("🔑 Testando autenticação com a API do Panda Videos...")
    if not verificar_autenticacao():
        print("❌ Falha na autenticação. Verifique se a variável de ambiente PANDA_API_KEY está configurada corretamente.")
        sys.exit(1)
    
    # Executar a função associada ao comando escolhido
    args.func(args)

if __name__ == "__main__":
    main() 