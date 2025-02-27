# Pontos de Atenção ao Usar o Panda CLI

## Comandos Disponíveis

O script `panda_cli.py` oferece os seguintes comandos:

```
{baixar, pastas, listar, todos, todos-id, subpastas}
```

**Não existem** os comandos:
- ❌ `listar-id` (erro comum)

## Uso Correto dos Comandos

### 1. Listando Pastas

```bash
# Lista todas as pastas disponíveis
python panda_cli.py pastas
```

### 2. Listando Vídeos de uma Pasta

```bash
# Por nome da pasta
python panda_cli.py listar "Nome da Pasta"

# Não existe comando listar-id, use todos-id com grep para filtrar resultados
python panda_cli.py todos-id ID_DA_PASTA --pasta-destino "temp" | grep "Título"
```

### 3. Baixando Vídeos

```bash
# Baixar um vídeo específico
python panda_cli.py baixar VIDEO_ID --pasta "pasta_destino"

# Baixar todos os vídeos de uma pasta por nome
python panda_cli.py todos "Nome da Pasta" --pasta-destino "downloads/Pasta"

# Baixar todos os vídeos de uma pasta por ID
python panda_cli.py todos-id PASTA_ID --pasta-destino "downloads/Pasta"
```

### 4. Identificando Subpastas

```bash
# Lista todas as subpastas
python panda_cli.py subpastas ID_PASTA_PRINCIPAL

# Filtrar subpastas com padrão específico
python panda_cli.py subpastas ID_PASTA_PRINCIPAL --padrao "^Módulo \d+"

# Baixar todos os vídeos das subpastas identificadas
python panda_cli.py subpastas ID_PASTA_PRINCIPAL --baixar --pasta-destino "downloads/Pasta"
```

## Exemplos de Filtros Úteis

### Filtrar Módulos Solidity (excluindo RUST)

```bash
python panda_cli.py subpastas PASTA_ID --padrao "^Módulo (\d+)($| - (?!RUST))"
```

### Filtrar Apenas Módulos RUST

```bash
python panda_cli.py subpastas PASTA_ID --padrao ".*RUST.*"
```

### Filtrar Intervalo de Módulos

```bash
python panda_cli.py subpastas PASTA_ID --padrao "^Módulo ([6-9]|1[0-3])"
```

## Dicas e Melhores Práticas

1. **Estruturação de Pastas**: Mantenha uma estrutura organizada para downloads
   ```
   downloads/
   ├── Curso_A/
   │   ├── Módulo_1/
   │   └── Módulo_2/
   └── Curso_B/
       ├── Módulo_1/
       └── Módulo_2/
   ```

2. **Verificação Prévia**: Sempre liste o conteúdo antes de iniciar downloads grandes
   ```bash
   # Verifique o conteúdo
   python panda_cli.py listar "Nome da Pasta"
   
   # Só então faça o download
   python panda_cli.py todos "Nome da Pasta" --pasta-destino "downloads/Pasta"
   ```

3. **Lidando com Interrupções**: Se um download for interrompido, você pode continuar de onde parou, pois o script detecta arquivos já baixados

4. **Salvando Metadados**: Mantenha um arquivo markdown com a lista de vídeos para referência futura

5. **Tamanho de Arquivo**: Use `du -sh pasta` para verificar o tamanho total dos downloads

## Erros Comuns

1. ❌ Usar `listar-id` ao invés do fluxo correto
2. ❌ Esquecer de colocar aspas em nomes de pastas com espaço
3. ❌ Não filtrar corretamente ao baixar conteúdo de cursos com módulos misturados (ex: Solidity e RUST)
4. ❌ Criar estruturas de pasta manual ao invés de deixar o script criar automaticamente

## Exemplo de Workflow Completo

```bash
# 1. Listar todas as pastas disponíveis
python panda_cli.py pastas

# 2. Identificar subpastas de um curso
python panda_cli.py subpastas PASTA_ID_CURSO

# 3. Filtrar apenas módulos relevantes
python panda_cli.py subpastas PASTA_ID_CURSO --padrao "^Módulo \d+($| - (?!RUST))"

# 4. Baixar todos os módulos filtrados
python panda_cli.py subpastas PASTA_ID_CURSO --padrao "^Módulo \d+($| - (?!RUST))" --baixar --pasta-destino "downloads/Nome_Do_Curso"

# 5. Verificar tamanho total do download
du -sh "downloads/Nome_Do_Curso"
``` 