#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações Centralizadas - Katube Colab
Sistema modular para download de áudio do YouTube com persistência no Google Drive
"""

from pathlib import Path
from typing import Optional


class Config:
    """
    Configurações centralizadas do Katube Colab
    Permite controle de todos os parâmetros de download
    """
    
    # ========================================================================
    # CONFIGURAÇÕES DE ÁUDIO
    # ========================================================================
    
    # Formato de áudio
    # Opções: 'flac', 'mp3', 'wav', 'm4a', 'opus'
    AUDIO_FORMAT = 'flac'
    
    # Qualidade de áudio (kbps)
    # 0 = melhor qualidade disponível
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
    SKIP_EXISTING = True  # True = pula se já existe, False = sobrescreve
    
    # Delay entre downloads (segundos)
    DELAY_MIN = 10
    DELAY_MAX = 20
    
    # Limite máximo de downloads por execução (0 = sem limite)
    MAX_DOWNLOADS = 0
    
    # ========================================================================
    # LOGS E RELATÓRIOS
    # ========================================================================
    
    # Ativar logs no terminal
    ENABLE_CONSOLE_LOG = True
    
    # Ativar logs em arquivo
    ENABLE_FILE_LOG = True
    
    # Pasta de logs
    LOG_FOLDER = 'logs'
    
    # ========================================================================
    # CONFIGURAÇÕES AVANÇADAS DO YT-DLP
    # ========================================================================
    
    # Filtros de duração de vídeo (segundos)
    MIN_DURATION = 30      # Mínimo 30 segundos
    MAX_DURATION = 7200    # Máximo 2 horas
    
    # Filtros de conteúdo
    SKIP_LIVE_STREAMS = True   # Pula transmissões ao vivo
    SKIP_PREMIERES = False     # Pula premieres
    SKIP_SHORTS = False        # Pula YouTube Shorts
    
    # Retry
    MAX_RETRIES = 3
    RETRY_DELAY = 60  # segundos
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    @classmethod
    def get_base_path(cls, folder_name: Optional[str] = None) -> Path:
        """
        Retorna o caminho completo da pasta base de downloads

        Args:
            folder_name: Nome customizado da pasta (usa BASE_FOLDER se None)

        Returns:
            Path completo para a pasta base
        """
        folder = folder_name or cls.BASE_FOLDER
        return Path(cls.DRIVE_ROOT) / folder
    
    @classmethod
    def get_log_path(cls) -> Path:
        """Retorna o caminho da pasta de logs"""
        return cls.get_base_path() / cls.LOG_FOLDER
    
    @classmethod
    def get_download_path(cls, content_type: str, content_id: str) -> Path:
        """
        Retorna o caminho completo para um tipo específico de download
        
        Args:
            content_type: 'playlist', 'channel', 'video', 'txt'
            content_id: ID do conteúdo
            
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
    def validate(cls) -> dict:
        """
        Valida as configurações
        
        Returns:
            Dict com status e mensagens
        """
        issues = []
        
        # Valida formato de áudio
        valid_formats = ['flac', 'mp3', 'wav', 'm4a', 'opus']
        if cls.AUDIO_FORMAT not in valid_formats:
            issues.append(f"Formato inválido: {cls.AUDIO_FORMAT}. Use: {valid_formats}")
        
        # Valida qualidade
        if cls.AUDIO_QUALITY < 0:
            issues.append("AUDIO_QUALITY deve ser >= 0")
        
        # Valida delays
        if cls.DELAY_MIN > cls.DELAY_MAX:
            issues.append("DELAY_MIN deve ser <= DELAY_MAX")
        
        # Valida durações
        if cls.MIN_DURATION > cls.MAX_DURATION:
            issues.append("MIN_DURATION deve ser <= MAX_DURATION")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    @classmethod
    def print_config(cls):
        """Imprime configuração atual de forma legível"""
        print("="*60)
        print("CONFIGURAÇÃO KATUBE COLAB")
        print("="*60)
        print(f"Formato de Áudio: {cls.AUDIO_FORMAT}")
        print(f"Qualidade: {cls.AUDIO_QUALITY} kbps" if cls.AUDIO_QUALITY > 0 else "Qualidade: Melhor disponível")
        print(f"Pasta Base: {cls.get_base_path()}")
        print(f"Skip Duplicatas: {cls.SKIP_EXISTING}")
        print(f"Delay: {cls.DELAY_MIN}-{cls.DELAY_MAX}s")
        print(f"Max Downloads: {cls.MAX_DOWNLOADS if cls.MAX_DOWNLOADS > 0 else 'Sem limite'}")
        print(f"Logs: Terminal={'Sim' if cls.ENABLE_CONSOLE_LOG else 'Não'}, Arquivo={'Sim' if cls.ENABLE_FILE_LOG else 'Não'}")
        print("="*60)


# Instância global para uso simples
config = Config()


if __name__ == "__main__":
    # Teste de validação
    validation = Config.validate()
    
    if validation['valid']:
        print("Configurações válidas!")
        Config.print_config()
    else:
        print("Erros encontrados:")
        for issue in validation['issues']:
            print(f"  - {issue}")