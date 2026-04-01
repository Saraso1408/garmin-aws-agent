#!/usr/bin/env python3
"""
Script para upload de dados Garmin para o S3.
Suporta arquivos JSON e CSV da pasta data_samples/.
"""

import os
import sys
import boto3
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
DATA_SAMPLES_DIR = Path(__file__).parent / "data_samples"
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")


def get_s3_client():
    """Retorna cliente S3 configurado."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    return boto3.client("s3", region_name=region)


def identify_file_type(file_path: Path) -> str:
    """Identifica se o arquivo é CSV ou JSON."""
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        return "JSON"
    elif suffix == ".csv":
        return "CSV"
    return "UNKNOWN"


def list_local_files():
    """Lista arquivos JSON e CSV na pasta data_samples."""
    if not DATA_SAMPLES_DIR.exists():
        print(f"❌ Pasta {DATA_SAMPLES_DIR} não encontrada")
        return []
    
    files = []
    for ext in ["*.json", "*.csv"]:
        files.extend(DATA_SAMPLES_DIR.glob(ext))
    
    return sorted(files)


def upload_file(s3_client, local_path: Path, s3_key: str) -> bool:
    """Faz upload de um arquivo para o S3."""
    try:
        file_type = identify_file_type(local_path)
        print(f"📤 [{file_type}] Upload: {local_path.name}")
        
        extra_args = {}
        if local_path.suffix == ".json":
            extra_args["ContentType"] = "application/json"
        elif local_path.suffix == ".csv":
            extra_args["ContentType"] = "text/csv"
        
        s3_client.upload_file(
            str(local_path),
            BUCKET_NAME,
            s3_key,
            ExtraArgs=extra_args
        )
        
        print(f"✅ Concluído: s3://{BUCKET_NAME}/{s3_key}")
        return True
        
    except Exception as e:
        print(f"❌ Erro no upload de {local_path.name}: {e}")
        return False


def main():
    """Função principal do script."""
    print("🚀 Upload de dados Garmin para S3")
    
    # Verifica se bucket está configurado
    if not BUCKET_NAME:
        print("❌ Erro: Variável S3_BUCKET_NAME não encontrada no .env")
        sys.exit(1)
    
    print(f"🪣 Bucket: {BUCKET_NAME}")
    print(f"📁 Origem: {DATA_SAMPLES_DIR}")
    print()
    
    # Verifica bucket
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"✅ Bucket acessível")
    except Exception as e:
        print(f"❌ Erro ao acessar bucket: {e}")
        sys.exit(1)
    
    # Lista arquivos locais
    files = list_local_files()
    if not files:
        print("⚠️  Nenhum arquivo .json ou .csv encontrado em data_samples/")
        sys.exit(0)
    
    print(f"📋 {len(files)} arquivo(s) encontrado(s):")
    for f in files:
        file_type = identify_file_type(f)
        print(f"   • [{file_type}] {f.name}")
    print()
    
    # Upload - organiza por ano: raw-data/2026/
    uploaded = 0
    current_year = datetime.now().year
    
    for file_path in files:
        s3_key = f"raw-data/{current_year}/{file_path.name}"
        
        if upload_file(s3, file_path, s3_key):
            uploaded += 1
    
    print()
    print(f"📊 Resumo: {uploaded}/{len(files)} arquivo(s) enviado(s)")
    
    if uploaded > 0:
        print(f"🔗 s3://{BUCKET_NAME}/raw-data/{current_year}/")


if __name__ == "__main__":
    main()
