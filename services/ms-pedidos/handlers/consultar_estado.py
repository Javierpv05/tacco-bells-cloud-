import json
import os

import boto3
from boto3.dynamodb.conditions import Key
from utils import build_response, log_event

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])



def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}

        pedido_id = path_params.get("pedido_id")
        tenant_id = query_params.get("tenant_id", "popeyes")

        if not pedido_id:
            log_event("WARN", "El parametro pedido_id es obligatorio")
            return build_response(400, {"error": "El parámetro 'pedido_id' es obligatorio"})

        respuesta = tabla.get_item(
            Key={"tenant_id": tenant_id, "pedido_id": pedido_id}
        )

        pedido = respuesta.get("Item")

        if not pedido:
            log_event("INFO", "Pedido no encontrado", {"pedido_id": pedido_id})
            return build_response(404, {"error": f"Pedido '{pedido_id}' no encontrado para el tenant '{tenant_id}'"})

        return build_response(200, pedido)

    except Exception as e:
        log_event("ERROR", f"Error al consultar pedido: {str(e)}")
        return build_response(500, {"error": f"Error al consultar pedido: {str(e)}"})
