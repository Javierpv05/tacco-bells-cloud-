import json
import os
import uuid
import boto3
from utils import convert_to_decimal, build_response, log_event

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        tenant_id = body.get("tenant_id") or "popeyes"
        nombre = body.get("nombre")
        precio = body.get("precio")

        if not nombre or precio is None:
            log_event("WARN", "Campos obligatorios faltantes", {"body": body})
            return build_response(400, {"error": "Los campos 'nombre' y 'precio' son obligatorios"})

        producto = {
            "tenant_id": tenant_id,
            "producto_id": uuid.uuid4().hex,
            "nombre": nombre,
            "precio": convert_to_decimal(precio),
            "descripcion": body.get("descripcion", ""),
            "disponible": bool(body.get("disponible", True)),
        }

        tabla.put_item(Item=producto)
        log_event("INFO", "Producto creado exitosamente", {"producto_id": producto["producto_id"]})

        return build_response(201, {"mensaje": "Producto creado", "producto": producto})
    except Exception as e:
        log_event("ERROR", f"Error al crear producto: {str(e)}")
        return build_response(500, {"error": f"Error al crear producto: {str(e)}"})
