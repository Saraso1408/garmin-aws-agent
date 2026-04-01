import json
import boto3
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('GARMIN_TABLE_NAME', 'GarminHealthStats')


class DecimalEncoder(json.JSONEncoder):
    """Encoder para converter Decimal em float/int ao serializar JSON."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 else int(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Lambda function para consultar dados no DynamoDB.
    Filtra por data (Timestamp) e/ou tipo de dado (DataType).
    
    Parâmetros via event:
    - timestamp: Data no formato 'YYYY-MM-DD' (opcional)
    - data_type: Tipo de dado, ex: 'Sono', 'Atividade' (opcional)
    """
    
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # Extrai parâmetros do event
        timestamp = event.get('timestamp')  # Filtro por data
        data_type = event.get('data_type')  # Filtro por tipo
        
        print(f"🔍 Query - Timestamp: {timestamp}, DataType: {data_type}")
        
        # Constrói a query
        if timestamp and data_type:
            # Query com ambos os filtros
            # Usa Timestamp como partition key e DataType como filter
            response = table.query(
                IndexName='TimestampIndex',  # Assumindo GSI em Timestamp
                KeyConditionExpression=Key('Timestamp').eq(timestamp),
                FilterExpression=Attr('DataType').eq(data_type)
            )
            
        elif timestamp:
            # Query apenas por data
            response = table.query(
                IndexName='TimestampIndex',
                KeyConditionExpression=Key('Timestamp').eq(timestamp)
            )
            
        elif data_type:
            # Scan com filtro por tipo (sem índice específico)
            response = table.scan(
                FilterExpression=Attr('DataType').eq(data_type)
            )
            
        else:
            # Scan completo (limitado para evitar timeout)
            response = table.scan(Limit=100)
        
        items = response.get('Items', [])
        
        # Paginação: continua se houver mais itens
        while 'LastEvaluatedKey' in response:
            if timestamp and data_type:
                response = table.query(
                    IndexName='TimestampIndex',
                    KeyConditionExpression=Key('Timestamp').eq(timestamp),
                    FilterExpression=Attr('DataType').eq(data_type),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
            elif timestamp:
                response = table.query(
                    IndexName='TimestampIndex',
                    KeyConditionExpression=Key('Timestamp').eq(timestamp),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
            elif data_type:
                response = table.scan(
                    FilterExpression=Attr('DataType').eq(data_type),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
            else:
                response = table.scan(
                    Limit=100,
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
            
            items.extend(response.get('Items', []))
        
        print(f"✅ {len(items)} registros encontrados")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'count': len(items),
                'filters': {
                    'timestamp': timestamp,
                    'data_type': data_type
                },
                'data': items
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }
