import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useCart } from '../context/CartContext';
import styles from './BottomNav.module.css';

const tabs = [
  { path: '/',        label: 'nav.home',    icon: '⌂' },
  { path: '/catalog', label: 'nav.catalog', icon: '☰' },
  { path: '/cart',    label: 'nav.cart',    icon: '◔' },
  { path: '/orders',  label: 'nav.orders',  icon: '✓' },
];

export function BottomNav() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const { totalItems } = useCart();

  const handleCatalogClick = () => {
    navigate('/catalog', { replace: location.pathname === '/catalog' });
  };

  return (
    <nav className={styles.nav}>
      {tabs.map((tab) => {
        const isActive = location.pathname === tab.path;
        if (tab.path === '/catalog') {
          return (
            <button
              key={tab.path}
              className={`${styles.tab} ${isActive ? styles.active : ''}`}
              onClick={handleCatalogClick}
            >
              <span className={styles.icon}>{tab.icon}</span>
              <span className={styles.label}>{t(tab.label)}</span>
            </button>
          );
        }
        return (
          <Link
            key={tab.path}
            to={tab.path}
            className={`${styles.tab} ${isActive ? styles.active : ''}`}
          >
            <span className={styles.iconWrap}>
              <span className={styles.icon}>{tab.icon}</span>
              {tab.path === '/cart' && totalItems > 0 && (
                <span className={styles.badge}>
                  {totalItems > 99 ? '99+' : totalItems}
                </span>
              )}
            </span>
            <span className={styles.label}>{t(tab.label)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
