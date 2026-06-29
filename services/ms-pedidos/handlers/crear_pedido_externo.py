import json
import os

import boto3
from utils import build_response, log_event, crear_pedido_core

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])

events_client = boto3.client("events")
EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]


def handler(event, context):
    """
    POST /pedidos/externos — canal para integraciones externas (Rappi/OCI).
    Protegido con API Key de API Gateway (header x-api-key). origen='rappi'
    siempre se fuerza aqui, nunca se toma del body del cliente.
    """
    body = {}
    try:
        body = json.loads(event.get("body") or "{}")
        resultado = crear_pedido_core(tabla, events_client, EVENT_BUS_NAME, body, origen="rappi")
        return build_response(201, resultado)
    except ValueError as e:
        log_event("WARN", str(e), {"body": body})
        return build_response(400, {"error": str(e)})
    except Exception as e:
        log_event("ERROR", f"Error al crear pedido externo: {str(e)}")
        return build_response(500, {"error": f"Error al crear pedido externo: {str(e)}"})
