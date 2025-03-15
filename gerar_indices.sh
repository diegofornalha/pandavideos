#!/bin/bash

# Diretório base do Acelerador Cripto
BASE_DIR="downloads/Acelerador_Cripto"

# Função para criar um arquivo README.md para uma pasta específica
criar_readme() {
    local pasta="$1"
    local nome_pasta=$(basename "$pasta")
    local nome_formatado=${nome_pasta//_/ }
    local arquivo_readme="$pasta/README.md"
    
    echo "Gerando índice para: $nome_formatado"
    
    # Lista de arquivos de vídeo na pasta
    arquivos=($(find "$pasta" -name "*.mp4*" | sort))
    
    if [ ${#arquivos[@]} -eq 0 ]; then
        echo "Nenhum vídeo encontrado em $pasta. Pulando..."
        return
    fi
    
    # Cabeçalho do README
    cat > "$arquivo_readme" << EOL
# Curso de $nome_formatado

## Aulas
EOL
    
    # Adicionar cada vídeo ao README
    numero=1
    
    for arquivo in "${arquivos[@]}"; do
        nome_arquivo=$(basename "$arquivo")
        
        # Formatar o nome do arquivo para um título limpo
        # Remove extensões e substitui underscores por espaços
        nome_limpo=${nome_arquivo%.*}      # Remove a primeira extensão
        nome_limpo=${nome_limpo%.*}        # Remove a segunda extensão se houver (.mp4.mp4)
        nome_limpo=${nome_limpo//_/ }      # Substitui _ por espaço
        
        # Adicionar apenas o título limpo ao README
        echo -e "\n$numero. $nome_limpo" >> "$arquivo_readme"
        
        ((numero++))
    done
    
    echo "✅ Índice gerado para $nome_formatado com ${#arquivos[@]} vídeos."
}

# Verifica se o diretório base existe
if [ ! -d "$BASE_DIR" ]; then
    echo "Diretório $BASE_DIR não encontrado!"
    exit 1
fi

echo "===== Gerando índices para todas as pastas do Acelerador Cripto ====="

# Encontra todas as subpastas do diretório base
subpastas=($(find "$BASE_DIR" -mindepth 1 -maxdepth 1 -type d | sort))

if [ ${#subpastas[@]} -eq 0 ]; then
    echo "Nenhuma subpasta encontrada em $BASE_DIR!"
    exit 1
fi

# Processa cada subpasta
for pasta in "${subpastas[@]}"; do
    criar_readme "$pasta"
    echo ""
done

echo "===== Geração de índices concluída! =====" 