#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Downloader - Katube Colab
Core do download de audio usando yt-dlp com suporte a CSV e checkpoint
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
    print_progress,
    format_duration,
    format_size
)
from downloaders.metadata_manager import MetadataManager


class CheckpointManager:
    """Gerenciador de checkpoint para retomada de downloads"""
    
    def __init__(self, checkpoint_path: Path):
        self.checkpoint_path = checkpoint_path
    
    def load(self) -> Dict:
        """Carrega checkpoint existente"""
        if not self.checkpoint_path.exists():
            return {
                'url': '',
                'total_videos': 0,
                'processed': [],
                'failed': [],
                'last_update': ''
            }
        
        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar checkpoint: {e}")
            return {
                'url': '',
                'total_videos': 0,
                'processed': [],
                'failed': [],
                'last_update': ''
            }
    
    def save(self, data: Dict) -> bool:
        """Salva checkpoint"""
        try:
            data['last_update'] = get_timestamp()
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar checkpoint: {e}")
            return False
    
    def add_processed(self, video_id: str) -> bool:
        """Adiciona video_id aos processados"""
        data = self.load()
        if video_id not in data['processed']:
            data['processed'].append(video_id)
        return self.save(data)
    
    def add_failed(self, video_id: str) -> bool:
        """Adiciona video_id aos falhados"""
        data = self.load()
        if video_id not in data['failed']:
            data['failed'].append(video_id)
        return self.save(data)


class YouTubeDownloader:
    """
    Gerenciador de downloads do YouTube
    Suporta: videos individuais, playlists, canais e arquivos txt
    Com suporte a CSV de metadados e checkpoint para retomada
    """
    
    def __init__(self, config: Config = None):
        """
        Inicializa o downloader
        
        Args:
            config: Configuracoes customizadas (usa padrao se None)
        """
        self.config = config or Config()
        self.metadata_manager = MetadataManager(self.config)
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
            url: URL do YouTube (video, playlist, canal)
            
        Returns:
            Dict com resultado do download
        """
        print_header(f"DOWNLOAD: {url}")
        
        if not validate_youtube_url(url):
            return {'success': False, 'error': 'URL invalida'}
        
        url_type, content_id = detect_url_type(url)
        
        if url_type == 'unknown':
            return {'success': False, 'error': 'Tipo de URL nao reconhecido'}
        
        print(f"Tipo: {url_type.upper()}")
        print(f"ID: {content_id}")
        
        # Determina pasta de destino
        output_path = self.config.get_download_path(url_type, content_id)
        ensure_path_exists(output_path)
        
        print(f"Destino: {output_path}")
        
        # Prepara CSV
        csv_path = self.config.get_csv_path(output_path)
        if self.config.CSV_ENABLED and not csv_path.exists():
            self.metadata_manager.create_csv(csv_path)
        
        # Executa download
        if url_type == 'video':
            return self._download_single_video(url, content_id, output_path, url_type)
        else:
            return self._download_collection(url, url_type, output_path)
    
    def download_from_txt(self, txt_path: str) -> Dict:
        """
        Download de multiplas URLs de um arquivo txt
        
        Args:
            txt_path: Caminho do arquivo txt com URLs
            
        Returns:
            Dict com resultado dos downloads
        """
        urls = read_urls_from_file(txt_path)
        
        if not urls:
            return {'success': False, 'error': 'Nenhuma URL valida encontrada'}
        
        print_header(f"DOWNLOAD DE ARQUIVO TXT: {len(urls)} URLs")
        
        # Gera ID sequencial
        txt_id = get_next_txt_id(self.config.get_base_path())
        output_path = self.config.get_download_path('txt', txt_id)
        ensure_path_exists(output_path)
        
        print(f"ID gerado: txt_{txt_id}")
        print(f"Destino: {output_path}")
        
        # Prepara CSV
        csv_path = self.config.get_csv_path(output_path)
        if self.config.CSV_ENABLED:
            self.metadata_manager.create_csv(csv_path)
        
        # Prepara checkpoint
        checkpoint_path = self.config.get_checkpoint_path(output_path)
        checkpoint = CheckpointManager(checkpoint_path) if self.config.CHECKPOINT_ENABLED else None
        
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processando: {url}")
            
            url_type, content_id = detect_url_type(url)
            video_path = output_path / content_id
            ensure_path_exists(video_path)
            
            result = self._download_single_video(url, content_id, video_path, 'txt', csv_path, checkpoint)
            results.append(result)
            
            # Delay entre downloads
            if i < len(urls) and result.get('success') and not result.get('skipped'):
                delay = random_delay(self.config.DELAY_MIN, self.config.DELAY_MAX)
                wait_with_countdown(delay, "Aguardando proximo download")
        
        return {
            'success': True,
            'txt_id': txt_id,
            'total_urls': len(urls),
            'results': results,
            'stats': self.stats,
            'csv_path': str(csv_path) if self.config.CSV_ENABLED else None
        }
    
    def _should_skip_video(self, video_id: str, video_path: Path, 
                           csv_path: Optional[Path], checkpoint: Optional[CheckpointManager]) -> bool:
        """
        Verifica se deve pular o video (ja processado)
        
        Args:
            video_id: ID do video
            video_path: Caminho da pasta do video
            csv_path: Caminho do CSV
            checkpoint: Gerenciador de checkpoint
            
        Returns:
            True se deve pular
        """
        # Verifica arquivo de audio
        audio_file = video_path / f"{video_id}.{self.config.AUDIO_FORMAT}"
        audio_exists = audio_file.exists()
        
        # Verifica CSV
        csv_has_video = False
        if csv_path and csv_path.exists():
            successful_ids = self.metadata_manager.get_successful_ids(csv_path)
            csv_has_video = video_id in successful_ids
        
        # Verifica checkpoint
        checkpoint_has_video = False
        if checkpoint:
            checkpoint_data = checkpoint.load()
            checkpoint_has_video = video_id in checkpoint_data.get('processed', [])
        
        # Decisao: pula apenas se TODOS confirmarem
        should_skip = audio_exists and (csv_has_video or not self.config.CSV_ENABLED)
        
        return should_skip
    
    def _download_single_video(self, url: str, video_id: str, output_path: Path,
                               collection_type: str = 'video',
                               csv_path: Optional[Path] = None,
                               checkpoint: Optional[CheckpointManager] = None) -> Dict:
        """
        Download de um unico video
        
        Args:
            url: URL do video
            video_id: ID do video
            output_path: Pasta de destino
            collection_type: Tipo de colecao
            csv_path: Caminho do CSV (opcional)
            checkpoint: Gerenciador de checkpoint (opcional)
            
        Returns:
            Dict com resultado
        """
        self.stats['total_attempted'] += 1
        
        # Define csv_path se nao fornecido
        if csv_path is None:
            csv_path = self.config.get_csv_path(output_path.parent)
        
        # Verifica se deve pular
        if self.config.SKIP_EXISTING and self._should_skip_video(video_id, output_path, csv_path, checkpoint):
            print(f"Ja existe: {video_id}")
            self.stats['skipped'] += 1
            return {
                'success': True,
                'skipped': True,
                'video_id': video_id
            }
        
        # Extrai metadados
        metadata = None
        if self.config.CSV_ENABLED:
            print(f"Extraindo metadados: {video_id}")
            metadata = self.metadata_manager.extract_metadata(url)
            
            if metadata:
                metadata['collection_type'] = collection_type
                metadata['download_status'] = 'pending'
                self.metadata_manager.add_metadata(csv_path, metadata)
        
        # Constroi comando yt-dlp
        cmd = self._build_ytdlp_command(url, output_path, video_id)
        
        # Define arquivo de audio
        audio_file = output_path / f"{video_id}.{self.config.AUDIO_FORMAT}"
        
        try:
            print(f"Baixando audio: {video_id}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if audio_file.exists():
                file_size = audio_file.stat().st_size
                print(f"Concluido: {video_id}.{self.config.AUDIO_FORMAT} ({format_size(file_size)})")
                self.stats['successful'] += 1
                
                # Atualiza CSV
                if self.config.CSV_ENABLED and csv_path:
                    self.metadata_manager.update_download_status(csv_path, video_id, 'success', file_size)
                
                # Atualiza checkpoint
                if checkpoint:
                    checkpoint.add_processed(video_id)
                
                return {
                    'success': True,
                    'video_id': video_id,
                    'file': str(audio_file),
                    'size': file_size
                }
            else:
                print(f"Erro: Arquivo nao foi criado")
                self.stats['failed'] += 1
                
                # Atualiza CSV
                if self.config.CSV_ENABLED and csv_path:
                    self.metadata_manager.update_download_status(csv_path, video_id, 'failed')
                
                # Atualiza checkpoint
                if checkpoint:
                    checkpoint.add_failed(video_id)
                
                return {
                    'success': False,
                    'video_id': video_id,
                    'error': 'Arquivo nao foi criado'
                }
                
        except subprocess.CalledProcessError as e:
            print(f"Erro no download: {e}")
            self.stats['failed'] += 1
            
            # Atualiza CSV
            if self.config.CSV_ENABLED and csv_path:
                self.metadata_manager.update_download_status(csv_path, video_id, 'failed')
            
            # Atualiza checkpoint
            if checkpoint:
                checkpoint.add_failed(video_id)
            
            return {
                'success': False,
                'video_id': video_id,
                'error': str(e)
            }
    
    def _download_collection(self, url: str, collection_type: str, output_path: Path) -> Dict:
        """
        Download de playlist ou canal
        
        Args:
            url: URL da colecao
            collection_type: 'playlist' ou 'channel'
            output_path: Pasta base
            
        Returns:
            Dict com resultado
        """
        print(f"Obtendo lista de videos da {collection_type}...")
        
        # Extrai lista de IDs
        video_ids = self._extract_video_ids(url)
        
        if not video_ids:
            return {'success': False, 'error': 'Nenhum video encontrado'}
        
        print(f"Encontrados {len(video_ids)} videos")
        
        # Prepara CSV
        csv_path = self.config.get_csv_path(output_path)
        if self.config.CSV_ENABLED:
            self.metadata_manager.create_csv(csv_path)
        
        # Prepara checkpoint
        checkpoint_path = self.config.get_checkpoint_path(output_path)
        checkpoint = None
        if self.config.CHECKPOINT_ENABLED:
            checkpoint = CheckpointManager(checkpoint_path)
            checkpoint_data = checkpoint.load()
            checkpoint_data['url'] = url
            checkpoint_data['total_videos'] = len(video_ids)
            checkpoint.save(checkpoint_data)
        
        # Aplica limite se configurado
        if self.config.MAX_DOWNLOADS > 0:
            video_ids = video_ids[:self.config.MAX_DOWNLOADS]
            print(f"Limitado a {len(video_ids)} videos")
        
        results = []
        
        for i, video_id in enumerate(video_ids, 1):
            print_progress(i, len(video_ids), "Progresso")
            
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_path = output_path / video_id
            ensure_path_exists(video_path)
            
            result = self._download_single_video(video_url, video_id, video_path, collection_type, csv_path, checkpoint)
            results.append(result)
            
            # Delay entre downloads
            if i < len(video_ids) and result.get('success') and not result.get('skipped'):
                delay = random_delay(self.config.DELAY_MIN, self.config.DELAY_MAX)
                wait_with_countdown(delay)
        
        # Resumo final
        if self.config.CSV_ENABLED:
            summary = self.metadata_manager.get_summary(csv_path)
            print("\n")
            print_header("RESUMO DO CSV")
            print(f"Total de videos: {summary['total_videos']}")
            print(f"Sucesso: {summary['successful']}")
            print(f"Falhas: {summary['failed']}")
            print(f"Pendentes: {summary['pending']}")
            print(f"Tamanho total: {summary['total_size_formatted']}")
            print(f"Duracao total: {summary['total_duration_formatted']}")
        
        return {
            'success': True,
            'collection_type': collection_type,
            'total_videos': len(video_ids),
            'results': results,
            'stats': self.stats,
            'csv_path': str(csv_path) if self.config.CSV_ENABLED else None
        }
    
    def _extract_video_ids(self, url: str) -> List[str]:
        """
        Extrai lista de IDs de videos de uma playlist/canal
        
        Args:
            url: URL da colecao
            
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
        Constroi comando yt-dlp
        
        Args:
            url: URL do video
            output_path: Pasta de destino
            video_id: ID do video
            
        Returns:
            Lista de argumentos do comando
        """
        cmd = [
            'yt-dlp',
            '-x',
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
        
        # Filtros de duracao
        if self.config.MIN_DURATION > 0:
            cmd.extend(['--match-filter', f'duration >= {self.config.MIN_DURATION}'])
        
        if self.config.MAX_DURATION > 0:
            cmd.extend(['--match-filter', f'duration <= {self.config.MAX_DURATION}'])
        
        # URL
        cmd.append(url)
        
        return cmd
    
    def get_stats(self) -> Dict:
        """Retorna estatisticas de download"""
        return self.stats.copy()


if __name__ == "__main__":
    # Teste basico
    downloader = YouTubeDownloader()
    print("YouTubeDownloader inicializado")
    print(f"Config valida: {Config.validate()['valid']}")
