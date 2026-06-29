"""
actualizar_usuario.py — PUT /auth/usuario (protegido con Cognito Authorizer)

Body esperado (todos opcionales):
{
    "nombre":   "Nuevo Nombre",
    "telefono": "999888777"
}
"""
import json
import os
import boto3
from utils import build_response, log_event, get_claims

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLA_USUARIOS"])

CAMPOS_ACTUALIZABLES = ["nombre", "telefono"]


def handler(event, context):
    try:
        claims = get_claims(event)
        if not claims:
            return build_response(401, {"error": "No autorizado. Token inválido o ausente."})

        user_id = claims.get("sub")
        tenant_id = claims.get("custom:tenant_id", "popeyes")

        if not user_id:
            return build_response(401, {"error": "Token inválido: falta el claim 'sub'"})

        body = json.loads(event.get("body") or "{}")

        update_parts = []
        attr_names = {}
        attr_values = {}

        for campo in CAMPOS_ACTUALIZABLES:
            if campo in body:
                update_parts.append(f"#{campo} = :{campo}")
                attr_names[f"#{campo}"] = campo
                attr_values[f":{campo}"] = str(body[campo]).strip()

        if not update_parts:
            return build_response(
                400,
                {"error": f"No se enviaron campos válidos. Actualizables: {', '.join(CAMPOS_ACTUALIZABLES)}"},
            )

        existing = tabla.get_item(Key={"tenant_id": tenant_id, "user_id": user_id})
        if not existing.get("Item"):
            return build_response(404, {"error": "Usuario no encontrado"})

        respuesta = tabla.update_item(
            Key={"tenant_id": tenant_id, "user_id": user_id},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values,
            ReturnValues="ALL_NEW",
        )

        log_event("INFO", "Perfil actualizado", {"user_id": user_id})
        return build_response(200, {"usuario": respuesta["Attributes"]})

    except Exception as e:
        log_event("ERROR", f"Error al actualizar usuario: {str(e)}")
        return build_response(500, {"error": f"Error al actualizar usuario: {str(e)}"})
