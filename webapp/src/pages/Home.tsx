import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import { getMe, getCategories } from '../api';
import type { Category, Me } from '../api';
import styles from './Home.module.css';

export function Home() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [me, setMe] = useState<Me | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getMe(), getCategories()])
      .then(([meData, cats]) => {
        setMe(meData);
        // Только категории верхнего уровня (без parent)
        setCategories(cats.filter((c) => c.parent_id === null));
      })
      .catch((err) => {
        console.error(err);
        setError(err.response?.data?.detail || 'Ошибка загрузки');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className={styles.center}>{t('common.loading')}</div>;
  if (error) return <div className={styles.center}>{error}</div>;

  return (
    <div className={styles.container}>
      {me && (
        <div className={styles.greeting}>
          {t('home.greeting', { name: me.first_name })}
          <div className={styles.orgName}>{me.organization.name}</div>
        </div>
      )}

      {me?.has_limits && (
        <div className={styles.warning}>{t('home.limits_warning')}</div>
      )}

      <h2 className={styles.sectionTitle}>{t('home.categories_title')}</h2>

      <div className={styles.grid}>
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={styles.card}
            onClick={() => navigate(`/catalog?category=${cat.id}`)}
          >
            <div className={styles.cardIcon}>{getCategoryIcon(cat.name)}</div>
            <div className={styles.cardName}>{cat.name}</div>
            <div className={styles.cardCount}>
              {cat.product_count} {t('common.products')}
            </div>
          </button>
        ))}
      </div>

      <button
        className={styles.allButton}
        onClick={() => navigate('/catalog')}
      >
        {t('home.all_products')} →
      </button>
    </div>
  );
}

export default Home;

/** Простая иконка по первой букве — заменим на нормальные иконки позже */
function getCategoryIcon(name: string): string {
  const icons: Record<string, string> = {
    'ИХЛА': '🧪',
    'Биохимия': '🔬',
    'Гематология': '🩸',
    'Гликированный гемоглобин': '📊',
    'Гемостаз': '💊',
    'Микробиология': '🦠',
    'Анализ мочи': '💧',
    'Контроль качества': '✓',
    'Расходные материалы': '📦',
  };
  for (const key in icons) {
    if (name.includes(key)) return icons[key];
  }
  return '◆';
}
