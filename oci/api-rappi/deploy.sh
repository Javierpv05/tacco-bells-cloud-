#!/bin/bash
set -e

echo "=========================================================="
echo "Desplegando API Rappi en OCI (contexto ya configurado)..."
echo "=========================================================="

# DATOS FIJOS
COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaad6gx6xntyy5hdei7piyhurlkq2zh3dxluixrcgoeltluek5yjuga"
REGION="us-chicago-1"
SUBNET_ID="ocid1.subnet.oc1.us-chicago-1.aaaaaaaat2lnw7oa4v45emqnxbdmcjtgr52jklq6ebg5df6qyqkfjgx3yafa"
APP_NAME="rappi-app"
FN_NAME="guardar-estado"
GW_NAME="api-rappi"
DEPLOYMENT_NAME="rappi-deployment"
PATH_PREFIX="/rappi"
AWS_URL="https://xoogztranc.execute-api.us-east-1.amazonaws.com/dev/pedidos/externos"

ROOT_ENV="$(cd "$(dirname "$0")/../.." && pwd)/.env"
if [ -f "$ROOT_ENV" ]; then
    set -a; source "$ROOT_ENV"; set +a
fi
if [ -z "$RAPPI_API_KEY" ]; then
    echo "ERROR: RAPPI_API_KEY no esta definida. Copia .env.example a .env en la raiz del repo y genera un valor (openssl rand -hex 32). Debe ser EL MISMO valor usado en services/ms-pedidos." >&2
    exit 1
fi

echo "Configuración:"
echo "- Compartment: $COMPARTMENT_ID"
echo "- Subnet: $SUBNET_ID"
echo "- Región: $REGION"

# 1. Verificar/Crear App
echo ""
echo "[1/4] Verificando/Creando Fn App '$APP_NAME'..."
APP_EXISTS=$(fn list apps | grep -w "$APP_NAME" || true)
if [ -z "$APP_EXISTS" ]; then
    echo "  -> Creando App..."
    fn create app "$APP_NAME" --annotation oracle.com/oci/subnetIds="[\"$SUBNET_ID\"]"
else
    echo "  -> App ya existe."
fi

# Obtener App ID
APP_ID=$(oci fn app list -c "$COMPARTMENT_ID" --name "$APP_NAME" --query 'data[0].id' --raw-output)

# 2. Desplegar función
echo ""
echo "[2/4] Desplegando función '$FN_NAME'..."
cd "$(dirname "$0")/function"
fn deploy --app "$APP_NAME"
cd ..

FUNC_OCID=$(oci fn function list --app-id "$APP_ID" --name "$FN_NAME" --query 'data[0].id' --raw-output)
echo "  -> Función OCID: $FUNC_OCID"

# 3. Crear API Gateway
echo ""
echo "[3/4] Creando API Gateway '$GW_NAME'..."
GW_ID=$(oci api-gateway gateway list -c "$COMPARTMENT_ID" --display-name "$GW_NAME" --lifecycle-state ACTIVE --query 'data.items[0].id' --raw-output 2>/dev/null || echo "")
if [ -z "$GW_ID" ] || [ "$GW_ID" == "None" ]; then
    echo "  -> Creando Gateway..."
    GW_ID=$(oci api-gateway gateway create -c "$COMPARTMENT_ID" --endpoint-type PUBLIC --subnet-id "$SUBNET_ID" --display-name "$GW_NAME" --query 'data.id' --raw-output)
    echo "  -> Esperando a que el Gateway esté ACTIVE..."
    oci api-gateway gateway get --gateway-id "$GW_ID" --wait-for-state ACTIVE > /dev/null
else
    echo "  -> Gateway ya existe ($GW_ID)."
fi

# 4. Crear Deployment
echo ""
echo "[4/4] Configurando deployment..."
cat <<EOF > deployment-spec.json
{
  "routes": [
    {
      "path": "/pedidos",
      "methods": ["POST"],
      "backend": {
        "type": "HTTP_BACKEND",
        "url": "$AWS_URL"
      },
      "requestPolicies": {
        "headerTransformations": {
          "setHeaders": {
            "items": [
              {
                "name": "x-api-key",
                "values": ["$RAPPI_API_KEY"],
                "ifExists": "OVERWRITE"
              }
            ]
          }
        }
      }
    },
    {
      "path": "/estado",
      "methods": ["POST"],
      "backend": {
        "type": "ORACLE_FUNCTIONS_BACKEND",
        "functionId": "$FUNC_OCID"
      }
    }
  ]
}
EOF

DEPLOYMENT_ID=$(oci api-gateway deployment list -c "$COMPARTMENT_ID" --gateway-id "$GW_ID" --display-name "$DEPLOYMENT_NAME" --lifecycle-state ACTIVE --query 'data.items[0].id' --raw-output 2>/dev/null || echo "")
if [ -z "$DEPLOYMENT_ID" ] || [ "$DEPLOYMENT_ID" == "None" ]; then
    echo "  -> Creando Deployment..."
    DEPLOYMENT_ID=$(oci api-gateway deployment create -c "$COMPARTMENT_ID" --gateway-id "$GW_ID" --display-name "$DEPLOYMENT_NAME" --path-prefix "$PATH_PREFIX" --specification file://deployment-spec.json --query 'data.id' --raw-output)
    echo "  -> Esperando a que el Deployment esté ACTIVE..."
    oci api-gateway deployment get --deployment-id "$DEPLOYMENT_ID" --wait-for-state ACTIVE > /dev/null
else
    echo "  -> Deployment ya existe, actualizando..."
    oci api-gateway deployment update --deployment-id "$DEPLOYMENT_ID" --specification file://deployment-spec.json > /dev/null
    oci api-gateway deployment get --deployment-id "$DEPLOYMENT_ID" --wait-for-state ACTIVE > /dev/null
fi

rm deployment-spec.json

GW_HOSTNAME=$(oci api-gateway gateway get --gateway-id "$GW_ID" --query 'data.hostname' --raw-output)

echo ""
echo "=========================================================="
echo "🚀 ¡DESPLIEGUE FINALIZADO!"
echo "=========================================================="
echo "👉 URL Base: https://$GW_HOSTNAME$PATH_PREFIX"
echo "✅ POST https://$GW_HOSTNAME$PATH_PREFIX/pedidos"
echo "✅ POST https://$GW_HOSTNAME$PATH_PREFIX/estado"
echo "=========================================================="