#!/usr/bin/env python3
"""
seed_productos.py — Inserta los productos de Popeyes en DynamoDB.

Uso:
    python scripts/seed_productos.py [--stage dev|prod] [--tenant popeyes]

Requiere credenciales AWS configuradas (mismo perfil que el deploy de Serverless).
"""
import argparse
import uuid
import decimal
import boto3

# ── Catálogo de Popeyes ─────────────────────────────────────────────────────
PRODUCTOS = [
    {
        "nombre": "Pollo Frito Clásico (3 piezas)",
        "descripcion": "Pollo frito sazonado con la receta original de Louisiana, crocante por fuera y jugoso por dentro.",
        "precio": 24.00,
        "categoria": "Pollo",
        "disponible": True,
    },
    {
        "nombre": "Pollo Frito Picante (3 piezas)",
        "descripcion": "Pollo frito con el toque picante característico de Popeyes, marinado por horas.",
        "precio": 25.00,
        "categoria": "Pollo",
        "disponible": True,
    },
    {
        "nombre": "Tenders de Pollo (5 piezas)",
        "descripcion": "Tiras de pollo apanadas y fritas, crocantes, servidas con tu salsa favorita.",
        "precio": 21.00,
        "categoria": "Pollo",
        "disponible": True,
    },
    {
        "nombre": "Sandwich Clásico de Pollo",
        "descripcion": "Filete de pollo crocante, pan brioche, lechuga y mayonesa, receta original de Popeyes.",
        "precio": 18.50,
        "categoria": "Sandwiches",
        "disponible": True,
    },
    {
        "nombre": "Sandwich Picante de Pollo",
        "descripcion": "Filete de pollo crocante con marinado picante, pan brioche y pickles.",
        "precio": 19.50,
        "categoria": "Sandwiches",
        "disponible": True,
    },
    {
        "nombre": "Camarones Apanados (8 piezas)",
        "descripcion": "Camarones empanizados y fritos, crocantes, servidos con salsa cocktail.",
        "precio": 26.00,
        "categoria": "Mariscos",
        "disponible": True,
    },
    {
        "nombre": "Cajun Fries",
        "descripcion": "Papas fritas sazonadas con la mezcla de especias cajún de la casa.",
        "precio": 10.00,
        "categoria": "Acompañamientos",
        "disponible": True,
    },
    {
        "nombre": "Red Beans & Rice",
        "descripcion": "Arroz con frijoles rojos al estilo Louisiana, guarnición clásica de Popeyes.",
        "precio": 9.50,
        "categoria": "Acompañamientos",
        "disponible": True,
    },
    {
        "nombre": "Buñuelos (Biscuits, 2 piezas)",
        "descripcion": "Panecillos suaves recién horneados, ideales para acompañar el pollo.",
        "precio": 7.00,
        "categoria": "Acompañamientos",
        "disponible": True,
    },
    {
        "nombre": "Combo Familiar (8 piezas + 2 acompañamientos)",
        "descripcion": "8 piezas de pollo frito a elección con 2 acompañamientos grandes para compartir.",
        "precio": 65.00,
        "categoria": "Combos",
        "disponible": True,
    },
    {
        "nombre": "Mac & Cheese",
        "descripcion": "Macarrones cremosos con queso fundido, guarnición clásica americana.",
        "precio": 11.00,
        "categoria": "Acompañamientos",
        "disponible": True,
    },
    {
        "nombre": "Pie de Manzana",
        "descripcion": "Postre individual de manzana horneado, crocante por fuera y caliente por dentro.",
        "precio": 8.00,
        "categoria": "Postres",
        "disponible": True,
    },
]


def seed(stage: str, tenant_id: str) -> None:
    table_name = f"productos-{stage}"
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    tabla = dynamodb.Table(table_name)

    print(f"\n🍗 Insertando {len(PRODUCTOS)} productos de Popeyes")
    print(f"   Tabla  : {table_name}")
    print(f"   Tenant : {tenant_id}\n")

    creados = 0
    errores = 0

    for p in PRODUCTOS:
        item = {
            "tenant_id": tenant_id,
            "producto_id": uuid.uuid4().hex,
            "nombre": p["nombre"],
            "descripcion": p["descripcion"],
            "precio": decimal.Decimal(str(p["precio"])),
            "categoria": p["categoria"],
            "disponible": p["disponible"],
        }
        try:
            tabla.put_item(Item=item)
            print(f"  ✅ {p['nombre']:<40} S/ {p['precio']:.2f}")
            creados += 1
        except Exception as e:
            print(f"  ❌ Error al insertar '{p['nombre']}': {e}")
            errores += 1

    print(f"\nResumen: {creados} insertados, {errores} errores.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed de productos Popeyes en DynamoDB")
    parser.add_argument("--stage", default="dev", choices=["dev", "prod"], help="Stage de despliegue (default: dev)")
    parser.add_argument("--tenant", default="popeyes", help="Tenant ID (default: popeyes)")
    args = parser.parse_args()
    seed(args.stage, args.tenant)
