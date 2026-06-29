"""
entregar_task.py — Invocada por Step Functions al finalizar el flujo. No espera token.
"""
import os
from datetime import datetime, timezone
import boto3

dynamodb = boto3.resource("dynamodb")
tabla_pedidos = dynamodb.Table(os.environ["TABLA_PEDIDOS"])

PASO = "ENTREGADO"
ESTADO_PEDIDO = "ENTREGADO"

def handler(event, context):
    try:
        pedido = event.get("pedido", event)
        tenant_id = pedido.get("tenant_id", "popeyes")
        pedido_id = pedido.get("pedido_id", "desconocido")

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
            "mensaje": f"Pedido {pedido_id} marcado como {ESTADO_PEDIDO}.",
            "tenant_id": tenant_id,
            "pedido_id": pedido_id,
            "paso": PASO,
        }

    except Exception as e:
        raise RuntimeError(f"Error en tarea {PASO}: {str(e)}")
