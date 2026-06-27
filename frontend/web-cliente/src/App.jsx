import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import ProductList from './pages/ProductList'
import Cart from './pages/Cart'
import OrderStatus from './pages/OrderStatus'

export default function App() {
  return (
    <div className="d-flex flex-column min-vh-100">
      <Navbar />
      <main className="flex-grow-1">
        <Routes>
          <Route path="/"           element={<ProductList />} />
          <Route path="/carrito"    element={<Cart />} />
          <Route path="/pedido/:id" element={<OrderStatus />} />
        </Routes>
      </main>
      <footer className="text-center py-3" style={{ color: 'var(--tb-muted)', fontSize: '.8rem', borderTop: '1px solid var(--tb-border)' }}>
        © 2024 Madam Tusan Pedidos Online · Powered by AWS Serverless
      </footer>
    </div>
  )
}
