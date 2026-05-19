/**
 * App.tsx — корневой роутер Mini App
 *
 * Изменения vs предыдущей версии:
 *   • /catalog теперь показывает настоящий <Catalog /> вместо заглушки
 *   • Stubs.tsx остаётся только для /cart и /orders
 */
import { Routes, Route, Navigate } from "react-router-dom";
import { Header } from "./components/Header";
import { BottomNav } from "./components/BottomNav";
import Home from "./pages/Home";
import Catalog from "./pages/Catalog";
import { CartStub, OrdersStub } from "./pages/Stubs";

export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/catalog" element={<Catalog />} />
        <Route path="/cart" element={<CartStub />} />
        <Route path="/orders" element={<OrdersStub />} />
        {/* Ловим неизвестные пути */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <BottomNav />
    </>
  );
}
