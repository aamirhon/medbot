import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import { Header } from './components/Header';
import { BottomNav } from './components/BottomNav';
import { Home } from './pages/Home';
import { Catalog, Cart } from './pages/Stubs';
import { tg } from './telegram';

import './i18n';
import './styles/global.css';

function App() {
  useEffect(() => {
    tg.init();
    // Применяем тему Telegram (если работаем в нём)
    document.documentElement.setAttribute('data-theme', tg.colorScheme);
  }, []);

  return (
    <BrowserRouter>
      <Header />
      <main style={{ paddingBottom: 70 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/catalog" element={<Catalog />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/orders" element={<Cart />} />
        </Routes>
      </main>
      <BottomNav />
    </BrowserRouter>
  );
}

export default App;
