#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metadata Manager - Katube Colab
Gerenciamento de metadados em CSV robusto (formato banco de dados relacional)
"""

import pandas as pd
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config


class MetadataManager:
    """
    Gerenciador de metadados em CSV
    Garante integridade: 1 linha = 1 tupla (sem quebras de linha nos campos)
    """

    def __init__(self, base_folder: str = "Katube_Download"):
        """
        Inicializa o gerenciador

        Args:
            base_folder: Nome da pasta base no Google Drive
        """
        self.base_folder = base_folder
        self.base_path = Path("/content/drive/MyDrive") / base_folder
        self.csv_path = self.base_path / "metadata.csv"

        # Colunas do CSV (9 campos conforme especificação)
        self.columns = [
            'id',              # ID do vídeo
            'title',           # Título
            'duration',        # Duração em segundos
            'upload_date',     # Data de upload (YYYYMMDD)
            'uploader',        # Nome do canal
            'uploader_id',     # ID do canal
            'view_count',      # Número de visualizações
            'like_count',      # Número de likes
            'comment_count'    # Número de comentários
        ]

        self._ensure_csv()

    def _ensure_csv(self):
        """Cria CSV se não existir"""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)

            if not self.csv_path.exists():
                df = pd.DataFrame(columns=self.columns)
                df.to_csv(self.csv_path, sep='|', index=False)
                print(f"CSV criado: {self.csv_path}")
        except Exception as e:
            print(f"Erro ao criar CSV: {e}")

    def _sanitize_value(self, value):
        """
        Remove quebras de linha e sanitiza valores
        CRÍTICO: Garante que não haja quebras de linha nos campos

        Args:
            value: Valor a sanitizar

        Returns:
            String sanitizada
        """
        if value is None:
            return ""

        value = str(value)

        # Remove TODAS quebras de linha (\n, \r, \r\n)
        value = value.replace('\n', ' ').replace('\r', ' ')

        # Remove pipes extras (delimitador)
        value = value.replace('|', '-')

        # Remove espaços duplicados
        value = ' '.join(value.split())

        # Remove caracteres de controle
        value = ''.join(char for char in value if ord(char) >= 32 or char == '\t')

        return value.strip()

    def _id_exists(self, video_id: str) -> bool:
        """
        Verifica se ID já existe no CSV

        Args:
            video_id: ID do vídeo

        Returns:
            True se existe, False caso contrário
        """
        try:
            if not self.csv_path.exists():
                return False

            df = pd.read_csv(self.csv_path, delimiter='|', dtype=str)

            if df.empty:
                return False

            return video_id in df['id'].values

        except Exception as e:
            print(f"Erro ao verificar ID: {e}")
            return False

    def save_metadata(self, metadata: Dict) -> bool:
        """
        Salva metadados de um único vídeo

        Args:
            metadata: Dicionário com metadados do vídeo

        Returns:
            True se salvou com sucesso
        """
        video_id = metadata.get('id')

        if not video_id:
            print("Erro: metadata sem 'id'")
            return False

        # Skip se já existe
        if self._id_exists(video_id):
            print(f"Skip: {video_id} já existe no CSV")
            return True

        # Prepara linha sanitizada
        row = {
            'id': self._sanitize_value(video_id),
            'title': self._sanitize_value(metadata.get('title', '')),
            'duration': int(metadata.get('duration', 0)),
            'upload_date': self._sanitize_value(metadata.get('upload_date', '')),
            'uploader': self._sanitize_value(metadata.get('uploader', '')),
            'uploader_id': self._sanitize_value(metadata.get('uploader_id', '')),
            'view_count': int(metadata.get('view_count', 0)),
            'like_count': int(metadata.get('like_count', 0)),
            'comment_count': int(metadata.get('comment_count', 0))
        }

        try:
            # Carrega CSV existente
            df_existing = pd.read_csv(self.csv_path, delimiter='|', dtype=str)

            # Adiciona nova linha
            df_new = pd.DataFrame([row])
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)

            # Salva com configurações robustas
            df_combined.to_csv(
                self.csv_path,
                sep='|',
                index=False,
                quoting=csv.QUOTE_MINIMAL,
                escapechar='\\',
                lineterminator='\n'
            )

            print(f"Salvo no CSV: {video_id}")
            return True

        except Exception as e:
            print(f"Erro ao salvar no CSV: {e}")
            return False

    def save_batch(self, results: List[Dict]) -> bool:
        """
        Salva batch de resultados no CSV

        Args:
            results: Lista de dicionários com resultados

        Returns:
            True se salvou com sucesso
        """
        if not results:
            return True

        try:
            # Carrega CSV existente
            df_existing = pd.read_csv(self.csv_path, delimiter='|', dtype=str)

            # Prepara novos dados
            new_rows = []

            for result in results:
                # Pula se não teve sucesso ou se foi skip
                if not result.get('success') or result.get('skipped'):
                    continue

                # Pula se já existe
                video_id = result.get('id')
                if not video_id or self._id_exists(video_id):
                    continue

                # Sanitiza e prepara linha
                row = {
                    'id': self._sanitize_value(video_id),
                    'title': self._sanitize_value(result.get('title', '')),
                    'duration': int(result.get('duration', 0)),
                    'upload_date': self._sanitize_value(result.get('upload_date', '')),
                    'uploader': self._sanitize_value(result.get('uploader', '')),
                    'uploader_id': self._sanitize_value(result.get('uploader_id', '')),
                    'view_count': int(result.get('view_count', 0)),
                    'like_count': int(result.get('like_count', 0)),
                    'comment_count': int(result.get('comment_count', 0))
                }

                new_rows.append(row)

            if new_rows:
                df_new = pd.DataFrame(new_rows)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)

                # Salva com configurações robustas
                df_combined.to_csv(
                    self.csv_path,
                    sep='|',
                    index=False,
                    quoting=csv.QUOTE_MINIMAL,
                    escapechar='\\',
                    lineterminator='\n'
                )

                print(f"\nAdicionados {len(new_rows)} novos registros ao CSV")
                return True
            else:
                print("\nNenhum novo registro para adicionar ao CSV")
                return True

        except Exception as e:
            print(f"Erro ao salvar batch no CSV: {e}")
            return False

    def get_stats(self) -> Dict:
        """
        Retorna estatísticas do CSV

        Returns:
            Dict com estatísticas
        """
        try:
            if not self.csv_path.exists():
                return {
                    'available': False,
                    'total': 0,
                    'error': 'CSV não existe'
                }

            df = pd.read_csv(self.csv_path, delimiter='|')

            if df.empty:
                return {
                    'available': True,
                    'total': 0,
                    'total_duration': 0,
                    'total_views': 0,
                    'total_likes': 0
                }

            # Converte colunas numéricas
            df['duration'] = pd.to_numeric(df['duration'], errors='coerce').fillna(0)
            df['view_count'] = pd.to_numeric(df['view_count'], errors='coerce').fillna(0)
            df['like_count'] = pd.to_numeric(df['like_count'], errors='coerce').fillna(0)

            return {
                'available': True,
                'total': len(df),
                'total_duration': int(df['duration'].sum()),
                'total_duration_hours': round(df['duration'].sum() / 3600, 2),
                'total_views': int(df['view_count'].sum()),
                'total_likes': int(df['like_count'].sum()),
                'avg_duration': int(df['duration'].mean()) if len(df) > 0 else 0,
                'avg_views': int(df['view_count'].mean()) if len(df) > 0 else 0
            }

        except Exception as e:
            return {
                'available': False,
                'total': 0,
                'error': str(e)
            }

    def validate_csv(self) -> Dict:
        """
        Valida integridade do CSV

        Returns:
            Dict com status da validação
        """
        issues = []

        try:
            if not self.csv_path.exists():
                return {
                    'valid': False,
                    'issues': ['CSV não existe']
                }

            df = pd.read_csv(self.csv_path, delimiter='|', dtype=str)

            # Verifica colunas
            if list(df.columns) != self.columns:
                issues.append(f"Colunas incorretas: {list(df.columns)}")

            # Verifica IDs duplicados
            if df['id'].duplicated().any():
                duplicates = df[df['id'].duplicated()]['id'].tolist()
                issues.append(f"IDs duplicados: {duplicates}")

            # Verifica quebras de linha nos valores (CRÍTICO)
            for col in df.columns:
                for idx, val in enumerate(df[col]):
                    if isinstance(val, str) and ('\n' in val or '\r' in val):
                        issues.append(f"Quebra de linha encontrada: linha {idx+2}, coluna '{col}'")

            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'total_rows': len(df)
            }

        except Exception as e:
            return {
                'valid': False,
                'issues': [f'Erro ao validar: {str(e)}']
            }


if __name__ == "__main__":
    # Teste básico
    manager = MetadataManager()
    print("MetadataManager inicializado")

    stats = manager.get_stats()
    print(f"Total de registros: {stats.get('total', 0)}")

    validation = manager.validate_csv()
    if validation['valid']:
        print("CSV válido!")
    else:
        print("Problemas encontrados:")
        for issue in validation['issues']:
            print(f"  - {issue}")
