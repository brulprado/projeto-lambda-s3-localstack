# projeto-lambda-s3-localstack
Executando tarefas automatizadas com Lambda Function e S3

**Autora:** Bruna Lima Prado

# Executando Tarefas Automatizadas com AWS Lambda e S3 (via LocalStack)

Este projeto demonstra um pipeline de processamento de dados serverless simulado 100% localmente. O objetivo é automatizar o processamento de arquivos JSON (contendo notas fiscais) enviados para um bucket S3. Um evento de upload aciona uma função Lambda, que lê o arquivo e armazena os dados em uma tabela DynamoDB.

Todo o ambiente AWS (S3, Lambda, DynamoDB) é simulado utilizando **LocalStack** e gerenciado via **AWS CLI**, permitindo o desenvolvimento e teste de infraestrutura sem custos e com um ciclo de feedback rápido, essencial para práticas de DevOps.

## 🏛️ Arquitetura do Pipeline

O fluxo de dados segue a seguinte arquitetura:

`[Upload: notas_fiscais.json] -> [S3 Bucket: 'notas-fiscais-upload'] -> [S3 Event Trigger (s3:ObjectCreated:*)] -> [Lambda Function: 'ProcessarNotasFiscais'] -> [DynamoDB Table: 'NotasFiscais']`

*`!Arquitetura do Projeto: (arquitetura.png)`*

## 🛠️ Tecnologias Utilizadas

* **Simulação de Cloud:** LocalStack
* **Gerenciamento de Infra:** AWS CLI v2
* **Containerização:** Docker Desktop
* **Linguagem da Lambda:** Python 3.9
* **Serviços AWS Simulados:**
    * **AWS S3:** Para armazenamento de objetos (arquivos `.json`).
    * **AWS Lambda:** Para execução de código serverless (processamento do arquivo).
    * **AWS DynamoDB:** Para armazenamento de dados NoSQL (persistência das notas).
    * **AWS IAM/STS:** Para as permissões (simuladas com ARNs padrão).
    * **AWS CloudWatch Logs:** Para depuração da função Lambda (via `aws logs tail`).

## 📋 Pré-requisitos

Antes de começar, garanta que você possui as seguintes ferramentas instaladas e **em execução**:

1.  **Docker Desktop:** Essencial para o LocalStack rodar os contêineres dos serviços AWS.
2.  **Python 3.9+** (e `pip`): Necessário para os scripts e a instalação das CLIs.
3.  **LocalStack:** (`pip install localstack`)
4.  **AWS CLI v2:** (`pip install awscli`)

## ⚙️ Configuração Inicial

1.  **Configure o AWS CLI:**
    Configure o AWS CLI com credenciais de teste. O LocalStack não as valida, mas elas são necessárias.

    ```bash
    aws configure
    ```
    * `AWS Access Key ID`: **test**
    * `AWS Secret Access Key`: **test**
    * `Default region name`: **us-east-1**
    * `Default output format`: **json**

2.  **Inicie o LocalStack:**
    Certifique-se de que o Docker Desktop está rodando e execute:

    ```bash
    localstack start -d
    ```

## 🚀 Como Executar o Projeto

Todos os comandos devem ser executados a partir da raiz deste repositório.

### 1. Criar os Recursos de Infraestrutura

Primeiro, criamos o bucket S3 e a tabela DynamoDB.

```bash
# Criar o bucket S3
aws s3api create-bucket --bucket notas-fiscais-upload --endpoint-url=http://localhost:4566

# Criar a tabela DynamoDB
aws dynamodb create-table --endpoint-url=http://localhost:4566 \
    --table-name NotasFiscais \
    --attribute-definitions AttributeName=id,AttributeType=S \
    --key-schema AttributeName=id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
2. Preparar e Criar a Função Lambda
O código da Lambda (grava_db.py) está configurado para usar http://host.docker.internal:4566 como endpoint-url. Isso permite que o contêiner da Lambda "enxergue" o serviço LocalStack rodando na máquina host.

Bash

# 1. Compactar o código da Lambda em um arquivo .zip
# (No PowerShell)
Compress-Archive -Path grava_db.py -DestinationPath lambda_function.zip

# (No Linux/macOS)
# zip lambda_function.zip grava_db.py

# 2. Criar a função Lambda
aws lambda create-function \
 --function-name ProcessarNotasFiscais \
 --runtime python3.9 \
 --role arn:aws:iam::000000000000:role/lambda-role \
 --handler grava_db.lambda_handler \
 --zip-file fileb://lambda_function.zip \
 --endpoint-url=http://localhost:4566
3. Configurar os Gatilhos (Triggers)
Conectamos o S3 à Lambda para que o upload de arquivos dispare a automação.

Bash

# 1. Dar permissão ao S3 para invocar a Lambda
aws lambda add-permission \
 --function-name ProcessarNotasFiscais \
 --statement-id s3-trigger \
 --action "lambda:InvokeFunction" \
 --principal s3.amazonaws.com \
 --source-arn arn:aws:s3:::notas-fiscais-upload \
 --endpoint-url=http://localhost:4566

# 2. Configurar o evento de notificação no bucket S3
# (Utiliza o arquivo notification.json deste repositório)
aws s3api put-bucket-notification-configuration \
 --bucket notas-fiscais-upload \
 --notification-configuration file://notification.json \
 --endpoint-url=http://localhost:4566
✅ Testando a Automação
Com tudo configurado, podemos testar o pipeline.

1. Gerar Dados de Teste (Opcional) Este comando executa o script gerar_dados.py para criar o arquivo notas_fiscais.json.

Bash

python gerar_dados.py
2. Fazer o Upload para o S3 (O Gatilho) Este comando envia o arquivo para o S3, o que deve disparar a Lambda.

Bash

aws s3 cp notas_fiscais.json s3://notas-fiscais-upload/notas_fiscais.json --endpoint-url=http://localhost:4566
3. Verificar o Resultado no DynamoDB Se tudo funcionou, os dados do arquivo JSON devem aparecer na tabela DynamoDB.

Bash

aws dynamodb scan --table-name NotasFiscais --endpoint-url=http://localhost:4566
Resultado Esperado:

JSON

{
    "Items": [
        {
            "valor": {
                "S": "500.75"
            },
            "cliente": {
                "S": "Maria Oliveira"
            },
            "id": {
                "S": "NF-2"
            },
            "data_emissao": {
                "S": "2025-10-15"
            }
        },
        {
            "valor": {
                "S": "1234.56"
            },
            "cliente": {
                "S": "João Silva"
            },
            "id": {
                "S": "NF-1"
            },
            "data_emissao": {
                "S": "2025-10-20"
            }
        }
        // ... (etc.)
    ],
    "Count": 3,
    "ScannedCount": 3,
    "ConsumedCapacity": null
}

🐛 **Depuração (Debugging)**
Se o dynamodb scan retornar uma lista vazia, a Lambda provavelmente falhou. Para ver os logs da Lambda em tempo real, abra um segundo terminal e execute:

Bash

aws logs tail /aws/lambda/ProcessarNotasFiscais --follow --endpoint-url=http://localhost:4566
Em seguida, execute o comando de upload (aws s3 cp...) no primeiro terminal e observe os logs no segundo.

🧹 Limpando o Ambiente
Para parar e remover os serviços, execute:

Bash

# Para os serviços da AWS (S3, DynamoDB, etc.)
aws s3 rb s3://notas-fiscais-upload --endpoint-url=http://localhost:4566 --force
aws dynamodb delete-table --table-name NotasFiscais --endpoint-url=http://localhost:4566
aws lambda delete-function --function-name ProcessarNotasFiscais --endpoint-url=http://localhost:4566

# Para o LocalStack
localstack stop
