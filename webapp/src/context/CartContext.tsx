import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { cartApi } from "../api";
import type { Cart } from "../api";

interface CartContextValue {
  cart: Cart | null;
  loading: boolean;
  totalItems: number;
  refreshCart: () => Promise<void>;
  addItem: (variant_id: string, quantity: number) => Promise<void>;
  updateItem: (item_id: string, quantity: number) => Promise<void>;
  removeItem: (item_id: string) => Promise<void>;
  clearCart: () => Promise<void>;
}

export const CartContext = createContext<CartContextValue>({
  cart: null,
  loading: false,
  totalItems: 0,
  refreshCart: async () => {},
  addItem: async () => {},
  updateItem: async () => {},
  removeItem: async () => {},
  clearCart: async () => {},
});

export function CartProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(false);

  const refreshCart = async () => {
    setLoading(true);
    try {
      setCart(await cartApi.getCart());
    } catch {
      // network error on init — stay null
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshCart();
  }, []);

  const addItem = async (variant_id: string, quantity: number) => {
    const result = await cartApi.addItem(variant_id, quantity);
    setCart(result);
  };

  const updateItem = async (item_id: string, quantity: number) => {
    const result = await cartApi.updateItem(item_id, quantity);
    setCart(result);
  };

  const removeItem = async (item_id: string) => {
    const result = await cartApi.removeItem(item_id);
    setCart(result);
  };

  const clearCart = async () => {
    const result = await cartApi.clearCart();
    setCart(result);
  };

  const totalItems = cart?.total_items ?? 0;

  return (
    <CartContext.Provider
      value={{ cart, loading, totalItems, refreshCart, addItem, updateItem, removeItem, clearCart }}
    >
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
