#!/bin/bash

# Pasta de destino para os arquivos
PASTA_DESTINO="downloads/Acelerador_Cripto/Price_Action_Avançado"

# ID da pasta Price Action Avançado
PASTA_ID="8d4a94da-4bb2-4794-8181-ee4f163eb965"

echo "===== Tentando baixar vídeos do módulo Price Action Avançado ====="
echo "ID da pasta: $PASTA_ID"
echo "Pasta de destino: $PASTA_DESTINO"
echo ""

# Cria o diretório se não existir
mkdir -p "$PASTA_DESTINO"

# Tenta baixar os vídeos com o modo verbose
echo "Verificando vídeos disponíveis..."
python3 -u panda_cli.py todos-id "$PASTA_ID" --pasta-destino "$PASTA_DESTINO"

# Verifica se algum vídeo foi baixado
NUM_VIDEOS=$(find "$PASTA_DESTINO" -name "*.mp4*" | wc -l)

if [ $NUM_VIDEOS -gt 0 ]; then
    echo ""
    echo "✅ Foram baixados $NUM_VIDEOS vídeos para a pasta $PASTA_DESTINO"
    
    # Gera o README
    echo "Gerando README.md..."
    
    # Cabeçalho do README
    cat > "$PASTA_DESTINO/README.md" << EOL
# Curso de Price Action Avançado

## Aulas
EOL
    
    # Adicionar cada vídeo ao README
    numero=1
    
    for arquivo in $(find "$PASTA_DESTINO" -name "*.mp4*" | sort); do
        nome_arquivo=$(basename "$arquivo")
        
        # Formatar o nome do arquivo para um título limpo
        # Remove extensões e substitui underscores por espaços
        nome_limpo=${nome_arquivo%.*}      # Remove a primeira extensão
        nome_limpo=${nome_limpo%.*}        # Remove a segunda extensão se houver (.mp4.mp4)
        nome_limpo=${nome_limpo//_/ }      # Substitui _ por espaço
        
        # Adicionar apenas o título limpo ao README
        echo "$numero. $nome_limpo" >> "$PASTA_DESTINO/README.md"
        
        ((numero++))
    done
    
    echo "✅ README.md gerado com $NUM_VIDEOS vídeos."
else
    echo ""
    echo "❌ Nenhum vídeo encontrado ou baixado para o módulo Price Action Avançado."
    
    # Cria um README explicativo
    cat > "$PASTA_DESTINO/README.md" << EOL
# Curso de Price Action Avançado

## Aviso
Este módulo não contém vídeos disponíveis atualmente.
Possíveis razões:
1. Os vídeos podem ter sido removidos temporariamente
2. O módulo pode estar em manutenção
3. Pode haver restrições de acesso a este conteúdo
EOL

    echo "✅ README.md explicativo criado."
fi

echo ""
echo "===== Processo concluído =====" 