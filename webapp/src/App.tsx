import { Routes, Route, Navigate } from "react-router-dom";
import { Header } from "./components/Header";
import { BottomNav } from "./components/BottomNav";
import { CartProvider } from "./context/CartContext";
import { OrdersProvider } from "./context/OrdersContext";
import Home from "./pages/Home";
import Catalog from "./pages/Catalog";
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";
import Orders from "./pages/Orders";
import OrderDetails from "./pages/OrderDetails";

export default function App() {
  return (
    <CartProvider>
      <OrdersProvider>
        {/* Header is full-width; inner content centers itself */}
        <Header />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/catalog" element={<Catalog />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/orders/:id" element={<OrderDetails />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        {/* BottomNav is full-width fixed; inner tabs center themselves */}
        <BottomNav />
      </OrdersProvider>
    </CartProvider>
  );
}
