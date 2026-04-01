#!/usr/bin/env python3
"""
Script para testar localmente a lambda_function.py.
Simula o evento enviado pelo Amazon Bedrock Agent.
"""

import json
import sys
from pathlib import Path

# Adiciona o diretório lambda ao path para importar o módulo
sys.path.insert(0, str(Path(__file__).parent))

from lambda_function import lambda_handler


def create_bedrock_mock_event(action_group: str, api_path: str, parameters: list = None):
    """
    Cria um mock do evento que o Amazon Bedrock Agent envia para a Lambda.
    
    Estrutura baseada em:
    https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
    """
    if parameters is None:
        parameters = []
    
    # Formato do evento Bedrock Agent
    mock_event = {
        "messageVersion": "1.0",
        "agent": {
            "alias": "TSTALIASID",
            "name": "GarminAgent",
            "version": "DRAFT",
            "id": "AGENT123456"
        },
        "inputText": "Buscar dados de sono de 2024-03-01",
        "sessionId": "session-12345-abcde",
        "actionGroup": action_group,
        "apiPath": api_path,
        "httpMethod": "POST",
        "parameters": [
            {
                "name": param["name"],
                "type": param.get("type", "string"),
                "value": param["value"]
            }
            for param in (parameters or [])
        ],
        "requestBody": {
            "content": {
                "application/json": {
                    "properties": [
                        {
                            "name": "timestamp",
                            "value": next((p["value"] for p in parameters if p["name"] == "timestamp"), None)
                        },
                        {
                            "name": "data_type",
                            "value": next((p["value"] for p in parameters if p["name"] == "data_type"), None)
                        }
                    ]
                }
            }
        }
    }
    
    return mock_event


def run_test(description: str, action_group: str, api_path: str, parameters: list = None):
    """Executa um teste e imprime o resultado."""
    print(f"\n{'='*60}")
    print(f"🧪 TESTE: {description}")
    print(f"{'='*60}")
    
    # Cria o mock event
    mock_event = create_bedrock_mock_event(action_group, api_path, parameters)
    
    print(f"\n📦 Evento Bedrock (mock):")
    print(json.dumps(mock_event, indent=2, ensure_ascii=False))
    
    # Contexto mock (vazio, apenas para compatibilidade)
    mock_context = {}
    
    print(f"\n⚡ Executando lambda_handler...")
    
    try:
        # Executa a função
        result = lambda_handler(mock_event, mock_context)
        
        print(f"\n✅ RESULTADO:")
        print(f"Status Code: {result.get('statusCode')}")
        print(f"Headers: {result.get('headers')}")
        
        # Parse do body JSON
        body = json.loads(result.get('body', '{}'))
        print(f"\nBody (parsed):")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Executa os testes locais."""
    print("🚀 Iniciando testes locais da Lambda Function")
    print(f"{'='*60}")
    
    # Teste 1: Buscar por data específica
    run_test(
        description="Buscar dados por data (2024-03-01)",
        action_group="GarminQueryGroup",
        api_path="/query-by-date",
        parameters=[
            {"name": "timestamp", "type": "string", "value": "2024-03-01"},
            {"name": "data_type", "type": "string", "value": None}
        ]
    )
    
    # Teste 2: Buscar por tipo de dado
    run_test(
        description="Buscar dados por tipo (Sono)",
        action_group="GarminQueryGroup",
        api_path="/query-by-type",
        parameters=[
            {"name": "timestamp", "type": "string", "value": None},
            {"name": "data_type", "type": "string", "value": "Sono"}
        ]
    )
    
    # Teste 3: Buscar por data e tipo
    run_test(
        description="Buscar dados por data e tipo (2024-03-01 + Sono)",
        action_group="GarminQueryGroup",
        api_path="/query-by-date-and-type",
        parameters=[
            {"name": "timestamp", "type": "string", "value": "2024-03-01"},
            {"name": "data_type", "type": "string", "value": "Sono"}
        ]
    )
    
    # Teste 4: Buscar todos os dados (sem filtros)
    run_test(
        description="Buscar todos os dados (sem filtros)",
        action_group="GarminQueryGroup",
        api_path="/query-all",
        parameters=[]
    )
    
    print(f"\n{'='*60}")
    print("🏁 Testes finalizados")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
