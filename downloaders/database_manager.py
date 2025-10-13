#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Manager - Katube Colab
Gerenciamento de metadados cumulativos em JSON
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config
from utils import ensure_path_exists, format_size, format_duration


class DatabaseManager:
    """
    Gerenciador de database.json cumulativo
    Armazena metadados de todos os downloads
    """
    
    def __init__(self, config: Config = None):
        """
        Inicializa o gerenciador
        
        Args:
            config: Configuracoes customizadas
        """
        self.config = config or Config()
        self.db_path = self.config.get_base_path() / 'database.json'
        
    def _get_empty_database(self) -> Dict:
        """
        Retorna estrutura vazia do database
        
        Returns:
            Dict com estrutura inicial
        """
        return {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "totals": {
                "files": 0,
                "size_bytes": 0,
                "duration_seconds": 0
            },
            "by_type": {
                "video": {"count": 0, "size_bytes": 0, "duration_seconds": 0},
                "playlist": {"count": 0, "size_bytes": 0, "duration_seconds": 0},
                "channel": {"count": 0, "size_bytes": 0, "duration_seconds": 0},
                "txt": {"count": 0, "size_bytes": 0, "duration_seconds": 0}
            },
            "videos": {}
        }
    
    def load_database(self) -> Dict:
        """
        Carrega database.json do Drive
        Cria novo se nao existir
        
        Returns:
            Dict com dados do database
        """
        if not self.db_path.exists():
            print("Database nao existe, criando novo...")
            return self._get_empty_database()
        
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Erro ao ler database, criando novo: {e}")
            return self._get_empty_database()
    
    def save_database(self, data: Dict) -> bool:
        """
        Salva database.json no Drive
        
        Args:
            data: Dados a salvar
            
        Returns:
            True se salvou com sucesso
        """
        try:
            ensure_path_exists(self.db_path.parent)
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar database: {e}")
            return False
    
    def add_video(self, video_data: Dict, content_type: str = 'video') -> bool:
        """
        Adiciona ou atualiza video no database
        
        Args:
            video_data: Metadados do video
            content_type: Tipo (video, playlist, channel, txt)
            
        Returns:
            True se adicionou com sucesso
        """
        db = self.load_database()
        
        video_id = video_data.get('id')
        if not video_id:
            print("Erro: video_data sem 'id'")
            return False
        
        # Verifica se ja existe
        already_exists = video_id in db['videos']
        
        # Adiciona video
        db['videos'][video_id] = {
            'id': video_id,
            'title': video_data.get('title', 'Unknown'),
            'duration_seconds': video_data.get('duration', 0),
            'filesize_bytes': video_data.get('filesize', 0),
            'uploader': video_data.get('uploader', 'Unknown'),
            'download_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'audio_format': video_data.get('audio_format', self.config.AUDIO_FORMAT),
            'type': content_type
        }
        
        # Atualiza totais apenas se for video novo
        if not already_exists:
            db['totals']['files'] += 1
            db['totals']['size_bytes'] += video_data.get('filesize', 0)
            db['totals']['duration_seconds'] += video_data.get('duration', 0)
            
            # Atualiza por tipo
            if content_type in db['by_type']:
                db['by_type'][content_type]['count'] += 1
                db['by_type'][content_type]['size_bytes'] += video_data.get('filesize', 0)
                db['by_type'][content_type]['duration_seconds'] += video_data.get('duration', 0)
        
        # Atualiza timestamp
        db['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return self.save_database(db)
    
    def get_summary(self) -> Dict:
        """
        Retorna resumo formatado dos dados
        
        Returns:
            Dict com estatisticas formatadas
        """
        db = self.load_database()
        
        totals = db['totals']
        
        return {
            'available': True,
            'last_update': db.get('last_update', 'Nunca'),
            'total_files': totals['files'],
            'total_size': totals['size_bytes'],
            'total_size_formatted': format_size(totals['size_bytes']),
            'total_duration': totals['duration_seconds'],
            'total_duration_formatted': format_duration(totals['duration_seconds']),
            'by_type': {
                'video': {
                    'count': db['by_type']['video']['count'],
                    'size_formatted': format_size(db['by_type']['video']['size_bytes']),
                    'duration_formatted': format_duration(db['by_type']['video']['duration_seconds'])
                },
                'playlist': {
                    'count': db['by_type']['playlist']['count'],
                    'size_formatted': format_size(db['by_type']['playlist']['size_bytes']),
                    'duration_formatted': format_duration(db['by_type']['playlist']['duration_seconds'])
                },
                'channel': {
                    'count': db['by_type']['channel']['count'],
                    'size_formatted': format_size(db['by_type']['channel']['size_bytes']),
                    'duration_formatted': format_duration(db['by_type']['channel']['duration_seconds'])
                },
                'txt': {
                    'count': db['by_type']['txt']['count'],
                    'size_formatted': format_size(db['by_type']['txt']['size_bytes']),
                    'duration_formatted': format_duration(db['by_type']['txt']['duration_seconds'])
                }
            }
        }
    
    def recalculate_from_files(self) -> bool:
        """
        Recalcula database varrendo todos os arquivos
        Funcao de backup/emergencia
        
        Returns:
            True se recalculou com sucesso
        """
        print("Recalculando database a partir dos arquivos...")
        print("AVISO: Isso pode demorar com muitos arquivos!")
        
        base_path = self.config.get_base_path()
        
        if not base_path.exists():
            print(f"Erro: Pasta base nao existe: {base_path}")
            return False
        
        # Cria database novo
        db = self._get_empty_database()
        
        # Varre todos os arquivos
        audio_format = self.config.AUDIO_FORMAT
        
        for audio_file in base_path.rglob(f"*.{audio_format}"):
            # Extrai video_id do nome do arquivo
            video_id = audio_file.stem
            
            # Detecta tipo pela pasta pai
            parent_name = audio_file.parent.parent.name
            if parent_name.startswith('video_'):
                content_type = 'video'
            elif parent_name.startswith('Playlist_'):
                content_type = 'playlist'
            elif parent_name.startswith('Canal_'):
                content_type = 'channel'
            elif parent_name.startswith('txt_'):
                content_type = 'txt'
            else:
                content_type = 'video'
            
            # Obtem tamanho do arquivo
            filesize = audio_file.stat().st_size
            
            # Adiciona ao database
            # Nota: duracao e outros metadados nao podem ser recuperados
            # apenas do arquivo, precisaria do yt-dlp novamente
            db['videos'][video_id] = {
                'id': video_id,
                'title': 'Unknown (recalculado)',
                'duration_seconds': 0,  # Nao disponivel
                'filesize_bytes': filesize,
                'uploader': 'Unknown (recalculado)',
                'download_date': datetime.fromtimestamp(audio_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                'audio_format': audio_format,
                'type': content_type
            }
            
            # Atualiza totais
            db['totals']['files'] += 1
            db['totals']['size_bytes'] += filesize
            
            # Atualiza por tipo
            db['by_type'][content_type]['count'] += 1
            db['by_type'][content_type]['size_bytes'] += filesize
        
        print(f"Recalculo concluido: {db['totals']['files']} arquivos")
        
        return self.save_database(db)


if __name__ == "__main__":
    # Teste basico
    db_manager = DatabaseManager()
    print("DatabaseManager inicializado")
    
    summary = db_manager.get_summary()
    print(f"Total de arquivos: {summary['total_files']}")