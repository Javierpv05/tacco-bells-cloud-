import json
import os
import boto3
from utils import build_response, log_event

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}

        producto_id = path_params.get("producto_id")
        tenant_id = (query_params or {}).get("tenant_id") or "popeyes"

        if not producto_id:
            log_event("WARN", "Falta producto_id en la ruta")
            return build_response(400, {"error": "El parametro 'producto_id' es obligatorio en la ruta"})

        respuesta = tabla.get_item(
            Key={"tenant_id": tenant_id, "producto_id": producto_id}
        )

        item = respuesta.get("Item")
        if not item:
            log_event("INFO", "Producto no encontrado", {"producto_id": producto_id})
            return build_response(404, {"error": "Producto no encontrado"})

        return build_response(200, {"producto": item})
    except Exception as e:
        log_event("ERROR", f"Error al buscar producto: {str(e)}")
        return build_response(500, {"error": f"Error al buscar producto: {str(e)}"})
