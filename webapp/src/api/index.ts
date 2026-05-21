/**
 * Albatros Mini App — API client
 * Базовый URL берётся из VITE_API_URL (или фоллбэк на localhost:8002)
 */
import axios from "axios";
import { tg } from "../telegram";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8002";
const DEV_TG_ID = import.meta.env.VITE_DEV_TG_ID ?? "";

// ─── Axios instance ────────────────────────────────────────────────────────

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const initData = tg?.initData;
  if (initData) {
    config.headers["X-Telegram-Init-Data"] = initData;
  } else if (DEV_TG_ID) {
    config.headers["X-Dev-Telegram-Id"] = DEV_TG_ID;
  }
  return config;
});

// ─── Types ────────────────────────────────────────────────────────────────

export interface Me {
  user_id: string;
  first_name: string;
  role: string;
  organization: {
    id: string;
    name: string;
    inn: string;
    type: string;
  };
  has_limits: boolean;
}

export interface Brand {
  id: string;
  code: string;
  name: string;
  sort_order: number;
}

export interface Category {
  id: string;
  name: string;
  parent_id: string | null;
  product_count: number;
}

export interface Variant {
  id: string;
  sku: string;
  pack_size: string;       // "50 опред." / "100 опред." / "1x714 мл"
  price: number | null;    // null = "По запросу"
  is_orderable: boolean;
  stock_qty: number;
}

export interface Product {
  id: string;
  name: string;
  short_name: string;
  category_id: string | null;
  brand_id: string | null;
  brand_name: string | null;
  image_url: string;
  variants: Variant[];
  min_price: number | null;
  is_orderable: boolean;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  per_page: number;
}

export interface ProductFilters {
  category_id?: string;
  brand_id?: string;
  search?: string;
  min_price?: number;
  max_price?: number;
  in_stock_only?: boolean;
  page?: number;
  per_page?: number;
}

// ─── API methods ──────────────────────────────────────────────────────────

export const getMe = (): Promise<Me> =>
  api.get<Me>("/me").then((r) => r.data);

export const getCategories = (): Promise<Category[]> =>
  api.get<Category[]>("/catalog/categories").then((r) => r.data);

export const getBrands = (): Promise<Brand[]> =>
  api.get<Brand[]>("/catalog/brands").then((r) => r.data);

export const getProducts = (filters: ProductFilters = {}): Promise<ProductListResponse> => {
  // Убираем undefined/null значения из параметров
  const params: Record<string, string | number | boolean> = {};
  for (const [k, v] of Object.entries(filters)) {
    if (v !== undefined && v !== null && v !== "") {
      params[k] = v as string | number | boolean;
    }
  }
  return api.get<ProductListResponse>("/catalog/products", { params }).then((r) => r.data);
};

export const getProduct = (id: string): Promise<Product> =>
  api.get<Product>(`/catalog/products/${id}`).then((r) => r.data);

// ─── Order types ──────────────────────────────────────────────────────────────

export interface OrderItem {
  id: string;
  variant_id: string;
  product_name: string;
  pack_size: string;
  sku: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Order {
  id: string;
  status: string;
  total_amount: number;
  comment: string;
  invoice_number: string | null;
  invoice_url: string | null;
  contract_url: string | null;
  created_at: string;
  paid_at: string | null;
  items: OrderItem[];
}

export interface OrderListItem {
  id: string;
  status: string;
  total_amount: number;
  invoice_number: string | null;
  items_count: number;
  created_at: string;
}

// ─── Order API ────────────────────────────────────────────────────────────────

export const orderApi = {
  create: (comment: string): Promise<Order> =>
    api.post<Order>('/orders', { comment }).then((r) => r.data),
  list: (): Promise<OrderListItem[]> =>
    api.get<OrderListItem[]>('/orders').then((r) => r.data),
  get: (id: string): Promise<Order> =>
    api.get<Order>(`/orders/${id}`).then((r) => r.data),
};

// ─── Cart types ───────────────────────────────────────────────────────────────

export interface CartVariantItem {
  id: string;
  variant_id: string;
  product_id: string;
  product_name: string;
  short_name: string;
  pack_size: string;
  sku: string;
  unit: string;
  unit_price: number;
  quantity: number;
  subtotal: number;
  image_url: string;
  stock_qty: number;
  in_stock: boolean;
  is_orderable: boolean;
}

export interface Cart {
  items: CartVariantItem[];
  total_items: number;
  total_amount: number;
  has_unavailable: boolean;
}

// ─── Cart API ─────────────────────────────────────────────────────────────────

export const cartApi = {
  getCart: () => api.get<Cart>("/cart").then((r) => r.data),
  addItem: (variant_id: string, quantity: number) =>
    api.post<Cart>("/cart/items", { variant_id, quantity }).then((r) => r.data),
  updateItem: (item_id: string, quantity: number) =>
    api.patch<Cart>(`/cart/items/${item_id}`, { quantity }).then((r) => r.data),
  removeItem: (item_id: string) =>
    api.delete<Cart>(`/cart/items/${item_id}`).then((r) => r.data),
  clearCart: () => api.delete<Cart>("/cart").then((r) => r.data),
};

export default api;
