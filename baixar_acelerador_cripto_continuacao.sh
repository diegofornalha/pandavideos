#!/bin/bash

# Cria a pasta principal se não existir
mkdir -p downloads/Acelerador_Cripto

echo "===== Continuando download dos módulos adicionais do Acelerador Cripto ====="

# Array com os IDs e nomes das pastas que ainda precisam ser baixadas
# Removidas as pastas: Exchanges_Descentralizadas_e_Wallets, Geopolítica_e_Economia_Internacional, 
# Gerenciamento_do_Risco_e_Operações, Gestão_do_Risco_no_DeFi, Império_Imobiliário_Global_Tokenizado e Wyckoff
# que já foram baixadas anteriormente.
declare -a pastas=(
    "1e0cb014-5def-47a1-a4f3-b1c133d27f13:Indicadores_Técnicos"
    "5e9fe8dc-278d-4e1b-959f-ee13ff13903e:Método_MicroCoins100x_Pro"
    "344764b3-b471-4bb2-aab3-536c87df1817:Método_Operac_Relamp"
    "3c05c917-1a58-4e00-9a7f-463f943b3837:Método_Trader_Institucional_Smart_Money"
    "eaccc20e-9e2f-4b30-a5ca-1baaf214f30d:O_Milagre_das_Finanças_Descentralizadas"
    "44f2612e-3005-40d2-addd-98303b6a7dfe:Outras_Estratégias_de_Entrada"
    "d41db3e6-2d0b-4388-829b-79a76eb7c338:Padrões_Gráficos_Escondidos"
    "8d4a94da-4bb2-4794-8181-ee4f163eb965:Price_Action_Avançado"
    "8824e73d-1651-4a8c-8f2a-76dd142ba6e5:Primeiros_Passos_no_CriptoMercado"
    "03c730bc-b4a2-4c45-8363-540fc9875737:Scalpings"
    "41cda018-1311-46df-82c2-a17c25dc15ad:Swing_Trading"
    "014e7a77-bd20-4a3f-bffb-286e34d2f3b4:Técnicas_e_Ferramentas_Complementares"
)

# Função para verificar espaço em disco disponível
verificar_espaco() {
    # Obtém o espaço livre em bytes no diretório de downloads
    espaco_livre=$(df -k "downloads/Acelerador_Cripto" | awk 'NR==2 {print $4}')
    # Converte para GB para facilitar a leitura
    espaco_livre_gb=$(echo "scale=2; $espaco_livre / 1024 / 1024" | bc)
    
    echo "Espaço livre em disco: ${espaco_livre_gb}GB"
    
    # Se o espaço livre for menor que 2GB, exibe um aviso
    if (( $(echo "$espaco_livre_gb < 2" | bc -l) )); then
        echo "⚠️ ALERTA: Espaço em disco muito baixo (menos de 2GB disponível)!"
        echo "Você pode cancelar o download e liberar espaço antes de continuar."
        echo "Pressione CTRL+C nos próximos 10 segundos para cancelar ou espere para continuar."
        sleep 10
    fi
}

# Função para limpar arquivos parciais ou corrompidos
limpar_arquivos_incompletos() {
    local pasta="$1"
    
    # Encontrar arquivos muito pequenos (provavelmente incompletos)
    pequenos_arquivos=$(find "$pasta" -name "*.mp4*" -size -10M)
    
    if [ -n "$pequenos_arquivos" ]; then
        echo "🧹 Encontrados arquivos pequenos/incompletos em $pasta:"
        echo "$pequenos_arquivos"
        echo "Removendo arquivos incompletos..."
        
        # Remove os arquivos pequenos
        for arquivo in $pequenos_arquivos; do
            rm -f "$arquivo"
            echo "  ✓ Removido: $(basename "$arquivo")"
        done
    fi
}

# Percorre todas as pastas e baixa os vídeos
for pasta in "${pastas[@]}"; do
    # Verifica o espaço em disco antes de cada pasta
    verificar_espaco
    
    # Separa o ID e o nome da pasta
    ID=$(echo $pasta | cut -d':' -f1)
    NOME=$(echo $pasta | cut -d':' -f2)
    
    echo ""
    echo "===== Baixando pasta: $NOME (ID: $ID) ====="
    echo ""
    
    # Cria o diretório com o nome correto
    mkdir -p "downloads/Acelerador_Cripto/$NOME"
    
    # Limpa arquivos incompletos se a pasta já existir
    limpar_arquivos_incompletos "downloads/Acelerador_Cripto/$NOME"
    
    # Executa o comando para baixar os vídeos
    python3 panda_cli.py todos-id "$ID" --pasta-destino "downloads/Acelerador_Cripto/$NOME"
    
    # Verifica se o download foi bem-sucedido
    if [ $? -ne 0 ]; then
        echo "⚠️ Erro no download da pasta $NOME. Verifique os logs acima."
        
        # Gera o README mesmo com possíveis falhas
        criar_readme "downloads/Acelerador_Cripto/$NOME"
        
        # Pergunta se deseja continuar para a próxima pasta
        read -p "Deseja continuar para a próxima pasta? (s/n): " continuar
        if [ "$continuar" != "s" ]; then
            echo "Download interrompido pelo usuário."
            exit 1
        fi
    else
        # Gera o README para a pasta atual
        criar_readme "downloads/Acelerador_Cripto/$NOME"
    fi
    
    # Aguarda 3 segundos entre cada pasta para evitar sobrecarga na API
    echo ""
    echo "Aguardando 3 segundos antes da próxima pasta..."
    sleep 3
done

echo ""
echo "===== Download concluído! ====="
echo "Todos os vídeos foram salvos em: downloads/Acelerador_Cripto/" 

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

echo ""
echo "===== Verificando e atualizando todos os índices ====="

# Para cada pasta na array, atualiza o README
for pasta in "${pastas[@]}"; do
    # Separa o nome da pasta
    NOME=$(echo $pasta | cut -d':' -f2)
    caminho_completo="downloads/Acelerador_Cripto/$NOME"
    
    # Verifica se a pasta existe
    if [ -d "$caminho_completo" ]; then
        criar_readme "$caminho_completo"
    fi
    
    echo ""
done

echo "===== Atualização de índices concluída! =====" 