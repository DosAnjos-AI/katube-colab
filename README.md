# Katube Colab

Sistema modular para download de áudio do YouTube com persistência no Google Drive e exportação automática de metadados em CSV.

## Funcionalidades

- Download de áudio em alta qualidade com formato configurável
- Suporte para vídeos individuais, playlists, canais e arquivos TXT
- Exportação automática de metadados completos em CSV
- Sistema de checkpoint para retomada de downloads interrompidos
- Detecção automática de duplicatas
- Delays configuráveis anti-bloqueio
- Logs automáticos de erros e downloads
- Estrutura organizada de pastas no Google Drive

## Formatos de Áudio Suportados

- **MP3** (padrão): Formato universal, boa compatibilidade
- **FLAC**: Alta qualidade, sem perda
- **WAV**: Áudio sem compressão
- **M4A**: Formato Apple, boa qualidade
- **OPUS**: Formato moderno, eficiente

## Estrutura de Pastas no Drive

```
MyDrive/Katube_Download/
├── Playlist_PLxxx/
│   ├── VIDEO_ID_1/
│   │   └── VIDEO_ID_1.mp3
│   ├── VIDEO_ID_2/
│   │   └── VIDEO_ID_2.mp3
│   ├── metadados.csv
│   └── checkpoint.json
├── Canal_UCxxx/
│   ├── VIDEO_ID_1/
│   │   └── VIDEO_ID_1.mp3
│   ├── metadados.csv
│   └── checkpoint.json
├── video_ABC123/
│   ├── ABC123/
│   │   └── ABC123.mp3
│   └── metadados.csv
├── txt_01/
│   ├── VIDEO_ID_1/
│   │   └── VIDEO_ID_1.mp3
│   ├── metadados.csv
│   └── checkpoint.json
└── logs/
    ├── download_2025-01-15.log
    └── errors_2025-01-15.log
```

## Início Rápido

### 1. Abrir no Google Colab

```python
# Clone do repositório
!git clone -b downloader_PDSI https://github.com/DosAnjos-AI/katube-colab.git
%cd katube-colab

# Instalar dependências
!pip install -q -r requirements.txt
```

### 2. Importar Módulos

```python
from downloaders import YouTubeDownloader, DriveManager
from config import Config
```

### 3. Configurar e Inicializar

```python
# Configurar formato de áudio (opcional)
Config.AUDIO_FORMAT = 'mp3'
Config.AUDIO_QUALITY = 0  # 0 = melhor qualidade

# Montar Google Drive
drive_manager = DriveManager()
drive_manager.mount_drive()
drive_manager.setup_folder_structure()

# Inicializar downloader
downloader = YouTubeDownloader()
```

### 4. Fazer Download

```python
# Vídeo individual
result = downloader.download_from_url("https://www.youtube.com/watch?v=VIDEO_ID")

# Playlist
result = downloader.download_from_url("https://www.youtube.com/playlist?list=PLAYLIST_ID")

# Canal
result = downloader.download_from_url("https://www.youtube.com/@username")

# Arquivo TXT
result = downloader.download_from_txt("urls.txt")
```

## Metadados Exportados (CSV)

O sistema gera automaticamente um arquivo CSV com os seguintes metadados:

### Informações Básicas
- `video_id`: ID único do vídeo
- `title`: Título do vídeo
- `duration_seconds`: Duração em segundos
- `duration_formatted`: Duração formatada (ex: "5m 30s")
- `upload_date`: Data de upload
- `url`: URL completa do vídeo

### Informações do Canal
- `channel_name`: Nome do canal/uploader
- `channel_id`: ID do canal
- `subscriber_count`: Número de inscritos do canal

### Estatísticas
- `view_count`: Número de visualizações
- `like_count`: Número de likes
- `comment_count`: Número de comentários

### Categorização
- `category`: Categoria do vídeo
- `tags`: Tags separadas por vírgula
- `description`: Descrição completa
- `language`: Idioma do vídeo

### Informações Técnicas
- `audio_format`: Formato do áudio baixado
- `audio_quality`: Qualidade configurada (kbps)
- `filesize_bytes`: Tamanho do arquivo em bytes
- `filesize_formatted`: Tamanho formatado (ex: "5.2 MB")
- `download_date`: Data e hora do download
- `download_status`: Status (success/failed/pending)
- `collection_type`: Tipo (video/playlist/channel/txt)

**Separador do CSV**: `|` (pipe) para evitar conflitos com vírgulas em títulos e descrições.

## Sistema de Checkpoint

O sistema salva automaticamente o progresso dos downloads em `checkpoint.json`.

### Funcionalidades

- Retoma downloads automaticamente de onde parou
- Registra vídeos processados e falhados
- Permite interromper e continuar downloads grandes
- Mantém histórico de última atualização

### Estrutura do Checkpoint

```json
{
  "url": "https://www.youtube.com/playlist?list=PLxxx",
  "total_videos": 150,
  "processed": ["video_id_1", "video_id_2", "..."],
  "failed": ["video_id_x"],
  "last_update": "2025-01-15 14:30:00"
}
```

### Como Retomar um Download

Basta executar novamente o mesmo comando de download. O sistema:
1. Carrega o checkpoint existente
2. Verifica quais vídeos já foram processados
3. Continua apenas com os vídeos pendentes

## Configurações Disponíveis

### Áudio

```python
Config.AUDIO_FORMAT = 'mp3'  # Formato: mp3, flac, wav, m4a, opus
Config.AUDIO_QUALITY = 0     # 0 = melhor, ou kbps específico
```

### Comportamento

```python
Config.SKIP_EXISTING = True      # Pular arquivos já baixados
Config.DELAY_MIN = 10            # Delay mínimo entre downloads (segundos)
Config.DELAY_MAX = 20            # Delay máximo entre downloads (segundos)
Config.MAX_DOWNLOADS = 0         # Limite de downloads (0 = sem limite)
```

### CSV e Checkpoint

```python
Config.CSV_ENABLED = True        # Gerar CSV de metadados
Config.CHECKPOINT_ENABLED = True # Habilitar checkpoint
Config.ENABLE_FILE_LOG = True    # Salvar logs em arquivo
```

### Filtros Avançados

```python
Config.MIN_DURATION = 30         # Duração mínima (segundos)
Config.MAX_DURATION = 7200       # Duração máxima (segundos)
Config.SKIP_LIVE_STREAMS = True  # Pular transmissões ao vivo
Config.SKIP_SHORTS = False       # Pular YouTube Shorts
```

## Formato do Arquivo TXT

Para downloads em lote, crie um arquivo `.txt` com uma URL por linha:

```
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
https://www.youtube.com/playlist?list=PLAYLIST_ID
https://www.youtube.com/@username
```

O sistema processa automaticamente todos os tipos de URL misturados.

## Exemplos de Uso

### Exemplo 1: Download de Playlist com Configurações Personalizadas

```python
from downloaders import YouTubeDownloader
from config import Config

# Configurações personalizadas
Config.AUDIO_FORMAT = 'flac'
Config.AUDIO_QUALITY = 0
Config.DELAY_MIN = 15
Config.DELAY_MAX = 25
Config.MAX_DOWNLOADS = 10  # Baixar apenas os 10 primeiros

# Download
downloader = YouTubeDownloader()
result = downloader.download_from_url("https://www.youtube.com/playlist?list=PLxxx")

# Resultado
print(f"Sucesso: {result['stats']['successful']}")
print(f"CSV: {result['csv_path']}")
```

### Exemplo 2: Análise de Metadados

```python
import pandas as pd

# Carregar CSV
csv_path = "/content/drive/MyDrive/Katube_Download/Playlist_PLxxx/metadados.csv"
df = pd.read_csv(csv_path, sep='|')

# Análises
print(f"Total de vídeos: {len(df)}")
print(f"Duração total: {df['duration_seconds'].sum() / 3600:.2f} horas")
print(f"Tamanho total: {df['filesize_bytes'].sum() / 1024 / 1024:.2f} MB")

# Top 5 mais vistos
top_videos = df.nlargest(5, 'view_count')[['title', 'view_count']]
print(top_videos)
```

### Exemplo 3: Retomar Download Interrompido

```python
# Se um download foi interrompido, basta executar novamente
playlist_url = "https://www.youtube.com/playlist?list=PLxxx"

# O sistema automaticamente:
# 1. Carrega o checkpoint
# 2. Verifica o CSV
# 3. Pula vídeos já baixados
# 4. Continua de onde parou

result = downloader.download_from_url(playlist_url)
```

### Exemplo 4: Filtrar CSV por Critérios

```python
import pandas as pd

csv_path = "/content/drive/MyDrive/Katube_Download/Playlist_PLxxx/metadados.csv"
df = pd.read_csv(csv_path, sep='|')

# Filtrar apenas vídeos com mais de 1 milhão de views
popular = df[df['view_count'] > 1000000]

# Filtrar vídeos de um canal específico
canal = df[df['channel_name'] == 'Nome do Canal']

# Filtrar por duração (entre 5 e 15 minutos)
media = df[(df['duration_seconds'] >= 300) & (df['duration_seconds'] <= 900)]

# Salvar filtrado
popular.to_csv('videos_populares.csv', sep='|', index=False)
```

## Verificações e Validações

### Verificar Integridade

```python
# Verifica se todos os arquivos do CSV existem fisicamente
from pathlib import Path
import pandas as pd

csv_path = "/content/drive/MyDrive/Katube_Download/Playlist_PLxxx/metadados.csv"
download_folder = "/content/drive/MyDrive/Katube_Download/Playlist_PLxxx"

df = pd.read_csv(csv_path, sep='|')
missing = []

for idx, row in df.iterrows():
    if row['download_status'] == 'success':
        video_id = row['video_id']
        audio_file = Path(download_folder) / video_id / f"{video_id}.{row['audio_format']}"
        if not audio_file.exists():
            missing.append(video_id)

print(f"Arquivos faltando: {len(missing)}")
```

### Validar Configurações

```python
# Verifica se todas as configurações são válidas
validation = Config.validate()

if validation['valid']:
    print("Configurações OK!")
else:
    for issue in validation['issues']:
        print(f"Problema: {issue}")
```

### Verificar Status do Checkpoint

```python
import json
from pathlib import Path

checkpoint_path = Path("/content/drive/MyDrive/Katube_Download/Playlist_PLxxx/checkpoint.json")

if checkpoint_path.exists():
    with open(checkpoint_path, 'r') as f:
        checkpoint = json.load(f)
    
    total = checkpoint['total_videos']
    processed = len(checkpoint['processed'])
    pendentes = total - processed
    
    print(f"Total: {total}")
    print(f"Processados: {processed}")
    print(f"Pendentes: {pendentes}")
```

## Utilitários

### Baixar CSV para o Computador

```python
from google.colab import files

csv_path = "/content/drive/MyDrive/Katube_Download/Playlist_PLxxx/metadados.csv"
files.download(csv_path)
```

### Exportar Lista de Títulos

```python
import pandas as pd

csv_path = "/content/drive/MyDrive/Katube_Download/Playlist_PLxxx/metadados.csv"
df = pd.read_csv(csv_path, sep='|')

with open('titulos.txt', 'w', encoding='utf-8') as f:
    for idx, row in df.iterrows():
        f.write(f"{idx+1}. {row['title']}\n")
```

### Limpeza de Pastas Vazias

```python
drive_manager = DriveManager()
removed = drive_manager.cleanup_empty_folders()
print(f"Pastas vazias removidas: {removed}")
```

### Resumo Geral

```python
summary = drive_manager.get_download_summary()

print(f"Total de pastas: {summary['total_folders']}")
print(f"Total de arquivos: {summary['total_files']}")
print(f"Tamanho total: {summary['total_size_formatted']}")
```

## Troubleshooting

### Problema: Download falha com erro de rede

**Solução**: Aumente os delays entre downloads

```python
Config.DELAY_MIN = 20
Config.DELAY_MAX = 30
```

### Problema: Erro "yt-dlp not found"

**Solução**: Reinstale o yt-dlp

```bash
!pip install --upgrade yt-dlp
```

### Problema: CSV não está sendo gerado

**Solução**: Verifique se está habilitado

```python
Config.CSV_ENABLED = True
```

### Problema: Checkpoint não retoma corretamente

**Solução**: Verifique se está habilitado e se o arquivo existe

```python
Config.CHECKPOINT_ENABLED = True

# Verificar se checkpoint existe
from pathlib import Path
checkpoint_path = Path("/content/drive/MyDrive/Katube_Download/Playlist_PLxxx/checkpoint.json")
print(f"Checkpoint existe: {checkpoint_path.exists()}")
```

### Problema: Vídeos privados ou removidos

**Comportamento**: O sistema registra como "failed" no CSV e continua com os próximos vídeos.

**Como verificar**:

```python
import pandas as pd

csv_path = "/content/drive/MyDrive/Katube_Download/Playlist_PLxxx/metadados.csv"
df = pd.read_csv(csv_path, sep='|')

failed = df[df['download_status'] == 'failed']
print(f"Vídeos falhados: {len(failed)}")
```

## Requisitos

- Python 3.8+
- Google Colab (ou ambiente local com Google Drive montado)
- Bibliotecas:
  - yt-dlp >= 2023.12.30
  - pandas >= 2.0.0

## Estrutura do Projeto

```
katube-colab/
├── config.py                   # Configurações centralizadas
├── utils.py                    # Funções auxiliares
├── requirements.txt            # Dependências
├── README.md                   # Este arquivo
├── colab_setup.ipynb           # Notebook principal
└── downloaders/
    ├── __init__.py             # Exports dos módulos
    ├── youtube_downloader.py   # Core do download
    ├── metadata_manager.py     # Gerenciamento de CSV
    ├── drive_manager.py        # Gerenciamento do Drive
    └── database_manager.py     # Database JSON (legado)
```

## Branches

- `main`: Branch estável com funcionalidades básicas
- `downloader_PDSI`: Branch de desenvolvimento com CSV e checkpoint (recomendada)

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

MIT License

## Aviso Legal

Este projeto é destinado apenas para fins educacionais e de pesquisa. Respeite os termos de serviço do YouTube e os direitos autorais dos criadores de conteúdo. Use este sistema de forma responsável e ética.

## Autor

DosAnjos-AI

## Links

- Repositório: https://github.com/DosAnjos-AI/katube-colab
- Issues: https://github.com/DosAnjos-AI/katube-colab/issues
- Documentação yt-dlp: https://github.com/yt-dlp/yt-dlp

## Changelog

### v1.1.0 (Branch downloader_PDSI)
- Adicionado suporte a CSV de metadados completos
- Implementado sistema de checkpoint para retomada
- CSV com separador | para evitar conflitos
- Formato de áudio padrão alterado para MP3
- Verificação tripla (arquivo + CSV + checkpoint)
- Continua downloads mesmo com erros individuais
- Novas funcionalidades de análise de metadados

### v1.0.0 (Branch main)
- Versão inicial
- Download básico de vídeos, playlists e canais
- Estrutura de pastas organizada
- Detecção de duplicatas
- Logs automáticos
