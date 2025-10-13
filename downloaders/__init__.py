#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downloaders Package - Katube Colab
Módulos de download e gerenciamento de armazenamento
"""

from .youtube_downloader import YouTubeDownloader
from .drive_manager import DriveManager

__all__ = ['YouTubeDownloader', 'DriveManager']
__version__ = '1.0.0'