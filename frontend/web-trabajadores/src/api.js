import axios from 'axios'

const PEDIDOS_API  = import.meta.env.VITE_PEDIDOS_API
const WORKFLOW_API = import.meta.env.VITE_WORKFLOW_API
const TENANT_ID    = import.meta.env.VITE_TENANT_ID || 'taco-bell'

// ── Utils ─────────────────────────────────────────────────────────────────
const getHeaders = () => {
  const token = localStorage.getItem('id_token')
  return token ? { Authorization: token } : {}
}

// ── ms-pedidos ────────────────────────────────────────────────────────────

/** Lista todos los pedidos del tenant */
export const listarPedidos = () =>
  axios.get(`${PEDIDOS_API}/pedidos`, {
    params: { tenant_id: TENANT_ID },
    headers: getHeaders(),
  })

/** Lista pedidos filtrados por estado usando el GSI PorEstado */
export const listarPorEstado = (estado) =>
  axios.get(`${PEDIDOS_API}/pedidos/estado/${estado}`, {
    params: { tenant_id: TENANT_ID },
    headers: getHeaders(),
  })

/** Consulta el detalle de un pedido por ID */
export const consultarPedido = (pedidoId) =>
  axios.get(`${PEDIDOS_API}/pedidos/${pedidoId}`, {
    params: { tenant_id: TENANT_ID },
    headers: getHeaders(),
  })

// ── ms-workflow ───────────────────────────────────────────────────────────

/**
 * Avanza el estado del pedido en la Step Function.
 * paso: "COCINA" | "DESPACHO" | "REPARTO"
 */
export const avanzarPaso = ({ pedidoId, paso, usuario, observacion = '' }) =>
  axios.post(`${WORKFLOW_API}/pasos/avanzar`, {
    tenant_id:  TENANT_ID,
    pedido_id:  pedidoId,
    paso,
    usuario,
    observacion,
  }, {
    headers: getHeaders(),
  })

export const TENANT_ID_VALUE = TENANT_ID
