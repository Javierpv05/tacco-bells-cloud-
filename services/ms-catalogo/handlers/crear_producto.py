import json
import os
import uuid
import boto3

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        tenant_id = body.get("tenant_id") or "taco-bell"
        nombre = body.get("nombre")
        precio = body.get("precio")

        if not nombre or precio is None:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {"error": "Los campos 'nombre' y 'precio' son obligatorios"}
                ),
            }

        producto = {
            "tenant_id": tenant_id,
            "producto_id": uuid.uuid4().hex,
            "nombre": nombre,
            "precio": precio,
            "descripcion": body.get("descripcion", ""),
            "disponible": bool(body.get("disponible", True)),
        }

        tabla.put_item(Item=producto)

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"mensaje": "Producto creado", "producto": producto}
            ),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": f"Error al crear producto: {str(e)}"}),
        }
