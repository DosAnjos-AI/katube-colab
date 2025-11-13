#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuracoes Centralizadas - Katube Colab
Sistema modular para download de audio do YouTube com persistencia no Google Drive
"""

from pathlib import Path
from typing import Optional


class Config:
    """
    Configuracoes centralizadas do Katube Colab
    Permite controle de todos os parametros de download
    """
    
    # ========================================================================
    # CONFIGURACOES DE AUDIO
    # ========================================================================
    
    # Formato de audio
    # Opcoes: 'mp3', 'flac', 'wav', 'm4a', 'opus'
    AUDIO_FORMAT = 'mp3'
    
    # Qualidade de audio (kbps)
    # 0 = melhor qualidade disponivel
    # Valores comuns: 128, 192, 256, 320
    AUDIO_QUALITY = 0
    
    # ========================================================================
    # ESTRUTURA DE PASTAS NO GOOGLE DRIVE
    # ========================================================================
    
    # Pasta raiz no Drive
    DRIVE_ROOT = '/content/drive/MyDrive'
    
    # Pasta base de downloads
    BASE_FOLDER = 'Katube_Download'
    
    # Prefixos para tipos de download
    PREFIX_PLAYLIST = 'Playlist'
    PREFIX_CHANNEL = 'Canal'
    PREFIX_VIDEO = 'video'
    PREFIX_TXT = 'txt'
    
    # ========================================================================
    # CONTROLE DE DOWNLOADS
    # ========================================================================
    
    # Comportamento com duplicatas
    SKIP_EXISTING = True  # True = pula se ja existe, False = sobrescreve
    
    # Delay entre downloads (segundos)
    DELAY_MIN = 10
    DELAY_MAX = 20
    
    # Limite maximo de downloads por execucao (0 = sem limite)
    MAX_DOWNLOADS = 0
    
    # ========================================================================
    # CSV E METADADOS
    # ========================================================================
    
    # Ativar geracao de CSV com metadados
    CSV_ENABLED = True
    
    # Nome do arquivo CSV
    CSV_FILENAME = 'metadados.csv'
    
    # Separador do CSV (usar | para evitar conflito com virgulas em titulos)
    CSV_SEPARATOR = '|'
    
    # ========================================================================
    # CHECKPOINT E RETOMADA
    # ========================================================================
    
    # Ativar sistema de checkpoint
    CHECKPOINT_ENABLED = True
    
    # Nome do arquivo de checkpoint
    CHECKPOINT_FILE = 'checkpoint.json'
    
    # ========================================================================
    # LOGS E RELATORIOS
    # ========================================================================
    
    # Ativar logs no terminal
    ENABLE_CONSOLE_LOG = True
    
    # Ativar logs em arquivo
    ENABLE_FILE_LOG = True
    
    # Pasta de logs
    LOG_FOLDER = 'logs'
    
    # ========================================================================
    # CONFIGURACOES AVANCADAS DO YT-DLP
    # ========================================================================
    
    # Filtros de duracao de video (segundos)
    MIN_DURATION = 30      # Minimo 30 segundos
    MAX_DURATION = 7200    # Maximo 2 horas
    
    # Filtros de conteudo
    SKIP_LIVE_STREAMS = True   # Pula transmissoes ao vivo
    SKIP_PREMIERES = False     # Pula premieres
    SKIP_SHORTS = False        # Pula YouTube Shorts
    
    # Retry
    MAX_RETRIES = 3
    RETRY_DELAY = 60  # segundos
    
    # ========================================================================
    # METODOS AUXILIARES
    # ========================================================================
    
    @classmethod
    def get_base_path(cls) -> Path:
        """Retorna o caminho completo da pasta base de downloads"""
        return Path(cls.DRIVE_ROOT) / cls.BASE_FOLDER
    
    @classmethod
    def get_log_path(cls) -> Path:
        """Retorna o caminho da pasta de logs"""
        return cls.get_base_path() / cls.LOG_FOLDER
    
    @classmethod
    def get_download_path(cls, content_type: str, content_id: str) -> Path:
        """
        Retorna o caminho completo para um tipo especifico de download
        
        Args:
            content_type: 'playlist', 'channel', 'video', 'txt'
            content_id: ID do conteudo
            
        Returns:
            Path completo para o download
        """
        prefix_map = {
            'playlist': cls.PREFIX_PLAYLIST,
            'channel': cls.PREFIX_CHANNEL,
            'video': cls.PREFIX_VIDEO,
            'txt': cls.PREFIX_TXT
        }
        
        prefix = prefix_map.get(content_type, 'unknown')
        folder_name = f"{prefix}_{content_id}"
        
        return cls.get_base_path() / folder_name
    
    @classmethod
    def get_csv_path(cls, download_path: Path) -> Path:
        """
        Retorna o caminho do arquivo CSV para um download
        
        Args:
            download_path: Caminho da pasta de download
            
        Returns:
            Path do arquivo CSV
        """
        return download_path / cls.CSV_FILENAME
    
    @classmethod
    def get_checkpoint_path(cls, download_path: Path) -> Path:
        """
        Retorna o caminho do arquivo de checkpoint
        
        Args:
            download_path: Caminho da pasta de download
            
        Returns:
            Path do arquivo checkpoint
        """
        return download_path / cls.CHECKPOINT_FILE
    
    @classmethod
    def validate(cls) -> dict:
        """
        Valida as configuracoes
        
        Returns:
            Dict com status e mensagens
        """
        issues = []
        
        # Valida formato de audio
        valid_formats = ['mp3', 'flac', 'wav', 'm4a', 'opus']
        if cls.AUDIO_FORMAT not in valid_formats:
            issues.append(f"Formato invalido: {cls.AUDIO_FORMAT}. Use: {valid_formats}")
        
        # Valida qualidade
        if cls.AUDIO_QUALITY < 0:
            issues.append("AUDIO_QUALITY deve ser >= 0")
        
        # Valida delays
        if cls.DELAY_MIN > cls.DELAY_MAX:
            issues.append("DELAY_MIN deve ser <= DELAY_MAX")
        
        # Valida duracoes
        if cls.MIN_DURATION > cls.MAX_DURATION:
            issues.append("MIN_DURATION deve ser <= MAX_DURATION")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    @classmethod
    def print_config(cls):
        """Imprime configuracao atual de forma legivel"""
        print("="*60)
        print("CONFIGURACAO KATUBE COLAB")
        print("="*60)
        print(f"Formato de Audio: {cls.AUDIO_FORMAT}")
        print(f"Qualidade: {cls.AUDIO_QUALITY} kbps" if cls.AUDIO_QUALITY > 0 else "Qualidade: Melhor disponivel")
        print(f"Pasta Base: {cls.get_base_path()}")
        print(f"Skip Duplicatas: {cls.SKIP_EXISTING}")
        print(f"Delay: {cls.DELAY_MIN}-{cls.DELAY_MAX}s")
        print(f"Max Downloads: {cls.MAX_DOWNLOADS if cls.MAX_DOWNLOADS > 0 else 'Sem limite'}")
        print(f"CSV Habilitado: {'Sim' if cls.CSV_ENABLED else 'Nao'}")
        print(f"Checkpoint Habilitado: {'Sim' if cls.CHECKPOINT_ENABLED else 'Nao'}")
        print(f"Logs: Terminal={'Sim' if cls.ENABLE_CONSOLE_LOG else 'Nao'}, Arquivo={'Sim' if cls.ENABLE_FILE_LOG else 'Nao'}")
        print("="*60)


# Instancia global para uso simples
config = Config()


if __name__ == "__main__":
    # Teste de validacao
    validation = Config.validate()
    
    if validation['valid']:
        print("Configuracoes validas!")
        Config.print_config()
    else:
        print("Erros encontrados:")
        for issue in validation['issues']:
            print(f"  - {issue}")
