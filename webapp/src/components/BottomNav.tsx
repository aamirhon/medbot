import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
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

  return (
    <nav className={styles.nav}>
      {tabs.map((tab) => {
        const isActive = location.pathname === tab.path;
        return (
          <Link
            key={tab.path}
            to={tab.path}
            className={`${styles.tab} ${isActive ? styles.active : ''}`}
          >
            <span className={styles.icon}>{tab.icon}</span>
            <span className={styles.label}>{t(tab.label)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
