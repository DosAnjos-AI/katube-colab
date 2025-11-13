# Katube Colab

Sistema modular para download de áudio do YouTube com persistência no Google Drive e gerenciamento completo de metadados.

## Características

### Download de Áudio
- Download de áudio em alta qualidade
- Suporte para 6 formatos: **mp3, flac, wav, m4a, opus, ogg**
- Suporte para vídeos individuais, playlists, canais e arquivos txt
- Persistência automática no Google Drive
- Estrutura de pastas organizada
- Delays anti-bloqueio configuráveis
- Logs automáticos detalhados

### Sistema de Metadados (NOVO!)
- **Extração completa de metadados** (18+ campos por vídeo)
- **CSV consolidado** com todos os downloads (`metadata_complete.csv`)
- **Skip inteligente de duplicados** usando CSV + verificação de pastas
- **Estatísticas completas** por tipo de download
- **Exportação filtrada** de subconjuntos
- Integração com pandas para análises personalizadas

### Metadados Capturados
- **Básicos**: id, title, description, duration, upload_date, timestamp
- **Canal**: uploader, uploader_id, uploader_url, channel, channel_id, channel_url
- **Estatísticas**: view_count, like_count, comment_count, average_rating
- **Categorização**: categories, tags, language
- **Arquivo**: audio_format, file_path, file_size_bytes, download_date, download_type

## Estrutura no Drive

```
MyDrive/Katube_Download/
├── metadata_complete.csv          # NOVO: CSV consolidado com todos os metadados
├── database.json                   # Database JSON (mantido para compatibilidade)
├── Playlist_PLxxx/
│   ├── ABC123/
│   │   └── ABC123.flac
│   └── XYZ789/
│       └── XYZ789.flac
├── Canal_UCxxx/
├── video_ABC123/
│   └── ABC123.mp3
├── txt_01/
└── logs/
    ├── download_2025-01-15.log
    └── errors_2025-01-15.log
```

##  Uso no Google Colab

### 1. Clone o repositório

```python
!git clone https://github.com/seu-usuario/katube-colab.git
%cd katube-colab
!pip install -r requirements.txt
```

### 2. Monte o Google Drive

```python
from google.colab import drive
drive.mount('/content/drive')
```

### 3. Importe e use

#### Uso Básico
```python
from downloaders import YouTubeDownloader, DriveManager
from config import Config

# Configura Drive
drive_manager = DriveManager()
drive_manager.setup_folder_structure()

# Download de vídeo individual
downloader = YouTubeDownloader()
result = downloader.download_from_url("https://youtube.com/watch?v=VIDEO_ID")

# Download de playlist
result = downloader.download_from_url("https://youtube.com/playlist?list=PLAYLIST_ID")

# Download de arquivo txt
result = downloader.download_from_txt("urls.txt")
```

#### Uso com Metadados Completos (NOVO!)
```python
from downloaders import YouTubeDownloader, MetadataManager
from config import Config

# Configurações
url = "https://youtube.com/watch?v=VIDEO_ID"
Config.AUDIO_FORMAT = 'mp3'  # Escolha o formato

# Inicializa
downloader = YouTubeDownloader()
metadata_manager = MetadataManager()

# Download automático com metadados
result = downloader.download_from_url(url)

# Resultado inclui metadados completos
if result['success']:
    metadata = result.get('metadata')
    print(f"Título: {metadata['title']}")
    print(f"Canal: {metadata['uploader']}")
    print(f"Views: {metadata['view_count']}")

# Estatísticas do CSV
summary = metadata_manager.get_summary()
print(f"Total no banco: {summary['total_videos']} vídeos")
print(f"Tamanho total: {summary['total_size_formatted']}")
```

#### Análise de Metadados com Pandas
```python
from downloaders import MetadataManager
import pandas as pd

manager = MetadataManager()
df = manager.load_csv()  # Usa separador pipe automaticamente

# Análises personalizadas
videos_por_canal = df.groupby('uploader').size()
total_views = df['view_count'].sum()
duracao_media = df['duration'].mean()

# Filtrar e exportar
playlists_df = df[df['download_type'] == 'playlist']
playlists_df.to_csv('apenas_playlists.csv')

# Leitura manual do CSV (se necessário)
# df = pd.read_csv('metadata_complete.csv', sep='|')
```

## Configuração

Edite `config.py` para personalizar:

```python
class Config:
    # Formato de áudio: 'flac', 'mp3', 'wav', 'm4a', 'opus', 'ogg'
    AUDIO_FORMAT = 'flac'

    # Qualidade (0 = melhor disponível)
    AUDIO_QUALITY = 0

    # Delays entre downloads (segundos)
    DELAY_MIN = 10
    DELAY_MAX = 20

    # Pular duplicatas (agora usa CSV + arquivos + pastas)
    SKIP_EXISTING = True
```

### Sistema de Skip Inteligente

O novo sistema verifica **3 condições** antes de baixar:
1. **Arquivo existe** no caminho esperado
2. **ID existe no CSV** `metadata_complete.csv`
3. **Pasta existe** e não está vazia

Se qualquer condição for verdadeira: **SKIP** com mensagem clara mostrando o motivo.

## 📋 Formato do arquivo txt

Uma URL por linha:

```
https://youtube.com/watch?v=ABC123
https://youtube.com/watch?v=XYZ789
https://youtube.com/playlist?list=PLxxx
```

## Requisitos

- Python 3.8+
- Google Colab (ou ambiente local com Google Drive montado)
- yt-dlp >= 2023.12.30
- pandas >= 1.5.0 (para sistema de metadados)

## CSV de Metadados

### Estrutura do CSV (`metadata_complete.csv`)

O CSV consolidado contém **23 colunas** com informações completas.

**IMPORTANTE:** O CSV usa **pipe (`|`)** como separador ao invés de vírgula, evitando conflitos com títulos, descrições e tags que frequentemente contêm vírgulas.

| Categoria | Campos |
|-----------|--------|
| **Identificação** | id |
| **Informações Básicas** | title, description, duration, upload_date, timestamp |
| **Canal/Uploader** | uploader, uploader_id, uploader_url, channel, channel_id, channel_url |
| **Estatísticas** | view_count, like_count, comment_count, average_rating |
| **Categorização** | categories, tags, language |
| **Arquivo** | audio_format, file_path, file_size_bytes, download_date, download_type |

### Localização

```
/content/drive/MyDrive/Katube_Download/metadata_complete.csv
```

### Acesso via Código

```python
from downloaders import MetadataManager

manager = MetadataManager()

# Verifica se vídeo existe
exists = manager.video_exists('VIDEO_ID')

# Busca metadados de um vídeo
metadata = manager.get_video_metadata('VIDEO_ID')

# Estatísticas gerais
summary = manager.get_summary()
print(f"Total: {summary['total_videos']} vídeos")

# Exporta filtrado
manager.export_filtered(
    {'download_type': 'playlist'},
    'playlists.csv'
)
```

## Licença

MIT License

## 🤝 Contribuições

Contribuições são bem-vindas! Abra uma issue ou pull request.

## ⚠️ Aviso Legal

Use este projeto de forma responsável e respeite os termos de serviço do YouTube.
