import json
import decimal
import uuid
from datetime import datetime, timezone

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def convert_to_decimal(obj):
    if isinstance(obj, list):
        return [convert_to_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, (float, int)) and not isinstance(obj, bool):
        return decimal.Decimal(str(obj))
    else:
        return obj

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

def log_event(level, message, data=None):
    log_entry = {
        'level': level,
        'message': message
    }
    if data is not None:
        log_entry['data'] = data
    print(json.dumps(log_entry, cls=DecimalEncoder))


def crear_pedido_core(tabla, events_client, event_bus_name, body, origen):
    """
    Logica compartida entre el canal publico (web) y el canal externo
    (Rappi/OCI, protegido con API Key). 'origen' lo decide el handler segun
    la ruta invocada, nunca se confia en un valor enviado por el cliente.
    """
    tenant_id = body.get("tenant_id")
    cliente_nombre = body.get("cliente_nombre")
    items = body.get("items", [])
    total = body.get("total")

    if not tenant_id or not cliente_nombre or not items or total is None:
        raise ValueError("Los campos 'tenant_id', 'cliente_nombre', 'items' y 'total' son obligatorios")

    pedido_id = uuid.uuid4().hex
    fecha_creacion = datetime.now(timezone.utc).isoformat()
    estado = "RECIBIDO"

    pedido = {
        "tenant_id": tenant_id,
        "pedido_id": pedido_id,
        "cliente_nombre": cliente_nombre,
        "items": convert_to_decimal(items),
        "total": convert_to_decimal(total),
        "estado": estado,
        "fecha_creacion": fecha_creacion,
        "tenant_estado": f"{tenant_id}#{estado}",
        "origen": origen,
    }

    tabla.put_item(Item=pedido)

    events_client.put_events(
        Entries=[
            {
                "Source": "pedidos.app",
                "DetailType": "PedidoCreado",
                "Detail": json.dumps(pedido, cls=DecimalEncoder),
                "EventBusName": event_bus_name,
            }
        ]
    )

    log_event("INFO", "Pedido creado y evento publicado", {"pedido_id": pedido_id, "origen": origen})

    return {
        "mensaje": "Pedido creado exitosamente",
        "pedido_id": pedido_id,
        "estado": estado,
        "fecha_creacion": fecha_creacion,
    }
