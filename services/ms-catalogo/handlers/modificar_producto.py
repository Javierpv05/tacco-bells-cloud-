import json
import os
import boto3
from utils import convert_to_decimal, build_response, log_event

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])

CAMPOS_PERMITIDOS = ["nombre", "precio", "descripcion", "disponible"]


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}
        body = json.loads(event.get("body") or "{}")

        tenant_id = (query_params or {}).get("tenant_id") or "popeyes"
        producto_id = path_params.get("producto_id")

        if not producto_id:
            log_event("WARN", "Falta producto_id en la ruta")
            return build_response(400, {"error": "El parametro 'producto_id' es obligatorio en la ruta"})

        update_parts = []
        attr_names = {}
        attr_values = {}

        for campo in CAMPOS_PERMITIDOS:
            if campo in body:
                update_parts.append(f"#{campo} = :{campo}")
                attr_names[f"#{campo}"] = campo

                val = body[campo]
                if campo == "disponible":
                    val = bool(val)
                elif campo == "precio":
                    val = convert_to_decimal(val)
                attr_values[f":{campo}"] = val

        if not update_parts:
            log_event("WARN", "No se enviaron campos validos", {"body": body})
            return build_response(400, {"error": "No se enviaron campos válidos para actualizar"})

        try:
            respuesta = tabla.update_item(
                Key={"tenant_id": tenant_id, "producto_id": producto_id},
                UpdateExpression="SET " + ", ".join(update_parts),
                ExpressionAttributeNames=attr_names,
                ExpressionAttributeValues=attr_values,
                ConditionExpression="attribute_exists(tenant_id) AND attribute_exists(producto_id)",
                ReturnValues="ALL_NEW",
            )
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            log_event("INFO", "Producto no encontrado para actualizar", {"producto_id": producto_id})
            return build_response(404, {"error": "Producto no encontrado para actualizar"})

        return build_response(200, {"producto": respuesta["Attributes"]})
    except Exception as e:
        log_event("ERROR", f"Error al modificar producto: {str(e)}")
        return build_response(500, {"error": f"Error al modificar producto: {str(e)}"})
