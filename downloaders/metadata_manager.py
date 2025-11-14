#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metadata Manager - Katube Colab
Gerenciamento de metadados em formato CSV
"""

import pandas as pd
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config
from utils import ensure_path_exists, format_size, format_duration


class MetadataManager:
    """
    Gerenciador de metadados em CSV
    Extrai, salva e gerencia dados dos videos
    """
    
    def __init__(self, config: Config = None):
        """
        Inicializa o gerenciador
        
        Args:
            config: Configuracoes customizadas
        """
        self.config = config or Config()
        self.csv_separator = self.config.CSV_SEPARATOR
        
    def extract_metadata(self, url: str) -> Optional[Dict]:
        """
        Extrai metadados completos de um video usando yt-dlp
        
        Args:
            url: URL do video
            
        Returns:
            Dict com metadados ou None se falhar
        """
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--no-warnings',
            '--skip-download',
            url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            raw_data = json.loads(result.stdout)
            
            # Extrai campos relevantes
            metadata = {
                'video_id': raw_data.get('id', ''),
                'title': raw_data.get('title', 'Unknown'),
                'duration_seconds': raw_data.get('duration', 0),
                'duration_formatted': format_duration(raw_data.get('duration', 0)),
                'upload_date': raw_data.get('upload_date', ''),
                'view_count': raw_data.get('view_count', 0),
                'like_count': raw_data.get('like_count', 0),
                'comment_count': raw_data.get('comment_count', 0),
                'channel_name': raw_data.get('uploader', 'Unknown'),
                'channel_id': raw_data.get('channel_id', ''),
                'subscriber_count': raw_data.get('channel_follower_count', 0),
                'category': raw_data.get('categories', ['Unknown'])[0] if raw_data.get('categories') else 'Unknown',
                'tags': ', '.join(raw_data.get('tags', [])) if raw_data.get('tags') else '',
                'description': raw_data.get('description', ''),
                'language': raw_data.get('language', ''),
                'url': raw_data.get('webpage_url', url),
                'filesize_bytes': 0,
                'filesize_formatted': '0 B',
                'audio_format': self.config.AUDIO_FORMAT,
                'audio_quality': self.config.AUDIO_QUALITY,
                'download_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'download_status': 'pending',
                'collection_type': ''
            }
            
            return metadata
            
        except Exception as e:
            print(f"Erro ao extrair metadados de {url}: {e}")
            return None
    
    def create_csv(self, csv_path: Path) -> bool:
        """
        Cria arquivo CSV com cabecalho
        
        Args:
            csv_path: Caminho do arquivo CSV
            
        Returns:
            True se criado com sucesso
        """
        try:
            columns = [
                'video_id', 'title', 'duration_seconds', 'duration_formatted',
                'upload_date', 'view_count', 'like_count', 'comment_count',
                'channel_name', 'channel_id', 'subscriber_count', 'category',
                'tags', 'description', 'language', 'audio_format', 'audio_quality',
                'filesize_bytes', 'filesize_formatted', 'download_date',
                'download_status', 'url', 'collection_type'
            ]
            
            df = pd.DataFrame(columns=columns)
            df.to_csv(csv_path, sep=self.csv_separator, index=False, encoding='utf-8')
            
            return True
            
        except Exception as e:
            print(f"Erro ao criar CSV: {e}")
            return False
    
    def load_csv(self, csv_path: Path) -> pd.DataFrame:
        """
        Carrega CSV existente
        
        Args:
            csv_path: Caminho do arquivo CSV
            
        Returns:
            DataFrame com dados ou DataFrame vazio
        """
        if not csv_path.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(csv_path, sep=self.csv_separator, encoding='utf-8')
            return df
        except Exception as e:
            print(f"Erro ao carregar CSV: {e}")
            return pd.DataFrame()
    
    def add_metadata(self, csv_path: Path, metadata: Dict) -> bool:
        """
        Adiciona metadados ao CSV
        
        Args:
            csv_path: Caminho do arquivo CSV
            metadata: Dados a adicionar
            
        Returns:
            True se adicionado com sucesso
        """
        try:
            # Garante que o CSV existe
            if not csv_path.exists():
                self.create_csv(csv_path)
            
            # Carrega CSV
            df = self.load_csv(csv_path)
            
            # Verifica se video_id ja existe
            if not df.empty and metadata['video_id'] in df['video_id'].values:
                # Atualiza linha existente
                df.loc[df['video_id'] == metadata['video_id']] = pd.Series(metadata)
            else:
                # Adiciona nova linha
                df = pd.concat([df, pd.DataFrame([metadata])], ignore_index=True)
            
            # Salva CSV
            df.to_csv(csv_path, sep=self.csv_separator, index=False, encoding='utf-8')
            
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar metadados ao CSV: {e}")
            return False
    
    def update_download_status(self, csv_path: Path, video_id: str, 
                               status: str, filesize: int = 0) -> bool:
        """
        Atualiza status de download no CSV
        
        Args:
            csv_path: Caminho do arquivo CSV
            video_id: ID do video
            status: Status ('success', 'failed', 'pending')
            filesize: Tamanho do arquivo em bytes
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            df = self.load_csv(csv_path)
            
            if df.empty or video_id not in df['video_id'].values:
                return False
            
            # Atualiza status
            df.loc[df['video_id'] == video_id, 'download_status'] = status
            
            # Atualiza filesize se fornecido
            if filesize > 0:
                df.loc[df['video_id'] == video_id, 'filesize_bytes'] = filesize
                df.loc[df['video_id'] == video_id, 'filesize_formatted'] = format_size(filesize)
            
            # Salva CSV
            df.to_csv(csv_path, sep=self.csv_separator, index=False, encoding='utf-8')
            
            return True
            
        except Exception as e:
            print(f"Erro ao atualizar status: {e}")
            return False
    
    def get_processed_ids(self, csv_path: Path) -> List[str]:
        """
        Retorna lista de video_ids ja processados
        
        Args:
            csv_path: Caminho do arquivo CSV
            
        Returns:
            Lista de video_ids
        """
        df = self.load_csv(csv_path)
        
        if df.empty:
            return []
        
        return df['video_id'].tolist()
    
    def get_successful_ids(self, csv_path: Path) -> List[str]:
        """
        Retorna lista de video_ids com download bem-sucedido
        
        Args:
            csv_path: Caminho do arquivo CSV
            
        Returns:
            Lista de video_ids
        """
        df = self.load_csv(csv_path)
        
        if df.empty:
            return []
        
        successful = df[df['download_status'] == 'success']
        return successful['video_id'].tolist()
    
    def get_summary(self, csv_path: Path) -> Dict:
        """
        Retorna resumo dos metadados
        
        Args:
            csv_path: Caminho do arquivo CSV
            
        Returns:
            Dict com estatisticas
        """
        df = self.load_csv(csv_path)
        
        if df.empty:
            return {
                'available': False,
                'total_videos': 0,
                'successful': 0,
                'failed': 0,
                'pending': 0
            }
        
        return {
            'available': True,
            'total_videos': len(df),
            'successful': len(df[df['download_status'] == 'success']),
            'failed': len(df[df['download_status'] == 'failed']),
            'pending': len(df[df['download_status'] == 'pending']),
            'total_size': df['filesize_bytes'].sum(),
            'total_size_formatted': format_size(df['filesize_bytes'].sum()),
            'total_duration': df['duration_seconds'].sum(),
            'total_duration_formatted': format_duration(df['duration_seconds'].sum())
        }


if __name__ == "__main__":
    # Teste basico
    manager = MetadataManager()
    print("MetadataManager inicializado")
