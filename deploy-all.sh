#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
STAGE="dev"

if [ -f "$ROOT/.env" ]; then
    set -a; source "$ROOT/.env"; set +a
fi
if [ -z "$RAPPI_API_KEY" ]; then
    echo "ERROR: RAPPI_API_KEY no esta definida. Copia .env.example a .env en la raiz y genera un valor (openssl rand -hex 32)." >&2
    exit 1
fi

# Parse --stage argument
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --stage) STAGE="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

SERVICES=(ms-auth ms-catalogo ms-pedidos ms-workflow)

echo "============================================"
echo "  Desplegando todos los servicios (stage: $STAGE)"
echo "============================================"

for service in "${SERVICES[@]}"; do
  echo ""
  echo ">>> Desplegando $service..."
  cd "$ROOT/services/$service"
  serverless deploy --stage "$STAGE"
  echo "<<< $service desplegado correctamente"
done

echo ""
echo "============================================"
echo "  Todos los servicios desplegados en $STAGE"
echo "============================================"
