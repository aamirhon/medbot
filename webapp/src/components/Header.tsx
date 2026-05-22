import { useTranslation } from 'react-i18next';
import styles from './Header.module.css';

export function Header() {
  const { t, i18n } = useTranslation();

  const toggleLanguage = () => {
    const next = i18n.language === 'ru' ? 'uz' : 'ru';
    i18n.changeLanguage(next);
  };

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.brand}>
          <span className={styles.logo}>Albatros</span>
          <span className={styles.tagline}>Healthcare</span>
        </div>
        <button
          className={styles.langButton}
          onClick={toggleLanguage}
          title={t('common.language')}
        >
          {i18n.language === 'ru' ? 'O\'Z' : 'RU'}
        </button>
      </div>
    </header>
  );
}
