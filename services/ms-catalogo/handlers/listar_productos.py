import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from utils import build_response, log_event

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    try:
        query_params = event.get("queryStringParameters") or {}
        tenant_id = query_params.get("tenant_id") or "popeyes"

        respuesta = tabla.query(
            KeyConditionExpression=Key("tenant_id").eq(tenant_id)
        )

        return build_response(200, {
            "items": respuesta.get("Items", []),
            "count": respuesta.get("Count", 0),
        })
    except Exception as e:
        log_event("ERROR", f"Error al listar productos: {str(e)}")
        return build_response(500, {"error": f"Error al listar productos: {str(e)}"})
