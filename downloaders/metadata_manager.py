#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metadata Manager - Katube Colab
Gerenciamento de metadados completos em CSV consolidado
"""

import os
import sys
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    import pandas as pd
except ImportError:
    print("AVISO: pandas não instalado. Execute: pip install pandas")
    pd = None

from config import Config
from utils import format_size, format_duration


class MetadataManager:
    """
    Gerenciador de CSV consolidado de metadados
    Armazena TODOS os metadados de todos os downloads

    IMPORTANTE: Usa pipe (|) como separador do CSV para evitar conflitos
    com vírgulas presentes em títulos, descrições e tags.
    """

    def __init__(self, config: Config = None):
        """
        Inicializa o gerenciador

        Args:
            config: Configurações customizadas
        """
        if pd is None:
            raise ImportError("pandas é necessário. Execute: pip install pandas")

        self.config = config or Config()
        self.csv_path = self.config.get_metadata_csv_path()

    @staticmethod
    def _clean_field(value: Any) -> str:
        """
        Limpa e normaliza um campo para ser salvo no CSV
        Remove TODOS os caracteres problemáticos

        Args:
            value: Valor a ser limpo

        Returns:
            String limpa e segura para CSV
        """
        # Trata None, NaN, e valores vazios
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""

        # Trata listas - usa ponto-e-vírgula como separador interno
        if isinstance(value, list):
            if not value:  # Lista vazia
                return ""
            # Limpa cada item e junta com ponto-e-vírgula
            cleaned_items = []
            for item in value:
                if item is not None:
                    item_str = str(item).strip()
                    # Remove vírgulas e pipes dos itens
                    item_str = item_str.replace(',', ' ').replace('|', '-')
                    if item_str:
                        cleaned_items.append(item_str)
            return ";".join(cleaned_items) if cleaned_items else ""

        # Converte para string
        value_str = str(value).strip()

        # Retorna vazio se não há conteúdo
        if not value_str:
            return ""

        # CRÍTICO: Remove quebras de linha (substituir por espaço)
        value_str = value_str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        # Remove pipes (conflitam com separador)
        value_str = value_str.replace('|', '-')

        # Remove aspas duplas (podem quebrar CSV) - substitui por aspas simples
        value_str = value_str.replace('"', "'")

        # Remove múltiplos espaços
        value_str = ' '.join(value_str.split())

        return value_str

    @staticmethod
    def _clean_number(value: Any, default: int = 0) -> int:
        """
        Limpa e normaliza um campo numérico

        Args:
            value: Valor a ser limpo
            default: Valor padrão se inválido

        Returns:
            Número inteiro limpo
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default

        # Trata strings vazias
        if isinstance(value, str) and not value.strip():
            return default

        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _get_empty_dataframe(self) -> pd.DataFrame:
        """
        Retorna DataFrame vazio com estrutura completa

        Returns:
            DataFrame com colunas definidas
        """
        columns = [
            # Chave primária
            'id',

            # Informações Básicas
            'title',
            'description',
            'duration',
            'upload_date',
            'timestamp',

            # Canal/Uploader
            'uploader',
            'uploader_id',
            'uploader_url',
            'channel',
            'channel_id',
            'channel_url',

            # Estatísticas
            'view_count',
            'like_count',
            'comment_count',
            'average_rating',

            # Categorização
            'categories',
            'tags',
            'language',

            # Arquivo
            'audio_format',
            'file_path',
            'file_size_bytes',
            'download_date',
            'download_type'
        ]

        return pd.DataFrame(columns=columns)

    def load_csv(self) -> pd.DataFrame:
        """
        Carrega CSV do Drive
        Cria novo se não existir

        Returns:
            DataFrame com dados
        """
        if not self.csv_path.exists():
            print(f"CSV não existe, criando novo em: {self.csv_path}")
            df = self._get_empty_dataframe()
            df.to_csv(self.csv_path, index=False, encoding='utf-8', sep='|')
            return df

        try:
            df = pd.read_csv(
                self.csv_path,
                encoding='utf-8',
                sep='|',
                quoting=csv.QUOTE_MINIMAL,
                escapechar='\\',
                on_bad_lines='skip',        # CRÍTICO: Ignora linhas malformadas
                engine='python',            # Engine mais tolerante
                keep_default_na=False       # Não converte strings vazias em NaN
            )

            # Remove linhas completamente vazias
            df = df.dropna(how='all')

            # Garante que 'id' seja string
            if 'id' in df.columns:
                df['id'] = df['id'].astype(str)

            # Substitui NaN por string vazia em campos de texto
            text_columns = ['title', 'description', 'uploader', 'uploader_id', 'uploader_url',
                          'channel', 'channel_id', 'channel_url', 'upload_date', 'language',
                          'categories', 'tags', 'audio_format', 'file_path', 'download_type']

            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].fillna("")

            # Substitui NaN por 0 em campos numéricos
            numeric_columns = ['duration', 'timestamp', 'view_count', 'like_count',
                             'comment_count', 'average_rating', 'file_size_bytes']

            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].fillna(0).astype(int)

            return df

        except Exception as e:
            print(f"Erro ao ler CSV, criando novo: {e}")
            return self._get_empty_dataframe()

    def save_csv(self, df: pd.DataFrame) -> bool:
        """
        Salva DataFrame no CSV usando csv.DictWriter para controle total

        Args:
            df: DataFrame a salvar

        Returns:
            True se salvou com sucesso
        """
        try:
            # Garante que o diretório existe
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)

            # Define ordem dos campos (23 colunas)
            fieldnames = [
                'id', 'title', 'description', 'duration', 'upload_date',
                'timestamp', 'uploader', 'uploader_id', 'uploader_url',
                'channel', 'channel_id', 'channel_url', 'view_count',
                'like_count', 'comment_count', 'average_rating', 'categories',
                'tags', 'language', 'audio_format', 'file_path',
                'file_size_bytes', 'download_date', 'download_type'
            ]

            # Escreve CSV linha por linha com csv.DictWriter
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    delimiter='|',               # Separador pipe
                    quoting=csv.QUOTE_MINIMAL,   # Mínimo de aspas
                    escapechar='\\',             # Escape para casos especiais
                    lineterminator='\n'          # Força terminador Unix
                )

                # Escreve cabeçalho
                writer.writeheader()

                # Escreve cada linha
                for _, row in df.iterrows():
                    # Converte row para dict e garante que todos campos existem
                    row_dict = {}
                    for field in fieldnames:
                        value = row.get(field, '')
                        # Garante que valores vazios sejam strings vazias
                        if pd.isna(value) or value is None:
                            row_dict[field] = ''
                        else:
                            row_dict[field] = value

                    writer.writerow(row_dict)

            return True

        except Exception as e:
            print(f"Erro ao salvar CSV: {e}")
            return False

    def video_exists(self, video_id: str) -> bool:
        """
        Verifica se vídeo já existe no CSV

        Args:
            video_id: ID do vídeo

        Returns:
            True se existe
        """
        df = self.load_csv()

        if df.empty:
            return False

        return str(video_id) in df['id'].astype(str).values

    def add_video(self, metadata: Dict, content_type: str = 'video') -> bool:
        """
        Adiciona ou atualiza vídeo no CSV

        Args:
            metadata: Metadados completos do vídeo
            content_type: Tipo (video, playlist, channel, txt)

        Returns:
            True se adicionou com sucesso
        """
        video_id = metadata.get('id')
        if not video_id:
            print("Erro: metadata sem 'id'")
            return False

        df = self.load_csv()

        # Prepara dados do vídeo com limpeza completa
        video_data = {
            # Chave primária
            'id': str(video_id),

            # Informações Básicas
            'title': self._clean_field(metadata.get('title')),
            'description': self._clean_field(metadata.get('description')),
            'duration': self._clean_number(metadata.get('duration'), 0),
            'upload_date': self._clean_field(metadata.get('upload_date')),
            'timestamp': self._clean_number(metadata.get('timestamp'), 0),

            # Canal/Uploader
            'uploader': self._clean_field(metadata.get('uploader')),
            'uploader_id': self._clean_field(metadata.get('uploader_id')),
            'uploader_url': self._clean_field(metadata.get('uploader_url')),
            'channel': self._clean_field(metadata.get('channel')),
            'channel_id': self._clean_field(metadata.get('channel_id')),
            'channel_url': self._clean_field(metadata.get('channel_url')),

            # Estatísticas
            'view_count': self._clean_number(metadata.get('view_count'), 0),
            'like_count': self._clean_number(metadata.get('like_count'), 0),
            'comment_count': self._clean_number(metadata.get('comment_count'), 0),
            'average_rating': self._clean_number(metadata.get('average_rating'), 0),

            # Categorização (listas limpas e convertidas)
            'categories': self._clean_field(metadata.get('categories')),
            'tags': self._clean_field(metadata.get('tags')),
            'language': self._clean_field(metadata.get('language')),

            # Arquivo
            'audio_format': self._clean_field(metadata.get('audio_format', self.config.AUDIO_FORMAT)),
            'file_path': self._clean_field(metadata.get('file_path')),
            'file_size_bytes': self._clean_number(metadata.get('file_size_bytes'), 0),
            'download_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'download_type': self._clean_field(content_type)
        }

        # Remove vídeo existente (se houver)
        df = df[df['id'].astype(str) != str(video_id)]

        # Adiciona novo registro
        df = pd.concat([df, pd.DataFrame([video_data])], ignore_index=True)

        return self.save_csv(df)

    def save_batch(self, results: List[Dict], content_type: str = 'video') -> int:
        """
        Salva múltiplos vídeos de uma vez

        Args:
            results: Lista de resultados de download com metadados
            content_type: Tipo de conteúdo

        Returns:
            Número de vídeos salvos
        """
        saved = 0

        for result in results:
            if not result.get('success') or result.get('skipped'):
                continue

            metadata = result.get('metadata')
            if metadata and self.add_video(metadata, content_type):
                saved += 1

        return saved

    def get_summary(self) -> Dict:
        """
        Retorna resumo estatístico do CSV

        Returns:
            Dict com estatísticas
        """
        df = self.load_csv()

        if df.empty:
            return {
                'available': True,
                'total_videos': 0,
                'total_size': 0,
                'total_size_formatted': '0 B',
                'total_duration': 0,
                'total_duration_formatted': '0s',
                'by_type': {},
                'csv_path': str(self.csv_path)
            }

        # Estatísticas gerais
        total_videos = len(df)
        total_size = df['file_size_bytes'].sum() if 'file_size_bytes' in df.columns else 0
        total_duration = df['duration'].sum() if 'duration' in df.columns else 0

        # Estatísticas por tipo
        by_type = {}
        if 'download_type' in df.columns:
            for dtype in df['download_type'].unique():
                type_df = df[df['download_type'] == dtype]
                by_type[dtype] = {
                    'count': len(type_df),
                    'size_bytes': type_df['file_size_bytes'].sum() if 'file_size_bytes' in type_df.columns else 0,
                    'size_formatted': format_size(type_df['file_size_bytes'].sum() if 'file_size_bytes' in type_df.columns else 0),
                    'duration_seconds': type_df['duration'].sum() if 'duration' in type_df.columns else 0,
                    'duration_formatted': format_duration(int(type_df['duration'].sum()) if 'duration' in type_df.columns else 0)
                }

        return {
            'available': True,
            'total_videos': total_videos,
            'total_size': int(total_size),
            'total_size_formatted': format_size(int(total_size)),
            'total_duration': int(total_duration),
            'total_duration_formatted': format_duration(int(total_duration)),
            'by_type': by_type,
            'csv_path': str(self.csv_path)
        }

    def export_filtered(self, filter_dict: Dict, output_path: str) -> bool:
        """
        Exporta subconjunto filtrado do CSV

        Args:
            filter_dict: Dicionário com filtros (ex: {'download_type': 'playlist'})
            output_path: Caminho do arquivo de saída

        Returns:
            True se exportou com sucesso
        """
        try:
            df = self.load_csv()

            if df.empty:
                print("CSV vazio, nada para exportar")
                return False

            # Aplica filtros
            for column, value in filter_dict.items():
                if column in df.columns:
                    df = df[df[column] == value]

            # Define ordem dos campos (23 colunas)
            fieldnames = [
                'id', 'title', 'description', 'duration', 'upload_date',
                'timestamp', 'uploader', 'uploader_id', 'uploader_url',
                'channel', 'channel_id', 'channel_url', 'view_count',
                'like_count', 'comment_count', 'average_rating', 'categories',
                'tags', 'language', 'audio_format', 'file_path',
                'file_size_bytes', 'download_date', 'download_type'
            ]

            # Exporta com csv.DictWriter (mesmo método do save_csv)
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    delimiter='|',
                    quoting=csv.QUOTE_MINIMAL,
                    escapechar='\\',
                    lineterminator='\n'
                )

                writer.writeheader()

                for _, row in df.iterrows():
                    row_dict = {}
                    for field in fieldnames:
                        value = row.get(field, '')
                        if pd.isna(value) or value is None:
                            row_dict[field] = ''
                        else:
                            row_dict[field] = value
                    writer.writerow(row_dict)

            print(f"Exportados {len(df)} registros para: {output_path}")
            return True

        except Exception as e:
            print(f"Erro ao exportar: {e}")
            return False

    def get_video_metadata(self, video_id: str) -> Optional[Dict]:
        """
        Retorna metadados de um vídeo específico

        Args:
            video_id: ID do vídeo

        Returns:
            Dict com metadados ou None se não encontrado
        """
        df = self.load_csv()

        if df.empty:
            return None

        video_row = df[df['id'].astype(str) == str(video_id)]

        if video_row.empty:
            return None

        return video_row.iloc[0].to_dict()

    def validate_csv_integrity(self) -> bool:
        """
        Valida integridade do CSV após gravação
        Verifica estrutura, linhas vazias e número de colunas

        Returns:
            True se CSV está válido
        """
        if not self.csv_path.exists():
            print("CSV não existe ainda")
            return False

        try:
            df = self.load_csv()

            # Número esperado de colunas
            expected_cols = 23
            actual_cols = len(df.columns)

            print("=" * 60)
            print("VALIDAÇÃO DO CSV".center(60))
            print("=" * 60)

            # Verifica número de colunas
            if actual_cols != expected_cols:
                print(f"⚠️  AVISO: CSV tem {actual_cols} colunas, esperado {expected_cols}")
                print(f"Colunas encontradas: {list(df.columns)}")
                return False
            else:
                print(f"✓ Número de colunas correto: {expected_cols}")

            # Verifica linhas vazias
            empty_rows = df.isnull().all(axis=1).sum()
            if empty_rows > 0:
                print(f"⚠️  AVISO: {empty_rows} linhas vazias detectadas")
                # Remove linhas vazias e salva
                df_clean = df.dropna(how='all')
                self.save_csv(df_clean)
                print(f"✓ Linhas vazias removidas automaticamente")
            else:
                print(f"✓ Sem linhas vazias")

            # Verifica registros válidos
            valid_records = len(df)
            print(f"✓ Total de registros válidos: {valid_records}")

            # Verifica IDs únicos
            duplicated_ids = df['id'].duplicated().sum()
            if duplicated_ids > 0:
                print(f"⚠️  AVISO: {duplicated_ids} IDs duplicados encontrados")
            else:
                print(f"✓ Todos os IDs são únicos")

            # Verifica campos obrigatórios
            required_fields = ['id', 'title', 'download_date']
            missing_required = []
            for field in required_fields:
                if field not in df.columns:
                    missing_required.append(field)
                elif df[field].isnull().any():
                    null_count = df[field].isnull().sum()
                    print(f"⚠️  AVISO: Campo '{field}' tem {null_count} valores nulos")

            if missing_required:
                print(f"✗ Campos obrigatórios faltando: {missing_required}")
                return False
            else:
                print(f"✓ Todos os campos obrigatórios presentes")

            print("=" * 60)
            print("✓ CSV VALIDADO COM SUCESSO".center(60))
            print("=" * 60)

            return True

        except Exception as e:
            print(f"✗ Erro na validação: {e}")
            return False

    def print_summary(self):
        """Imprime resumo formatado"""
        summary = self.get_summary()

        print("=" * 60)
        print("RESUMO DO CSV DE METADADOS".center(60))
        print("=" * 60)
        print(f"Total de vídeos: {summary['total_videos']}")
        print(f"Tamanho total: {summary['total_size_formatted']}")
        print(f"Duração total: {summary['total_duration_formatted']}")
        print(f"Arquivo CSV: {summary['csv_path']}")

        if summary['by_type']:
            print("\nPOR TIPO:")
            for dtype, stats in summary['by_type'].items():
                print(f"  {dtype}: {stats['count']} vídeos ({stats['size_formatted']})")

        print("=" * 60)


if __name__ == "__main__":
    # Teste básico
    manager = MetadataManager()
    print("MetadataManager inicializado")
    manager.print_summary()
