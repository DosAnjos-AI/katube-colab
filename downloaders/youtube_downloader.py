#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Downloader - Katube Colab
Core do download de áudio usando yt-dlp
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config
from utils import (
    detect_url_type, 
    validate_youtube_url, 
    random_delay, 
    wait_with_countdown,
    get_timestamp,
    ensure_path_exists,
    read_urls_from_file,
    get_next_txt_id,
    print_header,
    print_progress
)


class YouTubeDownloader:
    """
    Gerenciador de downloads do YouTube
    Suporta: vídeos individuais, playlists, canais e arquivos txt
    """
    
    def __init__(self, config: Config = None):
        """
        Inicializa o downloader
        
        Args:
            config: Configurações customizadas (usa padrão se None)
        """
        self.config = config or Config()
        self.stats = {
            'total_attempted': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
    def download_from_url(self, url: str) -> Dict:
        """
        Download a partir de uma URL do YouTube
        
        Args:
            url: URL do YouTube (vídeo, playlist, canal)
            
        Returns:
            Dict com resultado do download
        """
        print_header(f"DOWNLOAD: {url}")
        
        if not validate_youtube_url(url):
            return {'success': False, 'error': 'URL inválida'}
        
        url_type, content_id = detect_url_type(url)
        
        if url_type == 'unknown':
            return {'success': False, 'error': 'Tipo de URL não reconhecido'}
        
        print(f"Tipo: {url_type.upper()}")
        print(f"ID: {content_id}")
        
        # Determina pasta de destino
        output_path = self.config.get_download_path(url_type, content_id)
        ensure_path_exists(output_path)
        
        print(f"Destino: {output_path}")
        
        # Executa download
        if url_type == 'video':
            return self._download_single_video(url, content_id, output_path)
        else:
            return self._download_collection(url, url_type, output_path)
    
    def download_from_txt(self, txt_path: str) -> Dict:
        """
        Download de múltiplas URLs de um arquivo txt
        
        Args:
            txt_path: Caminho do arquivo txt com URLs
            
        Returns:
            Dict com resultado dos downloads
        """
        urls = read_urls_from_file(txt_path)
        
        if not urls:
            return {'success': False, 'error': 'Nenhuma URL válida encontrada'}
        
        print_header(f"DOWNLOAD DE ARQUIVO TXT: {len(urls)} URLs")
        
        # Gera ID sequencial
        txt_id = get_next_txt_id(self.config.get_base_path())
        output_path = self.config.get_download_path('txt', txt_id)
        ensure_path_exists(output_path)
        
        print(f"ID gerado: txt_{txt_id}")
        print(f"Destino: {output_path}")
        
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processando: {url}")
            
            url_type, content_id = detect_url_type(url)
            video_path = output_path / content_id
            ensure_path_exists(video_path)
            
            result = self._download_single_video(url, content_id, video_path)
            results.append(result)
            
            # Delay entre downloads
            if i < len(urls) and result['success']:
                delay = random_delay(self.config.DELAY_MIN, self.config.DELAY_MAX)
                wait_with_countdown(delay, "Aguardando próximo download")
        
        return {
            'success': True,
            'txt_id': txt_id,
            'total_urls': len(urls),
            'results': results,
            'stats': self.stats
        }
    
    def _download_single_video(self, url: str, video_id: str, output_path: Path) -> Dict:
        """
        Download de um único vídeo
        
        Args:
            url: URL do vídeo
            video_id: ID do vídeo
            output_path: Pasta de destino
            
        Returns:
            Dict com resultado
        """
        self.stats['total_attempted'] += 1
        
        # Verifica duplicata
        audio_file = output_path / f"{video_id}.{self.config.AUDIO_FORMAT}"
        
        if audio_file.exists() and self.config.SKIP_EXISTING:
            print(f"Já existe: {audio_file.name}")
            self.stats['skipped'] += 1
            return {
                'success': True,
                'skipped': True,
                'video_id': video_id,
                'file': str(audio_file)
            }
        
        # Constrói comando yt-dlp
        cmd = self._build_ytdlp_command(url, output_path, video_id)
        
        try:
            print("Baixando áudio...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if audio_file.exists():
                file_size = audio_file.stat().st_size
                print(f"Concluído: {video_id}.{self.config.AUDIO_FORMAT} ({file_size/1024/1024:.2f} MB)")
                self.stats['successful'] += 1
                
                return {
                    'success': True,
                    'video_id': video_id,
                    'file': str(audio_file),
                    'size': file_size
                }
            else:
                print(f"Erro: Arquivo não foi criado")
                self.stats['failed'] += 1
                return {
                    'success': False,
                    'video_id': video_id,
                    'error': 'Arquivo não foi criado'
                }
                
        except subprocess.CalledProcessError as e:
            print(f"Erro no download: {e}")
            self.stats['failed'] += 1
            return {
                'success': False,
                'video_id': video_id,
                'error': str(e)
            }
    
    def _download_collection(self, url: str, collection_type: str, output_path: Path) -> Dict:
        """
        Download de playlist ou canal
        
        Args:
            url: URL da coleção
            collection_type: 'playlist' ou 'channel'
            output_path: Pasta base
            
        Returns:
            Dict com resultado
        """
        print(f"Obtendo lista de vídeos da {collection_type}...")
        
        # Extrai lista de IDs
        video_ids = self._extract_video_ids(url)
        
        if not video_ids:
            return {'success': False, 'error': 'Nenhum vídeo encontrado'}
        
        print(f"Encontrados {len(video_ids)} vídeos")
        
        # Aplica limite se configurado
        if self.config.MAX_DOWNLOADS > 0:
            video_ids = video_ids[:self.config.MAX_DOWNLOADS]
            print(f"Limitado a {len(video_ids)} vídeos")
        
        results = []
        
        for i, video_id in enumerate(video_ids, 1):
            print_progress(i, len(video_ids), "Progresso")
            
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_path = output_path / video_id
            ensure_path_exists(video_path)
            
            result = self._download_single_video(video_url, video_id, video_path)
            results.append(result)
            
            # Delay entre downloads
            if i < len(video_ids) and result['success']:
                delay = random_delay(self.config.DELAY_MIN, self.config.DELAY_MAX)
                wait_with_countdown(delay)
        
        return {
            'success': True,
            'collection_type': collection_type,
            'total_videos': len(video_ids),
            'results': results,
            'stats': self.stats
        }
    
    def _extract_video_ids(self, url: str) -> List[str]:
        """
        Extrai lista de IDs de vídeos de uma playlist/canal
        
        Args:
            url: URL da coleção
            
        Returns:
            Lista de video IDs
        """
        cmd = [
            'yt-dlp',
            '--flat-playlist',
            '--print', 'id',
            '--quiet',
            url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_ids = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return video_ids
        except subprocess.CalledProcessError:
            return []
    
    def _build_ytdlp_command(self, url: str, output_path: Path, video_id: str) -> List[str]:
        """
        Constrói comando yt-dlp
        
        Args:
            url: URL do vídeo
            output_path: Pasta de destino
            video_id: ID do vídeo
            
        Returns:
            Lista de argumentos do comando
        """
        cmd = [
            'yt-dlp',
            '-x',  # Extrair áudio
            '--audio-format', self.config.AUDIO_FORMAT,
        ]
        
        # Qualidade
        if self.config.AUDIO_QUALITY > 0:
            cmd.extend(['--audio-quality', str(self.config.AUDIO_QUALITY)])
        
        # Output
        cmd.extend([
            '--output', str(output_path / f"{video_id}.%(ext)s"),
            '--quiet',
            '--no-warnings',
        ])
        
        # Filtros de duração
        if self.config.MIN_DURATION > 0:
            cmd.extend(['--match-filter', f'duration >= {self.config.MIN_DURATION}'])
        
        if self.config.MAX_DURATION > 0:
            cmd.extend(['--match-filter', f'duration <= {self.config.MAX_DURATION}'])
        
        # URL
        cmd.append(url)
        
        return cmd
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de download"""
        return self.stats.copy()


if __name__ == "__main__":
    # Teste básico
    downloader = YouTubeDownloader()
    print("YouTubeDownloader inicializado")
    print(f"Config válida: {Config.validate()['valid']}")