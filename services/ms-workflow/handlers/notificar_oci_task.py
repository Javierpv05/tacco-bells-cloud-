"""
notificar_oci_task.py — Invocada por Step Functions (Task simple, sin token).

Solo se llega aqui cuando el Choice State "EsRappi_*" de la maquina de
estados determino que el pedido se origino en Rappi/OCI. Notifica el
cambio de estado al endpoint /estado de OCI. Si OCI no responde, el error
se captura (Catch en la ASL) y el flujo real del pedido continua: una
caida del simulador de Rappi no debe bloquear la cocina/despacho/reparto.
"""
import json
import os
import urllib.request
import urllib.error

OCI_URL = os.environ.get("OCI_URL")


def handler(event, context):
    pedido_id = event.get("pedido_id", "desconocido")
    estado = event.get("estado", "DESCONOCIDO")

    if not OCI_URL:
        return {"status": "skipped", "motivo": "OCI_URL no configurada", "pedido_id": pedido_id}

    payload = json.dumps({"pedido_id": pedido_id, "estado": estado}).encode("utf-8")
    request = urllib.request.Request(
        OCI_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as resp:
            return {"status": "ok", "http_status": resp.status, "pedido_id": pedido_id, "estado": estado}
    except urllib.error.URLError as e:
        raise RuntimeError(f"Error al notificar a OCI para el pedido {pedido_id}: {str(e)}")
