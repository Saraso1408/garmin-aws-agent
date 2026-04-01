#!/usr/bin/env python3
"""
Script para testar conexão com AWS Bedrock Runtime.
Envia uma pergunta simples para o modelo Claude 3.5 Haiku.
"""

import json
import boto3
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


# ID do modelo Claude 3.5 Haiku na AWS Bedrock
MODEL_ID = "us.amazon.nova-micro-v1:0"


def create_message_payload(prompt: str) -> dict:
    """Cria o payload no formato esperado pelo modelo Claude."""
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }


def test_bedrock_connection():
    """Testa a conexão com Bedrock enviando uma mensagem simples."""
    
    print("🚀 Testando conexão com AWS Bedrock Runtime")
    print(f"🤖 Modelo: {MODEL_ID}")
    print("-" * 60)
    
    try:
        # Cria cliente Bedrock Runtime
        print("📡 Criando cliente bedrock-runtime...")
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        print("✅ Cliente criado com sucesso")
        
        # Prepara a pergunta
        prompt = "Olá, você está ativo?"
        print(f"\n💬 Pergunta: '{prompt}'")
        
        # Cria o payload
        payload = create_message_payload(prompt)
        body = json.dumps(payload)
        
        print(f"📦 Enviando requisição...")
        
        # Invoca o modelo
        response = client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body
        )
        
        print("✅ Resposta recebida!")
        print("-" * 60)
        
        # Processa a resposta
        response_body = json.loads(response['body'].read())
        
        # Extrai o texto da resposta
        if 'content' in response_body and len(response_body['content']) > 0:
            assistant_response = response_body['content'][0]['text']
        elif 'completion' in response_body:
            assistant_response = response_body['completion']
        else:
            assistant_response = str(response_body)
        
        print("📝 Resposta do modelo:")
        print(f"\n{assistant_response}")
        
        # Informações adicionais
        print("\n" + "-" * 60)
        print(f"📊 Usage:")
        if 'usage' in response_body:
            usage = response_body['usage']
            print(f"   Input tokens:  {usage.get('input_tokens', 'N/A')}")
            print(f"   Output tokens: {usage.get('output_tokens', 'N/A')}")
        
        print(f"   Stop reason: {response_body.get('stop_reason', 'N/A')}")
        
        print("\n✅ Teste concluído com sucesso! Credenciais e acesso ao modelo funcionando.")
        
    except client.exceptions.AccessDeniedException as e:
        print(f"\n❌ Erro de acesso negado: {e}")
        print("   Verifique se você tem permissão para usar o modelo Bedrock.")
        
    except client.exceptions.ResourceNotFoundException as e:
        print(f"\n❌ Modelo não encontrado: {e}")
        print(f"   Verifique se o modelo '{MODEL_ID}' está disponível na sua região.")
        
    except client.exceptions.ValidationException as e:
        print(f"\n❌ Erro de validação: {e}")
        print("   Verifique o formato da requisição.")
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_bedrock_connection()
