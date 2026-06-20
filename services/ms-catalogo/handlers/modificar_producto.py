import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])

CAMPOS_PERMITIDOS = ["nombre", "precio", "descripcion", "disponible"]


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}
        body = json.loads(event.get("body") or "{}")

        tenant_id = (query_params or {}).get("tenant_id") or "taco-bell"
        producto_id = path_params.get("producto_id")

        if not producto_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {
                        "error": "El parametro 'producto_id' es obligatorio en la ruta"
                    }
                ),
            }

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
                attr_values[f":{campo}"] = val

        if not update_parts:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {"error": "No se enviaron campos válidos para actualizar"}
                ),
            }

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
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {"error": "Producto no encontrado para actualizar"}
                ),
            }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"producto": respuesta["Attributes"]}),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": f"Error al modificar producto: {str(e)}"}
            ),
        }
