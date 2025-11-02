import json
import boto3
import urllib.parse
import os


endpoint_url = "http://host.docker.internal:4566"

# Criamos os "clientes" para S3 e DynamoDB
s3 = boto3.client('s3', endpoint_url=endpoint_url)
dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)

def lambda_handler(event, context):
    print("Evento recebido:", json.dumps(event))

    # 1. Obter o nome do bucket e o arquivo (objeto) do evento
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print(f"Processando arquivo {key} do bucket {bucket}...")

    try:
        # 2. Ler o arquivo JSON do S3
        response = s3.get_object(Bucket=bucket, Key=key)
        conteudo_json = response['Body'].read().decode('utf-8')
        notas_fiscais = json.loads(conteudo_json)
        print("Arquivo JSON lido com sucesso.") # Nova linha de log

        # 3. Pegar a nossa tabela no DynamoDB
        tabela = dynamodb.Table('NotasFiscais')
        print(f"Conectado à tabela {tabela.name}.") # Nova linha de log

        # 4. Iterar sobre os registros e salvar no DynamoDB
        # (Usando batch_writer para mais eficiência)
        with tabela.batch_writer() as batch:
            for nf in notas_fiscais:
                print(f"Salvando nota: {nf['id']}")
                batch.put_item(
                    Item={
                        'id': nf['id'],
                        'cliente': nf['cliente'],
                        'valor': str(nf['valor']), # Salvar como string
                        'data_emissao': nf['data_emissao']
                    }
                )

        print("Todos os dados foram salvos com sucesso!")
        return {
            'statusCode': 200,
            'body': json.dumps('Dados processados com sucesso!')
        }

    except Exception as e:
        # Imprimir o erro real se ele acontecer
        print(f"ERRO AO PROCESSAR O ARQUIVO: {e}") 
        raise e