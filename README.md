# 🎵 Katube Colab

Sistema modular para download de áudio do YouTube com persistência no Google Drive.

##  Características

-  Download de áudio em alta qualidade (FLAC padrão)
-  Suporte para vídeos individuais, playlists, canais e arquivos txt
-  Persistência automática no Google Drive
-  Estrutura de pastas organizada
-  Detecção de duplicatas
-  Delays anti-bloqueio
-  Logs automáticos

##  Estrutura no Drive

```
MyDrive/Katube_Download/
├── Playlist_PLxxx/
│   ├── ABC123/
│   │   └── ABC123.flac
│   └── XYZ789/
│       └── XYZ789.flac
├── Canal_UCxxx/
├── video_ABC123/
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

## ⚙️ Configuração

Edite `config.py` para personalizar:

```python
class Config:
    # Formato de áudio: 'flac', 'mp3', 'wav', 'm4a'
    AUDIO_FORMAT = 'flac'
    
    # Qualidade (0 = melhor disponível)
    AUDIO_QUALITY = 0
    
    # Delays entre downloads (segundos)
    DELAY_MIN = 10
    DELAY_MAX = 20
    
    # Pular duplicatas
    SKIP_EXISTING = True
```

## 📋 Formato do arquivo txt

Uma URL por linha:

```
https://youtube.com/watch?v=ABC123
https://youtube.com/watch?v=XYZ789
https://youtube.com/playlist?list=PLxxx
```

## 🛠️ Requisitos

- Python 3.8+
- Google Colab (ou ambiente local com Google Drive montado)
- yt-dlp

## 📝 Licença

MIT License

## 🤝 Contribuições

Contribuições são bem-vindas! Abra uma issue ou pull request.

## ⚠️ Aviso Legal

Use este projeto de forma responsável e respeite os termos de serviço do YouTube.
