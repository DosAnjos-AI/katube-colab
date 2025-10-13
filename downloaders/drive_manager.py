#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Drive Manager - Katube Colab
Gerenciamento de persistência no Google Drive
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config
from utils import ensure_path_exists, get_date_string, format_size


class DriveManager:
    """
    Gerenciador de armazenamento no Google Drive
    Lida com logs, verificação de espaço e estrutura de pastas
    """
    
    def __init__(self, config: Config = None):
        """
        Inicializa o gerenciador
        
        Args:
            config: Configurações customizadas
        """
        self.config = config or Config()
        self.drive_mounted = False
        
    def mount_drive(self) -> bool:
        """
        Monta o Google Drive no Colab
        
        Returns:
            True se montado com sucesso
        """
        try:
            from google.colab import drive
            
            print("Montando Google Drive...")
            drive.mount('/content/drive', force_remount=False)
            
            # Verifica se montou
            drive_path = Path(self.config.DRIVE_ROOT)
            self.drive_mounted = drive_path.exists()
            
            if self.drive_mounted:
                print(f"Drive montado: {drive_path}")
                return True
            else:
                print("Erro: Drive não foi montado")
                return False
                
        except ImportError:
            print("Aviso: google.colab não disponível (rodando localmente?)")
            self.drive_mounted = True  # Assume montado em ambiente local
            return True
        except Exception as e:
            print(f"Erro ao montar Drive: {e}")
            return False
    
    def setup_folder_structure(self) -> bool:
        """
        Cria estrutura de pastas base no Drive
        
        Returns:
            True se criado com sucesso
        """
        try:
            base_path = self.config.get_base_path()
            log_path = self.config.get_log_path()
            
            ensure_path_exists(base_path)
            ensure_path_exists(log_path)
            
            print(f"Estrutura criada:")
            print(f"  Base: {base_path}")
            print(f"  Logs: {log_path}")
            
            return True
            
        except Exception as e:
            print(f"Erro ao criar estrutura: {e}")
            return False
    
    def check_drive_space(self) -> Dict:
        """
        Verifica espaço disponível no Drive
        
        Returns:
            Dict com informações de espaço
        """
        try:
            import shutil
            
            drive_path = Path(self.config.DRIVE_ROOT)
            
            if not drive_path.exists():
                return {'available': False, 'error': 'Drive não montado'}
            
            stat = shutil.disk_usage(drive_path)
            
            return {
                'available': True,
                'total': stat.total,
                'used': stat.used,
                'free': stat.free,
                'total_formatted': format_size(stat.total),
                'used_formatted': format_size(stat.used),
                'free_formatted': format_size(stat.free),
                'usage_percent': (stat.used / stat.total) * 100
            }
            
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    def log_download(self, log_data: Dict) -> bool:
        """
        Salva log de download no Drive
        
        Args:
            log_data: Dados do download para logar
            
        Returns:
            True se salvou com sucesso
        """
        if not self.config.ENABLE_FILE_LOG:
            return True
        
        try:
            log_path = self.config.get_log_path()
            log_file = log_path / f"download_{get_date_string()}.log"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            log_entry = {
                'timestamp': timestamp,
                'data': log_data
            }
            
            # Append ao arquivo de log
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar log: {e}")
            return False
    
    def log_error(self, error_data: Dict) -> bool:
        """
        Salva log de erro no Drive
        
        Args:
            error_data: Dados do erro
            
        Returns:
            True se salvou com sucesso
        """
        if not self.config.ENABLE_FILE_LOG:
            return True
        
        try:
            log_path = self.config.get_log_path()
            error_file = log_path / f"errors_{get_date_string()}.log"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            error_entry = {
                'timestamp': timestamp,
                'error': error_data
            }
            
            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_entry, ensure_ascii=False) + '\n')
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar log de erro: {e}")
            return False
    
    def get_download_summary(self) -> Dict:
        """
        Gera resumo dos downloads no Drive
        
        Returns:
            Dict com estatísticas
        """
        try:
            base_path = self.config.get_base_path()
            
            if not base_path.exists():
                return {'available': False, 'error': 'Pasta base não existe'}
            
            summary = {
                'total_folders': 0,
                'total_files': 0,
                'total_size': 0,
                'by_type': {
                    'video': 0,
                    'playlist': 0,
                    'channel': 0,
                    'txt': 0
                }
            }
            
            # Conta arquivos e pastas
            for item in base_path.iterdir():
                if item.is_dir() and item.name != 'logs':
                    summary['total_folders'] += 1
                    
                    # Detecta tipo pela pasta
                    if item.name.startswith('video_'):
                        summary['by_type']['video'] += 1
                    elif item.name.startswith('Playlist_'):
                        summary['by_type']['playlist'] += 1
                    elif item.name.startswith('Canal_'):
                        summary['by_type']['channel'] += 1
                    elif item.name.startswith('txt_'):
                        summary['by_type']['txt'] += 1
                    
                    # Conta arquivos de áudio
                    for audio_file in item.rglob(f"*.{self.config.AUDIO_FORMAT}"):
                        summary['total_files'] += 1
                        summary['total_size'] += audio_file.stat().st_size
            
            summary['total_size_formatted'] = format_size(summary['total_size'])
            summary['available'] = True
            
            return summary
            
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    def cleanup_empty_folders(self) -> int:
        """
        Remove pastas vazias da estrutura
        
        Returns:
            Número de pastas removidas
        """
        try:
            base_path = self.config.get_base_path()
            removed = 0
            
            for item in base_path.rglob('*'):
                if item.is_dir() and not any(item.iterdir()):
                    item.rmdir()
                    removed += 1
                    print(f"Removida pasta vazia: {item.name}")
            
            return removed
            
        except Exception as e:
            print(f"Erro no cleanup: {e}")
            return 0


if __name__ == "__main__":
    # Teste básico
    manager = DriveManager()
    print("DriveManager inicializado")
    
    # Testa verificação de espaço (se Drive estiver montado)
    space_info = manager.check_drive_space()
    if space_info['available']:
        print(f"Espaço livre: {space_info['free_formatted']}")