import axios from 'axios';
import { tg } from '../telegram';

/**
 * HTTP-клиент для нашего FastAPI бэкенда.
 * Все запросы автоматически добавляют X-Telegram-Init-Data
 * — это наша авторизация.
 */

// Адрес API — для разработки на localhost, для прода будет другой
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8002';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

// Перехватчик: добавляем заголовок авторизации к каждому запросу
api.interceptors.request.use((config) => {
  config.headers['X-Telegram-Init-Data'] = tg.initData;
  // DEV: для разработки в браузере (без Telegram)
  if (import.meta.env.DEV) {
    config.headers['X-Dev-Telegram-Id'] = import.meta.env.VITE_DEV_TG_ID || '';
  }
  return config;
});

// Перехватчик ответа: централизованная обработка ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('Не авторизованы — initData невалиден');
    }
    if (error.response?.status === 403) {
      console.error('Доступ запрещён — пользователь не зарегистрирован');
    }
    return Promise.reject(error);
  }
);

// ─── Типы данных ────────────────────────────────────────────────────────────

export interface Category {
  id: string;
  name: string;
  parent_id: string | null;
  product_count: number;
}

export interface Brand {
  id: string;
  code: string;
  name: string;
  sort_order: number;
}

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

// ─── Методы API ──────────────────────────────────────────────────────────────

export const apiClient = {
  me: () => api.get<Me>('/me').then((r) => r.data),
  categories: () =>
    api.get<Category[]>('/catalog/categories').then((r) => r.data),
};
