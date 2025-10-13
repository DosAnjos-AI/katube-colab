#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitários - Katube Colab
Funções auxiliares reutilizáveis
"""

import re
import time
import random
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs
from datetime import datetime


def detect_url_type(url: str) -> Tuple[str, Optional[str]]:
    """
    Detecta o tipo de URL do YouTube e extrai o ID
    
    Args:
        url: URL do YouTube
        
    Returns:
        Tuple (tipo, id) onde tipo é 'playlist', 'channel', 'video' ou 'unknown'
    """
    # Playlist
    if 'playlist?list=' in url or '&list=' in url:
        parsed = urlparse(url)
        playlist_id = parse_qs(parsed.query).get('list', [None])[0]
        if playlist_id:
            return ('playlist', playlist_id)
    
    # Canal por handle (@usuario)
    if '/@' in url:
        handle = url.split('/@')[1].split('/')[0].split('?')[0]
        return ('channel', handle)
    
    # Canal por ID (UC...)
    if '/channel/' in url:
        channel_id = url.split('/channel/')[1].split('/')[0].split('?')[0]
        return ('channel', channel_id)
    
    # Vídeo (watch?v=)
    if 'watch?v=' in url:
        parsed = urlparse(url)
        video_id = parse_qs(parsed.query).get('v', [None])[0]
        if video_id:
            return ('video', video_id)
    
    # URL encurtada (youtu.be)
    if 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[1].split('?')[0]
        return ('video', video_id)
    
    return ('unknown', None)


def validate_youtube_url(url: str) -> bool:
    """
    Valida se é uma URL válida do YouTube
    
    Args:
        url: URL para validar
        
    Returns:
        True se válida, False caso contrário
    """
    url_type, url_id = detect_url_type(url)
    return url_type != 'unknown' and url_id is not None


def sanitize_filename(filename: str) -> str:
    """
    Remove caracteres inválidos de nomes de arquivo
    
    Args:
        filename: Nome do arquivo original
        
    Returns:
        Nome sanitizado
    """
    # Remove caracteres inválidos
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Remove espaços extras
    filename = re.sub(r'\s+', ' ', filename).strip()
    
    return filename


def format_duration(seconds: int) -> str:
    """
    Formata duração em segundos para formato legível
    
    Args:
        seconds: Duração em segundos
        
    Returns:
        String formatada (ex: "2h 30m 15s")
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def format_size(bytes_size: int) -> str:
    """
    Formata tamanho em bytes para formato legível
    
    Args:
        bytes_size: Tamanho em bytes
        
    Returns:
        String formatada (ex: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def random_delay(min_seconds: int, max_seconds: int) -> int:
    """
    Gera delay aleatório entre downloads
    
    Args:
        min_seconds: Mínimo de segundos
        max_seconds: Máximo de segundos
        
    Returns:
        Delay em segundos
    """
    return random.randint(min_seconds, max_seconds)


def wait_with_countdown(seconds: int, message: str = "Aguardando"):
    """
    Espera com contagem regressiva visual
    
    Args:
        seconds: Tempo de espera
        message: Mensagem a exibir
    """
    for remaining in range(seconds, 0, -1):
        print(f"\r{message}: {remaining}s restantes...", end='', flush=True)
        time.sleep(1)
    print("\r" + " " * 50 + "\r", end='', flush=True)


def get_timestamp() -> str:
    """
    Retorna timestamp formatado para logs
    
    Returns:
        String com timestamp (ex: "2025-01-15 14:30:45")
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_date_string() -> str:
    """
    Retorna data formatada para nomes de arquivo
    
    Returns:
        String com data (ex: "2025-01-15")
    """
    return datetime.now().strftime("%Y-%m-%d")


def ensure_path_exists(path: Path) -> Path:
    """
    Garante que um caminho existe, criando se necessário
    
    Args:
        path: Caminho a verificar/criar
        
    Returns:
        Path do diretório
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_urls_from_file(file_path: str) -> list:
    """
    Lê URLs de um arquivo txt (uma por linha)
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Lista de URLs válidas
    """
    urls = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and validate_youtube_url(line):
                    urls.append(line)
    except Exception as e:
        print(f"Erro ao ler arquivo {file_path}: {e}")
    
    return urls


def get_next_txt_id(base_path: Path) -> str:
    """
    Gera próximo ID sequencial para pastas txt_XX
    
    Args:
        base_path: Caminho base onde estão as pastas txt_
        
    Returns:
        Próximo ID (ex: "01", "02", "03")
    """
    existing_folders = list(base_path.glob("txt_*"))
    
    if not existing_folders:
        return "01"
    
    # Extrai números existentes
    numbers = []
    for folder in existing_folders:
        match = re.search(r'txt_(\d+)', folder.name)
        if match:
            numbers.append(int(match.group(1)))
    
    if numbers:
        next_num = max(numbers) + 1
        return f"{next_num:02d}"
    
    return "01"


def print_separator(char='=', length=60):
    """Imprime separador visual"""
    print(char * length)


def print_header(title: str, char='=', length=60):
    """Imprime cabeçalho formatado"""
    print_separator(char, length)
    print(title.center(length))
    print_separator(char, length)


def print_progress(current: int, total: int, prefix: str = "Progresso"):
    """
    Imprime barra de progresso simples
    
    Args:
        current: Número atual
        total: Total de itens
        prefix: Texto antes da barra
    """
    percent = (current / total) * 100 if total > 0 else 0
    bar_length = 30
    filled = int(bar_length * current / total) if total > 0 else 0
    bar = '█' * filled + '-' * (bar_length - filled)
    
    print(f"\r{prefix}: |{bar}| {percent:.1f}% ({current}/{total})", end='', flush=True)
    
    if current >= total:
        print()  # Nova linha quando completo


if __name__ == "__main__":
    # Testes das funções
    print_header("TESTE DE UTILITÁRIOS")
    
    # Teste de detecção de URL
    test_urls = [
        "https://www.youtube.com/watch?v=ABC123",
        "https://www.youtube.com/playlist?list=PLxxx",
        "https://www.youtube.com/@usuario",
        "https://youtu.be/XYZ789"
    ]
    
    for url in test_urls:
        url_type, url_id = detect_url_type(url)
        print(f"{url_type.upper()}: {url_id}")
    
    # Teste de formatação
    print(f"\nDuração: {format_duration(7325)}")
    print(f"Tamanho: {format_size(1536000)}")
    print(f"Timestamp: {get_timestamp()}")