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

        estado = path_params.get("estado")
        tenant_id = query_params.get("tenant_id", "popeyes")

        if not estado:
            log_event("WARN", "El parametro estado es obligatorio")
            return build_response(400, {"error": "El parámetro 'estado' es obligatorio"})

        # Clave compuesta para el GSI PorEstado
        tenant_estado = f"{tenant_id}#{estado.upper()}"

        respuesta = tabla.query(
            IndexName="PorEstado",
            KeyConditionExpression=Key("tenant_estado").eq(tenant_estado),
        )

        pedidos = respuesta.get("Items", [])

        return build_response(200, {
            "tenant_id": tenant_id,
            "estado": estado.upper(),
            "total": len(pedidos),
            "pedidos": pedidos,
        })

    except Exception as e:
        log_event("ERROR", f"Error al listar pedidos por estado: {str(e)}")
        return build_response(500, {"error": f"Error al listar pedidos por estado: {str(e)}"})
