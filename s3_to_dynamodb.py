#!/usr/bin/env python3
"""
Script para ler dados do S3 e salvar no DynamoDB.
Processa arquivos JSON/CSV e insere na tabela GarminHealthStats.
"""

import os
import sys
import json
import boto3
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from io import StringIO

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
TABLE_NAME = "GarminHealthStats"
S3_PREFIX = "raw-data/"


def get_s3_client():
    """Retorna cliente S3 configurado."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    return boto3.client("s3", region_name=region)


def get_dynamodb_table():
    """Retorna recurso da tabela DynamoDB."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    dynamodb = boto3.resource("dynamodb", region_name=region)
    return dynamodb.Table(TABLE_NAME)


def list_s3_files(s3_client, year=None):
    """Lista arquivos JSON e CSV no S3."""
    if not year:
        year = datetime.now().year
    
    prefix = f"{S3_PREFIX}{year}/"
    
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        
        if "Contents" not in response:
            print(f"⚠️  Nenhum arquivo encontrado em s3://{BUCKET_NAME}/{prefix}")
            return []
        
        files = []
        for obj in response["Contents"]:
            key = obj["Key"]
            if key.endswith(".json") or key.endswith(".csv"):
                files.append(key)
        
        return files
        
    except Exception as e:
        print(f"❌ Erro ao listar arquivos no S3: {e}")
        return []


def read_s3_file(s3_client, s3_key: str):
    """Lê arquivo do S3 e retorna conteúdo como string."""
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        content = response["Body"].read().decode("utf-8")
        return content
    except Exception as e:
        print(f"❌ Erro ao ler {s3_key}: {e}")
        return None


def process_data(content: str, file_type: str):
    """Processa dados usando pandas, garantindo DataType e Timestamp."""
    try:
        if file_type == "json":
            # Tenta carregar como JSON
            data = json.loads(content)
            
            # Se for um único objeto, converte para lista
            if isinstance(data, dict):
                data = [data]
            
            df = pd.DataFrame(data)
            
        elif file_type == "csv":
            df = pd.read_csv(StringIO(content))
        else:
            print(f"❌ Tipo de arquivo não suportado: {file_type}")
            return None
        
        # Garante colunas DataType e Timestamp
        if "DataType" not in df.columns:
            # Tenta inferir do nome do arquivo ou usar default
            df["DataType"] = "Sono"  # Default, pode ser ajustado
        
        if "Timestamp" not in df.columns:
            # Usa data atual se não houver timestamp
            df["Timestamp"] = datetime.now().strftime("%Y-%m-%d")
        
        # Normaliza Timestamp para formato YYYY-MM-DD
        df["Timestamp"] = pd.to_datetime(df["Timestamp"]).dt.strftime("%Y-%m-%d")
        
        return df
        
    except Exception as e:
        print(f"❌ Erro ao processar dados: {e}")
        return None


def save_to_dynamodb(table, df: pd.DataFrame) -> int:
    """Salva DataFrame no DynamoDB usando put_item."""
    saved_count = 0
    
    for _, row in df.iterrows():
        try:
            # Converte row para dicionário, tratando valores NaN
            item = {}
            for col, value in row.items():
                if pd.isna(value):
                    item[col] = None
                elif isinstance(value, (int, float)):
                    item[col] = value
                else:
                    item[col] = str(value)
            
            # Adiciona campos obrigatórios se não existirem
            if "DataType" not in item or not item["DataType"]:
                item["DataType"] = "Sono"
            if "Timestamp" not in item or not item["Timestamp"]:
                item["Timestamp"] = datetime.now().strftime("%Y-%m-%d")
            
            # Salva no DynamoDB
            table.put_item(Item=item)
            saved_count += 1
            
        except Exception as e:
            print(f"❌ Erro ao salvar registro: {e}")
            continue
    
    return saved_count


def main():
    """Função principal do script."""
    print("🚀 S3 → DynamoDB: Processando dados Garmin")
    
    # Verifica configurações
    if not BUCKET_NAME:
        print("❌ Erro: Variável S3_BUCKET_NAME não encontrada no .env")
        sys.exit(1)
    
    print(f"🪣 Bucket: {BUCKET_NAME}")
    print(f"📊 Tabela DynamoDB: {TABLE_NAME}")
    print()
    
    # Inicializa clientes
    s3 = get_s3_client()
    table = get_dynamodb_table()
    
    # Verifica tabela
    try:
        table.load()
        print(f"✅ Tabela '{TABLE_NAME}' acessível")
    except Exception as e:
        print(f"❌ Erro ao acessar tabela DynamoDB: {e}")
        sys.exit(1)
    
    # Lista arquivos no S3
    current_year = datetime.now().year
    s3_files = list_s3_files(s3, year=current_year)
    
    if not s3_files:
        print(f"⚠️  Nenhum arquivo encontrado em raw-data/{current_year}/")
        sys.exit(0)
    
    print(f"📋 {len(s3_files)} arquivo(s) encontrado(s):")
    for f in s3_files:
        print(f"   • {f}")
    print()
    
    # Processa cada arquivo
    total_saved = 0
    
    for s3_key in s3_files:
        file_type = "json" if s3_key.endswith(".json") else "csv"
        print(f"📥 Lendo: {s3_key}")
        
        # Lê do S3
        content = read_s3_file(s3, s3_key)
        if not content:
            continue
        
        # Processa com pandas
        df = process_data(content, file_type)
        if df is None or df.empty:
            print(f"⚠️  Nenhum dado válido em {s3_key}")
            continue
        
        print(f"📊 Registros encontrados: {len(df)}")
        print(f"   Colunas: {list(df.columns)}")
        
        # Salva no DynamoDB
        saved = save_to_dynamodb(table, df)
        total_saved += saved
        print(f"✅ {saved}/{len(df)} registros salvos no DynamoDB")
        print()
    
    print(f"📊 Total: {total_saved} registros salvos na tabela '{TABLE_NAME}'")


if __name__ == "__main__":
    main()
