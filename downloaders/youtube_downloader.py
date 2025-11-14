#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Downloader - Katube Colab
Core do download de áudio usando yt-dlp com detecção automática de tipo
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import (
    detect_url_type,
    validate_youtube_url,
    ensure_path_exists,
    print_header,
    print_progress
)
from downloaders.metadata_manager import MetadataManager


class YouTubeDownloader:
    """
    Gerenciador de downloads do YouTube com detecção automática
    Suporta: vídeos individuais, playlists e canais
    """

    def __init__(
        self,
        base_folder: str = "Katube_Download",
        audio_format: str = "mp3",
        audio_quality: int = 256,
        min_duration: int = 30,
        max_duration: int = 7200
    ):
        """
        Inicializa o downloader

        Args:
            base_folder: Nome da pasta base no Google Drive
            audio_format: Formato do áudio (mp3, flac, wav, m4a, ogg, opus)
            audio_quality: Qualidade em kbps (0 = melhor, 128, 192, 256, 320)
            min_duration: Duração mínima em segundos
            max_duration: Duração máxima em segundos
        """
        self.base_folder = base_folder
        self.base_path = Path("/content/drive/MyDrive") / base_folder
        self.audio_format = audio_format
        self.audio_quality = audio_quality
        self.min_duration = min_duration
        self.max_duration = max_duration

        # Gerenciador de metadados
        self.metadata_manager = MetadataManager(base_folder)

        # Estatísticas
        self.stats = {
            'total_attempted': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }

    def process_url(self, url: str, delay: int = 2) -> List[Dict]:
        """
        Processa URL detectando tipo automaticamente

        Args:
            url: URL do YouTube (vídeo, playlist ou canal)
            delay: Delay entre downloads em segundos

        Returns:
            Lista de resultados
        """
        print_header("KATUBE - PROCESSAMENTO AUTOMÁTICO")

        if not validate_youtube_url(url):
            print("ERRO: URL inválida")
            return [{'success': False, 'error': 'URL inválida'}]

        # Detecta tipo automaticamente
        url_type, content_id = detect_url_type(url)

        print(f"URL detectada: {url}")
        print(f"Tipo: {url_type.upper()}")
        print(f"ID: {content_id}")
        print(f"Destino: {self.base_path}")
        print("=" * 80)

        # Processa conforme o tipo
        if url_type == 'video':
            return self._process_video(url, delay)
        elif url_type == 'playlist':
            return self._process_playlist(url, delay)
        elif url_type == 'channel':
            return self._process_channel(url, delay)
        else:
            print("ERRO: Tipo de URL não reconhecido")
            return [{'success': False, 'error': 'Tipo não reconhecido'}]

    def _process_video(self, url: str, delay: int = 0) -> List[Dict]:
        """
        Processa vídeo individual

        Args:
            url: URL do vídeo
            delay: Não usado para vídeo único

        Returns:
            Lista com resultado (1 item)
        """
        print("\nProcessando vídeo individual...")

        # Extrai metadados primeiro
        metadata = self._extract_metadata(url)

        if not metadata:
            return [{'success': False, 'error': 'Falha ao extrair metadados'}]

        video_id = metadata.get('id')
        print(f"\nVídeo: {metadata.get('title', 'Unknown')}")
        print(f"ID: {video_id}")
        print(f"Duração: {metadata.get('duration', 0)}s")

        # Verifica se deve pular
        if self._should_skip(video_id):
            print(f"SKIP: Vídeo já existe")
            self.stats['skipped'] += 1
            return [{'success': True, 'skipped': True, 'id': video_id}]

        # Cria pasta do vídeo
        video_folder = self.base_path / f"video_{video_id}"
        ensure_path_exists(video_folder)

        # Baixa áudio
        result = self._download_audio(url, video_id, video_folder, metadata)

        return [result]

    def _process_playlist(self, url: str, delay: int = 2) -> List[Dict]:
        """
        Processa playlist completa

        Args:
            url: URL da playlist
            delay: Delay entre downloads em segundos

        Returns:
            Lista de resultados
        """
        print("\nProcessando playlist...")

        # Extrai lista de IDs
        video_ids = self._extract_video_ids(url)

        if not video_ids:
            print("ERRO: Nenhum vídeo encontrado na playlist")
            return [{'success': False, 'error': 'Playlist vazia'}]

        print(f"Encontrados {len(video_ids)} vídeos na playlist\n")

        results = []

        for i, video_id in enumerate(video_ids, 1):
            print(f"\n[{i}/{len(video_ids)}] Processando: {video_id}")

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Extrai metadados
            metadata = self._extract_metadata(video_url)

            if not metadata:
                print(f"ERRO: Falha ao extrair metadados de {video_id}")
                results.append({'success': False, 'id': video_id, 'error': 'Falha nos metadados'})
                continue

            print(f"Título: {metadata.get('title', 'Unknown')[:60]}...")

            # Verifica skip
            if self._should_skip(video_id):
                print(f"SKIP: Vídeo já existe")
                self.stats['skipped'] += 1
                results.append({'success': True, 'skipped': True, 'id': video_id})
                continue

            # Cria pasta do vídeo
            video_folder = self.base_path / f"video_{video_id}"
            ensure_path_exists(video_folder)

            # Baixa áudio
            result = self._download_audio(video_url, video_id, video_folder, metadata)
            results.append(result)

            # Delay entre downloads
            if i < len(video_ids) and result.get('success') and delay > 0:
                print(f"Aguardando {delay}s...")
                time.sleep(delay)

        return results

    def _process_channel(self, url: str, delay: int = 2) -> List[Dict]:
        """
        Processa todos os vídeos de um canal

        Args:
            url: URL do canal
            delay: Delay entre downloads em segundos

        Returns:
            Lista de resultados
        """
        print("\nProcessando canal...")

        # Modifica URL para pegar todos os vídeos
        if '/@' in url:
            if '/videos' not in url:
                url = url.rstrip('/') + '/videos'

        # Extrai lista de IDs
        video_ids = self._extract_video_ids(url)

        if not video_ids:
            print("ERRO: Nenhum vídeo encontrado no canal")
            return [{'success': False, 'error': 'Canal vazio'}]

        print(f"Encontrados {len(video_ids)} vídeos no canal\n")

        results = []

        for i, video_id in enumerate(video_ids, 1):
            print(f"\n[{i}/{len(video_ids)}] Processando: {video_id}")

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Extrai metadados
            metadata = self._extract_metadata(video_url)

            if not metadata:
                print(f"ERRO: Falha ao extrair metadados de {video_id}")
                results.append({'success': False, 'id': video_id, 'error': 'Falha nos metadados'})
                continue

            print(f"Título: {metadata.get('title', 'Unknown')[:60]}...")

            # Verifica skip
            if self._should_skip(video_id):
                print(f"SKIP: Vídeo já existe")
                self.stats['skipped'] += 1
                results.append({'success': True, 'skipped': True, 'id': video_id})
                continue

            # Cria pasta do vídeo
            video_folder = self.base_path / f"video_{video_id}"
            ensure_path_exists(video_folder)

            # Baixa áudio
            result = self._download_audio(video_url, video_id, video_folder, metadata)
            results.append(result)

            # Delay entre downloads
            if i < len(video_ids) and result.get('success') and delay > 0:
                print(f"Aguardando {delay}s...")
                time.sleep(delay)

        return results

    def _should_skip(self, video_id: str) -> bool:
        """
        Verifica se deve pular download (pasta existe OU ID no CSV)

        Args:
            video_id: ID do vídeo

        Returns:
            True se deve pular
        """
        # Verifica pasta
        video_folder = self.base_path / f"video_{video_id}"
        if video_folder.exists():
            audio_file = video_folder / f"{video_id}.{self.audio_format}"
            if audio_file.exists():
                return True

        # Verifica CSV
        if self.metadata_manager._id_exists(video_id):
            return True

        return False

    def _extract_video_ids(self, url: str) -> List[str]:
        """
        Extrai lista de IDs de vídeos de playlist/canal

        Args:
            url: URL da playlist ou canal

        Returns:
            Lista de video IDs
        """
        cmd = [
            'yt-dlp',
            '--flat-playlist',
            '--print', 'id',
            '--no-warnings',
            url
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
            video_ids = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return video_ids
        except Exception as e:
            print(f"Erro ao extrair IDs: {e}")
            return []

    def _extract_metadata(self, url: str) -> Optional[Dict]:
        """
        Extrai os 9 campos necessários de metadados

        Args:
            url: URL do vídeo

        Returns:
            Dict com metadados ou None se falhar
        """
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--no-warnings',
            '--no-playlist',
            url
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            data = json.loads(result.stdout)

            # Extrai apenas os 9 campos necessários
            metadata = {
                'id': data.get('id', ''),
                'title': data.get('title', ''),
                'duration': data.get('duration', 0),
                'upload_date': data.get('upload_date', ''),
                'uploader': data.get('uploader', ''),
                'uploader_id': data.get('uploader_id', ''),
                'view_count': data.get('view_count', 0),
                'like_count': data.get('like_count', 0),
                'comment_count': data.get('comment_count', 0)
            }

            # DEBUG: Mostra valores extraídos (importante para diagnóstico)
            print(f"  DEBUG - Metadados extraídos:")
            print(f"    - view_count: {metadata['view_count']} (tipo: {type(metadata['view_count']).__name__})")
            print(f"    - like_count: {metadata['like_count']} (tipo: {type(metadata['like_count']).__name__})")
            print(f"    - comment_count: {metadata['comment_count']} (tipo: {type(metadata['comment_count']).__name__})")

            return metadata

        except Exception as e:
            print(f"Erro ao extrair metadados: {e}")
            return None

    def _download_audio(
        self,
        url: str,
        video_id: str,
        output_folder: Path,
        metadata: Dict
    ) -> Dict:
        """
        Baixa áudio do vídeo

        Args:
            url: URL do vídeo
            video_id: ID do vídeo
            output_folder: Pasta de destino
            metadata: Metadados do vídeo

        Returns:
            Dict com resultado
        """
        self.stats['total_attempted'] += 1

        # Arquivo de saída
        audio_file = output_folder / f"{video_id}.{self.audio_format}"

        # Constrói comando
        cmd = [
            'yt-dlp',
            '-x',  # Extrair áudio
            '--audio-format', self.audio_format,
            '--output', str(audio_file).replace(f'.{self.audio_format}', '.%(ext)s'),
            '--no-playlist',
            '--no-warnings'
        ]

        # Qualidade
        if self.audio_quality > 0:
            cmd.extend(['--audio-quality', str(self.audio_quality)])

        # Filtros de duração
        if self.min_duration > 0:
            cmd.extend(['--match-filter', f'duration >= {self.min_duration}'])
        if self.max_duration > 0:
            cmd.extend(['--match-filter', f'duration <= {self.max_duration}'])

        # URL
        cmd.append(url)

        try:
            print("Baixando áudio...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=600  # 10 minutos timeout
            )

            if audio_file.exists():
                file_size = audio_file.stat().st_size
                print(f"Concluído: {file_size / 1024 / 1024:.2f} MB")

                self.stats['successful'] += 1

                # Prepara resultado com metadados
                result_data = metadata.copy()
                result_data['success'] = True
                result_data['file'] = str(audio_file)
                result_data['size'] = file_size

                return result_data

            else:
                print("ERRO: Arquivo não foi criado")
                self.stats['failed'] += 1
                return {
                    'success': False,
                    'id': video_id,
                    'error': 'Arquivo não criado'
                }

        except subprocess.TimeoutExpired:
            print("ERRO: Timeout no download")
            self.stats['failed'] += 1
            return {
                'success': False,
                'id': video_id,
                'error': 'Timeout'
            }

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            print(f"ERRO: {error_msg}")
            self.stats['failed'] += 1
            return {
                'success': False,
                'id': video_id,
                'error': error_msg
            }

        except Exception as e:
            print(f"ERRO: {str(e)}")
            self.stats['failed'] += 1
            return {
                'success': False,
                'id': video_id,
                'error': str(e)
            }

    def get_stats(self) -> Dict:
        """Retorna estatísticas de download"""
        return self.stats.copy()


if __name__ == "__main__":
    # Teste básico
    downloader = YouTubeDownloader()
    print("YouTubeDownloader inicializado")
    print(f"Pasta base: {downloader.base_path}")
