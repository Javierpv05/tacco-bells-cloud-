import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}

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

        try:
            tabla.delete_item(
                Key={"tenant_id": tenant_id, "producto_id": producto_id},
                ConditionExpression="attribute_exists(tenant_id) AND attribute_exists(producto_id)",
            )
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": "Producto no encontrado"}),
            }

        return {
            "statusCode": 204,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": "",
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": f"Error al eliminar producto: {str(e)}"}
            ),
        }
