import { useTranslation } from 'react-i18next';

export function Catalog() {
  const { t } = useTranslation();
  return (
    <div style={{ padding: 20 }}>
      <h2>{t('nav.catalog')}</h2>
      <p style={{ color: 'var(--color-text-soft)' }}>
        Раздел в разработке. Здесь будет каталог товаров с поиском и фильтрами.
      </p>
    </div>
  );
}

export function Cart() {
  const { t } = useTranslation();
  return (
    <div style={{ padding: 20 }}>
      <h2>{t('nav.cart')}</h2>
      <p style={{ color: 'var(--color-text-soft)' }}>
        Корзина пуста. Скоро здесь появятся товары.
      </p>
    </div>
  );
}
