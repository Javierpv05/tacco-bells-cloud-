import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    try:
        query_params = event.get("queryStringParameters") or {}
        tenant_id = query_params.get("tenant_id") or "taco-bell"

        respuesta = tabla.query(
            KeyConditionExpression=Key("tenant_id").eq(tenant_id)
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "items": respuesta.get("Items", []),
                    "count": respuesta.get("Count", 0),
                }
            ),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": f"Error al listar productos: {str(e)}"}
            ),
        }
