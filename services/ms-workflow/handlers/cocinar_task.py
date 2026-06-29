"""
cocinar_task.py — Invocada por Step Functions (waitForTaskToken).

Step Functions llama a esta Lambda con:
  {
    "paso": "COCINA",
    "pedido": { ...datos del pedido... },
    "taskToken": "<token>"
  }

La Lambda guarda el token en DynamoDB, actualiza el estado en pedidos y pausa el flujo.
"""
import os
import uuid
from datetime import datetime, timezone
import boto3

dynamodb = boto3.resource("dynamodb")
tabla_pasos = dynamodb.Table(os.environ["TABLA_PASOS"])
tabla_pedidos = dynamodb.Table(os.environ["TABLA_PEDIDOS"])

PASO = "COCINA"
ESTADO_PEDIDO = "EN_COCINA"

def handler(event, context):
    try:
        pedido = event.get("pedido", event)
        task_token = event.get("taskToken")

        tenant_id = pedido.get("tenant_id", "popeyes")
        pedido_id = pedido.get("pedido_id", "desconocido")

        # 1. Registrar el paso pendiente
        paso_item = {
            "tenant_id": tenant_id,
            "paso_id": f"{pedido_id}#{PASO}",
            "pedido_id": pedido_id,
            "paso": PASO,
            "estado": "PENDIENTE",
            "task_token": task_token,
            "fecha_inicio": datetime.now(timezone.utc).isoformat(),
        }
        tabla_pasos.put_item(Item=paso_item)

        # 2. Actualizar el estado del pedido en la tabla principal
        tabla_pedidos.update_item(
            Key={"tenant_id": tenant_id, "pedido_id": pedido_id},
            UpdateExpression="SET tenant_estado = :te, estado_actual = :e, actualizado_en = :t",
            ExpressionAttributeValues={
                ":te": f"{tenant_id}#{ESTADO_PEDIDO}",
                ":e": ESTADO_PEDIDO,
                ":t": datetime.now(timezone.utc).isoformat(),
            }
        )

        return {
            "statusCode": 200,
            "mensaje": f"Paso {PASO} registrado. Esperando confirmación del operador.",
            "tenant_id": tenant_id,
            "pedido_id": pedido_id,
            "paso": PASO,
        }

    except Exception as e:
        raise RuntimeError(f"Error en tarea {PASO}: {str(e)}")
