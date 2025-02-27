# Guia de Referência para o Panda CLI

## Comandos Disponíveis

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `pastas` | Lista todas as pastas disponíveis | `python panda_cli.py pastas` |
| `listar` | Lista vídeos em uma pasta específica por nome | `python panda_cli.py listar "Nome da Pasta"` |
| `baixar` | Baixa um vídeo específico pelo ID | `python panda_cli.py baixar VIDEO_ID --pasta pasta_destino` |
| `todos` | Baixa todos os vídeos de uma pasta (usando nome) | `python panda_cli.py todos "Nome da Pasta" --pasta-destino "downloads/Pasta"` |
| `todos-id` | Baixa todos os vídeos de uma pasta (usando ID) | `python panda_cli.py todos-id PASTA_ID --pasta-destino "downloads/Pasta"` |
| `subpastas` | Identifica subpastas/módulos de um curso | `python panda_cli.py subpastas PASTA_ID` |

## Pontos de Atenção

### 1. Comandos inexistentes
- ❌ **Erro comum**: Usar `listar-id` que não existe
- ✅ **Correto**: Use `todos-id` para referenciar uma pasta pelo ID

```
# Errado
python panda_cli.py listar-id PASTA_ID

# Correto
python panda_cli.py todos-id PASTA_ID --pasta-destino "temp"
```

### 2. Filtragem de pastas e módulos
- Para filtrar módulos específicos, use o parâmetro `--padrao` com expressões regulares:

```
# Filtrar apenas módulos RUST
python panda_cli.py subpastas PASTA_ID --padrao ".*RUST.*"

# Filtrar módulos Solidity (excluir módulos RUST)
python panda_cli.py subpastas PASTA_ID --padrao "^Módulo ([6-9]|1[0-3])($| - (?!(RUST|Rust)))"
```

### 3. Estrutura hierárquica de pastas
- O Panda Videos não exibe naturalmente a estrutura hierárquica
- A função `subpastas` ajuda a descobrir as subpastas relacionadas a um curso específico
- Use padrões específicos para filtrar e identificar apenas os módulos desejados

### 4. Download de pastas completas
- Para baixar todos os módulos de uma vez:

```
# Baixar todos os módulos de um curso, organizando em pastas
python panda_cli.py subpastas PASTA_ID --baixar --pasta-destino "downloads/Curso" --padrao "PADRÃO"
```

### 5. Verificação de downloads
- Sempre verifique se os downloads foram concluídos corretamente:

```
# Verificar tamanho das pastas baixadas
du -sh "downloads/Pasta/*"

# Listar arquivos de uma pasta específica
ls -la "downloads/Pasta/Subpasta"
```

### 6. Interrupções de download
- Se um download for interrompido, reinicie especificando apenas os módulos restantes
- Use padrões mais específicos em `--padrao` para selecionar apenas os módulos faltantes

## Exemplos de Uso Avançado

### Baixar apenas módulos específicos:
```
# Baixar apenas módulos 6 a 13 de Solidity
python panda_cli.py subpastas ID_CURSO --baixar --pasta-destino "downloads/Pasta" --padrao "^Módulo ([6-9]|1[0-3])($| - (?!(RUST|Rust)))"
```

### Verificar conteúdo de um módulo sem baixar:
```
# Listar vídeos do módulo sem baixar
python panda_cli.py todos-id ID_MÓDULO --pasta-destino "temp" | grep "Título"
```

### Baixar vídeos em ordem numérica:
Os vídeos são baixados na ordem em que aparecem na API, que nem sempre segue a ordem numérica. Para garantir melhor organização, os arquivos são salvos com seus nomes originais preservando a sequência. 