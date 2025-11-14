#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metadata Manager - Katube Colab
Gerenciamento de metadados em CSV robusto (formato banco de dados relacional)
+ Sistema de backup em JSON individual por vídeo
"""

import pandas as pd
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config


class MetadataManager:
    """
    Gerenciador de metadados em CSV + JSON
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
        self.json_folder = self.base_path / "metadados"  # NOVO: Pasta de backups JSON

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
        self._ensure_json_folder()

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

    def _ensure_json_folder(self):
        """Cria pasta de metadados JSON se não existir"""
        try:
            self.json_folder.mkdir(parents=True, exist_ok=True)
            print(f"Pasta de metadados JSON: {self.json_folder}")
        except Exception as e:
            print(f"Erro ao criar pasta JSON: {e}")

    def _safe_int(self, value):
        """
        Converte valor para int de forma segura
        CRÍTICO: Lida com None, strings vazias e valores inválidos

        Args:
            value: Valor a converter

        Returns:
            int ou 0 se conversão falhar
        """
        if value is None:
            return 0
        if value == '':
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

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

    def _save_json_backup(self, result: Dict):
        """
        Salva metadados completos em JSON individual
        Backup completo com TODOS os campos extraídos (não apenas os 9 do CSV)

        Args:
            result: Dicionário com todos os metadados
        """
        try:
            video_id = result.get('id')
            if not video_id:
                return

            json_path = self.json_folder / f"{video_id}.json"

            # Salva TODOS os metadados extraídos
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"  ✓ JSON backup: {video_id}.json")

        except Exception as e:
            print(f"  ⚠ Aviso: Erro ao salvar JSON backup para {video_id}: {e}")

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

        # Salva JSON backup primeiro
        self._save_json_backup(metadata)

        # Prepara linha sanitizada
        row = {
            'id': self._sanitize_value(video_id),
            'title': self._sanitize_value(metadata.get('title', '')),
            'duration': self._safe_int(metadata.get('duration')),
            'upload_date': self._sanitize_value(metadata.get('upload_date', '')),
            'uploader': self._sanitize_value(metadata.get('uploader', '')),
            'uploader_id': self._sanitize_value(metadata.get('uploader_id', '')),
            'view_count': self._safe_int(metadata.get('view_count')),
            'like_count': self._safe_int(metadata.get('like_count')),
            'comment_count': self._safe_int(metadata.get('comment_count'))
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
            print("JSON backup foi salvo com sucesso!")
            return False

    def save_batch(self, results: List[Dict]) -> bool:
        """
        Salva batch de resultados no CSV E em JSON
        Sistema duplo: JSON (backup completo) + CSV (campos principais)

        Args:
            results: Lista de dicionários com resultados

        Returns:
            True se salvou com sucesso
        """
        if not results:
            print("Nenhum resultado para salvar")
            return True

        print("\n" + "="*80)
        print("SALVANDO METADADOS")
        print("="*80)

        # PRIMEIRO: Salva JSONs individuais (backup completo)
        print("\n1. Salvando backups JSON...")
        json_count = 0
        for result in results:
            if result.get('success') and not result.get('skipped'):
                self._save_json_backup(result)
                json_count += 1

        print(f"  ✓ {json_count} arquivos JSON salvos em: {self.json_folder}")

        # SEGUNDO: Salva no CSV (campos principais)
        print("\n2. Salvando no CSV consolidado...")

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
                if not video_id:
                    print(f"  ⚠ Pulando resultado sem ID")
                    continue

                if video_id in df_existing['id'].values:
                    print(f"  ⚠ ID {video_id} já existe no CSV, pulando...")
                    continue

                # DEBUG: Mostra valores recebidos
                print(f"\n  Processando: {video_id}")
                print(f"    - title: {result.get('title', 'N/A')[:50]}...")
                print(f"    - view_count: {result.get('view_count')} (tipo: {type(result.get('view_count'))})")
                print(f"    - like_count: {result.get('like_count')} (tipo: {type(result.get('like_count'))})")
                print(f"    - comment_count: {result.get('comment_count')} (tipo: {type(result.get('comment_count'))})")

                # Sanitiza e prepara linha usando _safe_int()
                row = {
                    'id': self._sanitize_value(video_id),
                    'title': self._sanitize_value(result.get('title', '')),
                    'duration': self._safe_int(result.get('duration')),
                    'upload_date': self._sanitize_value(result.get('upload_date', '')),
                    'uploader': self._sanitize_value(result.get('uploader', '')),
                    'uploader_id': self._sanitize_value(result.get('uploader_id', '')),
                    'view_count': self._safe_int(result.get('view_count')),
                    'like_count': self._safe_int(result.get('like_count')),
                    'comment_count': self._safe_int(result.get('comment_count'))
                }

                new_rows.append(row)
                print(f"  ✓ Preparado para CSV: {video_id}")

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

                print(f"\n  ✓ {len(new_rows)} registros adicionados ao CSV!")
                print(f"  ✓ CSV salvo em: {self.csv_path}")
                return True
            else:
                print("\n  ℹ Nenhum registro novo para adicionar ao CSV")
                return True

        except Exception as e:
            print(f"\n  ✗ ERRO ao salvar CSV: {e}")
            print("  ✓ Os backups JSON foram salvos com sucesso!")
            import traceback
            traceback.print_exc()
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
