"""
avanzar_paso.py — Endpoint público: POST /pasos/avanzar

El operador o frontend llama a este endpoint cuando completa un paso.
El handler:
  1. Valida el body.
  2. Busca en DynamoDB el paso PENDIENTE del pedido para obtener el task_token.
  3. Llama a send_task_success para reanudar la Step Function.
  4. Actualiza el estado del paso en DynamoDB a COMPLETADO.

Body esperado:
{
    "tenant_id": "popeyes",
    "pedido_id": "abc123",
    "paso": "COCINA" | "DESPACHO" | "REPARTO",
    "usuario": "chef-juan",
    "observacion": "Listo en 10 min"   (opcional)
}
"""
import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key, Attr
from utils import build_response, log_event

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLA_PASOS"])
sfn_client = boto3.client("stepfunctions")

PASOS_VALIDOS = {"COCINA", "DESPACHO", "REPARTO"}


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")

        tenant_id = body.get("tenant_id", "popeyes")
        pedido_id = body.get("pedido_id")
        paso = (body.get("paso") or "").upper()
        usuario = body.get("usuario", "operador")
        observacion = body.get("observacion", "")

        # ── Validaciones ──────────────────────────────────────────────────
        if not pedido_id:
            log_event("WARN", "El campo pedido_id es obligatorio")
            return build_response(400, {"error": "El campo 'pedido_id' es obligatorio"})

        if paso not in PASOS_VALIDOS:
            log_event("WARN", f"Paso invalido: {paso}")
            return build_response(400, {"error": f"Paso inválido '{paso}'. Válidos: {', '.join(sorted(PASOS_VALIDOS))}"})

        # ── Buscar el task_token del paso PENDIENTE en DynamoDB ───────────
        paso_id = f"{pedido_id}#{paso}"
        respuesta = tabla.get_item(
            Key={"tenant_id": tenant_id, "paso_id": paso_id}
        )

        paso_pendiente = respuesta.get("Item")

        if not paso_pendiente or paso_pendiente.get("estado") != "PENDIENTE":
            log_event("WARN", f"No se encontro un paso {paso} pendiente para {pedido_id}")
            return build_response(404, {"error": f"No se encontró un paso '{paso}' PENDIENTE para el pedido '{pedido_id}'"})

        task_token = paso_pendiente.get("task_token")

        if not task_token:
            log_event("ERROR", "El paso pendiente no tiene task_token")
            return build_response(500, {"error": "El paso pendiente no tiene task_token registrado"})

        fecha_fin = datetime.now(timezone.utc).isoformat()

        # ── Actualizar estado del paso a COMPLETADO en DynamoDB ───────────
        tabla.update_item(
            Key={"tenant_id": tenant_id, "paso_id": paso_id},
            UpdateExpression=(
                "SET #estado = :completado, usuario = :usuario, "
                "observacion = :obs, fecha_fin = :fecha_fin"
            ),
            ExpressionAttributeNames={"#estado": "estado"},
            ExpressionAttributeValues={
                ":completado": "COMPLETADO",
                ":usuario": usuario,
                ":obs": observacion,
                ":fecha_fin": fecha_fin,
            },
        )

        # ── Actualizar estado del pedido ──────────────────────────────────
        nuevo_estado = ""
        if paso == "COCINA":
            nuevo_estado = "EN_DESPACHO"
        elif paso == "DESPACHO":
            nuevo_estado = "EN_REPARTO"
        elif paso == "REPARTO":
            nuevo_estado = "ENTREGADO"

        if nuevo_estado:
            tabla_pedidos = dynamodb.Table(os.environ["TABLA_PEDIDOS"])
            tabla_pedidos.update_item(
                Key={"tenant_id": tenant_id, "pedido_id": pedido_id},
                UpdateExpression="SET tenant_estado = :te, estado_actual = :e, actualizado_en = :t",
                ExpressionAttributeValues={
                    ":te": f"{tenant_id}#{nuevo_estado}",
                    ":e": nuevo_estado,
                    ":t": fecha_fin,
                }
            )

        # ── Notificar a Step Functions para reanudar el flujo ─────────────
        output = json.dumps(
            {
                "paso": paso,
                "pedido_id": pedido_id,
                "tenant_id": tenant_id,
                "usuario": usuario,
                "observacion": observacion,
                "completado_en": fecha_fin,
            }
        )

        sfn_client.send_task_success(taskToken=task_token, output=output)

        # La notificacion a OCI/Rappi ya no se hace aqui: la maquina de
        # estados la modela como Choice ("EsRappi_*") + Task tras cada paso,
        # asi solo se notifica cuando el pedido realmente vino de Rappi.

        log_event("INFO", f"Paso {paso} completado", {"pedido_id": pedido_id})
        return build_response(200, {
            "mensaje": f"Paso '{paso}' completado. Workflow avanzado.",
            "pedido_id": pedido_id,
            "tenant_id": tenant_id,
            "paso": paso,
            "usuario": usuario,
            "completado_en": fecha_fin,
        })

    except sfn_client.exceptions.TaskDoesNotExist:
        log_event("ERROR", "Task token does not exist")
        return build_response(404, {"error": "El task_token no corresponde a ninguna tarea activa en Step Functions"})

    except sfn_client.exceptions.TaskTimedOut:
        log_event("ERROR", "Task token timed out")
        return build_response(410, {"error": "El task_token ha expirado. La tarea ya no está activa"})

    except Exception as e:
        log_event("ERROR", f"Error al avanzar paso: {str(e)}")
        return build_response(500, {"error": f"Error al avanzar el paso: {str(e)}"})
