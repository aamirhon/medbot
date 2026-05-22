import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { orderApi } from '../api';
import type { OrderListItem } from '../api';

const LS_PAID = 'orders.lastSeen.paid';

function readLS(key: string): number {
  const v = localStorage.getItem(key);
  return v ? parseInt(v, 10) : 0;
}

interface OrdersContextValue {
  orders: OrderListItem[] | null;
  loading: boolean;
  pendingPaymentCount: number;
  paidCount: number;
  pendingPaymentBadge: number;
  paidBadge: number;
  refreshOrders: () => Promise<void>;
  markOrdersSeen: () => void;
}

export const OrdersContext = createContext<OrdersContextValue>({
  orders: null,
  loading: false,
  pendingPaymentCount: 0,
  paidCount: 0,
  pendingPaymentBadge: 0,
  paidBadge: 0,
  refreshOrders: async () => {},
  markOrdersSeen: () => {},
});

export function OrdersProvider({ children }: { children: ReactNode }) {
  const [orders, setOrders] = useState<OrderListItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastSeenPaid, setLastSeenPaid] = useState(() => readLS(LS_PAID));

  const pendingPaymentCount = orders
    ? orders.filter((o) => o.status === 'invoiced').length
    : 0;
  const paidCount = orders
    ? orders.filter((o) => ['paid', 'shipped', 'completed'].includes(o.status)).length
    : 0;

  // pending-payment badge = live count; clears only when orders are actually paid
  const pendingPaymentBadge = pendingPaymentCount;
  const paidBadge           = Math.max(0, paidCount - lastSeenPaid);

  const refreshOrders = async () => {
    setLoading(true);
    try {
      const data = await orderApi.list();
      setOrders(data);
    } catch (err) {
      console.error('OrdersContext: failed to load orders', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshOrders();
  }, []);

  const markOrdersSeen = () => {
    // only the "paid" badge uses seen-tracking; pending stays until orders are paid
    localStorage.setItem(LS_PAID, String(paidCount));
    setLastSeenPaid(paidCount);
  };

  return (
    <OrdersContext.Provider
      value={{
        orders,
        loading,
        pendingPaymentCount,
        paidCount,
        pendingPaymentBadge,
        paidBadge,
        refreshOrders,
        markOrdersSeen,
      }}
    >
      {children}
    </OrdersContext.Provider>
  );
}

export const useOrders = () => useContext(OrdersContext);
