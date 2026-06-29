"""
obtener_usuario.py — GET /auth/usuario (protegido con Cognito Authorizer)

Cuando API Gateway valida el JWT, inyecta los claims en:
  event['requestContext']['authorizer']['claims']

Claims disponibles:
  - sub         → user_id único en Cognito
  - email       → email del usuario
  - name        → nombre
  - custom:tenant_id → tenant del usuario
"""
import os
import boto3
from utils import build_response, log_event, get_claims

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLA_USUARIOS"])


def handler(event, context):
    try:
        # ── Extraer identidad desde el JWT via API Gateway ────────────────
        claims = get_claims(event)
        if not claims:
            return build_response(401, {"error": "No autorizado. Token inválido o ausente."})

        user_id = claims.get("sub")
        tenant_id = claims.get("custom:tenant_id", "popeyes")

        if not user_id:
            return build_response(401, {"error": "Token inválido: falta el claim 'sub'"})

        # ── Consultar perfil en DynamoDB ──────────────────────────────────
        respuesta = tabla.get_item(Key={"tenant_id": tenant_id, "user_id": user_id})
        usuario = respuesta.get("Item")

        if not usuario:
            # El usuario está en Cognito pero no en DynamoDB (caso borde)
            log_event("WARN", "Usuario en Cognito pero no en DynamoDB", {"user_id": user_id})
            return build_response(
                200,
                {
                    "user_id": user_id,
                    "email": claims.get("email", ""),
                    "nombre": claims.get("name", ""),
                    "tenant_id": tenant_id,
                    "rol": "cliente",
                },
            )

        log_event("INFO", "Perfil obtenido", {"user_id": user_id})
        return build_response(200, {"usuario": usuario})

    except Exception as e:
        log_event("ERROR", f"Error al obtener usuario: {str(e)}")
        return build_response(500, {"error": f"Error al obtener usuario: {str(e)}"})
