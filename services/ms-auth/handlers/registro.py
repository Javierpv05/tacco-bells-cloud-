"""
registro.py — POST /auth/registro (público, sin authorizer)

Body esperado:
{
    "email":    "usuario@ejemplo.com",
    "password": "Pass1234",
    "nombre":   "Juan Pérez",
    "telefono": "987654321",    (opcional)
    "rol":      "cliente" | "trabajador",
    "tenant_id": "popeyes"  (opcional, default popeyes)
}

Flujo:
  1. Registra el usuario en Cognito (sign_up).
  2. Guarda el perfil en DynamoDB (tabla usuarios).
  3. Retorna 201 con el user_id (sub de Cognito).
"""
import json
import os
import boto3
from botocore.exceptions import ClientError
from utils import build_response, log_event

cognito = boto3.client("cognito-idp")
dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLA_USUARIOS"])

APP_CLIENT_ID = os.environ["APP_CLIENT_ID"]
TENANT_DEFAULT = "popeyes"
ROLES_VALIDOS = {"cliente", "trabajador"}


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        email = body.get("email", "").strip().lower()
        password = body.get("password", "")
        nombre = body.get("nombre", "").strip()
        telefono = body.get("telefono", "")
        rol = body.get("rol", "cliente").lower()
        tenant_id = body.get("tenant_id", TENANT_DEFAULT)

        # ── Validaciones básicas ──────────────────────────────────────────
        if not email or not password or not nombre:
            log_event("WARN", "Campos obligatorios faltantes", {"body": body})
            return build_response(
                400,
                {"error": "Los campos 'email', 'password' y 'nombre' son obligatorios"},
            )

        if rol not in ROLES_VALIDOS:
            return build_response(
                400,
                {"error": f"Rol inválido '{rol}'. Válidos: {', '.join(sorted(ROLES_VALIDOS))}"},
            )

        # ── Registro en Cognito ───────────────────────────────────────────
        try:
            resp_cognito = cognito.sign_up(
                ClientId=APP_CLIENT_ID,
                Username=email,
                Password=password,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "name", "Value": nombre},
                    {"Name": "custom:tenant_id", "Value": tenant_id},
                ],
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "UsernameExistsException":
                return build_response(409, {"error": "El email ya está registrado"})
            if code == "InvalidPasswordException":
                return build_response(
                    400,
                    {"error": "Contraseña inválida. Mínimo 8 caracteres, al menos 1 número y 1 letra minúscula"},
                )
            log_event("ERROR", f"Error Cognito sign_up: {str(e)}")
            return build_response(500, {"error": f"Error al registrar usuario: {str(e)}"})

        user_id = resp_cognito["UserSub"]  # sub de Cognito

        # ── Guardar perfil en DynamoDB ────────────────────────────────────
        item = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "email": email,
            "nombre": nombre,
            "rol": rol,
            "telefono": telefono,
            "confirmado": False,
        }
        tabla.put_item(Item=item)

        log_event("INFO", "Usuario registrado", {"user_id": user_id, "email": email, "rol": rol})

        return build_response(
            201,
            {
                "mensaje": "Usuario registrado exitosamente. Revisa tu email para confirmar la cuenta.",
                "user_id": user_id,
                "email": email,
                "rol": rol,
                "tenant_id": tenant_id,
            },
        )

    except Exception as e:
        log_event("ERROR", f"Error inesperado en registro: {str(e)}")
        return build_response(500, {"error": f"Error inesperado: {str(e)}"})
