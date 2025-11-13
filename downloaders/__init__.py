#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downloaders Package - Katube Colab
Modulos de download e gerenciamento de armazenamento
"""

from .youtube_downloader import YouTubeDownloader
from .drive_manager import DriveManager
from .database_manager import DatabaseManager
from .metadata_manager import MetadataManager

__all__ = ['YouTubeDownloader', 'DriveManager', 'DatabaseManager', 'MetadataManager']
__version__ = '2.0.0'