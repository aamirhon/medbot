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

export default api;
