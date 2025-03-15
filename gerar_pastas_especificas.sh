#!/bin/bash

# Diretório base do Acelerador Cripto
BASE_DIR="downloads/Acelerador_Cripto"

# Lista de pastas específicas para gerar índices
PASTAS=(
    "Avenue"
    "Binance"
    "BingX_Futuros"
    "Boas_vindas"
    "Candlesticks"
    "Controle_Emocional_Aplicado_ao_Trading"
    "Declaração_Cripto"
    "Encontro_Individual"
    "Essência_da_Análise_Técnica"
)

# Função para criar um arquivo README.md para uma pasta específica
criar_readme() {
    local pasta_completa="$1"
    local nome_pasta=$(basename "$pasta_completa")
    local nome_formatado=${nome_pasta//_/ }
    local arquivo_readme="$pasta_completa/README.md"
    
    echo "Gerando índice para: $nome_formatado"
    
    # Lista de arquivos de vídeo na pasta
    arquivos=($(find "$pasta_completa" -name "*.mp4*" | sort))
    
    if [ ${#arquivos[@]} -eq 0 ]; then
        echo "Nenhum vídeo encontrado em $pasta_completa. Pulando..."
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
        echo "$numero. $nome_limpo" >> "$arquivo_readme"
        
        ((numero++))
    done
    
    echo "✅ Índice gerado para $nome_formatado com ${#arquivos[@]} vídeos."
}

# Verifica se o diretório base existe
if [ ! -d "$BASE_DIR" ]; then
    echo "Diretório $BASE_DIR não encontrado!"
    exit 1
fi

echo "===== Gerando índices para pastas específicas do Acelerador Cripto ====="

# Processa cada pasta específica
for pasta in "${PASTAS[@]}"; do
    caminho_completo="$BASE_DIR/$pasta"
    if [ -d "$caminho_completo" ]; then
        criar_readme "$caminho_completo"
        echo ""
    else
        echo "⚠️ Pasta não encontrada: $pasta"
    fi
done

echo "===== Geração de índices concluída! =====" 