import WebApp from '@twa-dev/sdk';

/**
 * Обёртка над Telegram WebApp SDK.
 * При работе в браузере (не в Telegram) часть методов делает заглушку.
 */

export const tg = {
  isReady: false,

  init() {
    try {
      WebApp.ready();
      WebApp.expand();
      this.isReady = true;
    } catch {
      // не в Telegram — продолжаем без него
      console.warn('Not running inside Telegram. Mock mode.');
    }
  },

  /**
   * initData — подписанная строка от Telegram.
   * Передаём в API заголовком X-Telegram-Init-Data.
   * В режиме разработки (вне Telegram) возвращаем пустую строку —
   * бэкенд должен иметь dev-режим без проверки подписи.
   */
  get initData(): string {
    try {
      return WebApp.initData || '';
    } catch {
      return '';
    }
  },

  /**
   * Цветовая тема Telegram (light / dark).
   */
  get colorScheme(): 'light' | 'dark' {
    try {
      return WebApp.colorScheme;
    } catch {
      return 'light';
    }
  },

  /**
   * Язык интерфейса Telegram (ru, uz, en...) — используем для авто-i18n.
   */
  get language(): string {
    try {
      return WebApp.initDataUnsafe?.user?.language_code || 'ru';
    } catch {
      return 'ru';
    }
  },

  /**
   * Главная кнопка снизу Telegram — для CTA вроде "Оформить заказ".
   */
  mainButton: {
    show(text: string, onClick: () => void) {
      try {
        WebApp.MainButton.setText(text);
        WebApp.MainButton.onClick(onClick);
        WebApp.MainButton.show();
      } catch {}
    },
    hide() {
      try {
        WebApp.MainButton.hide();
      } catch {}
    },
  },

  /**
   * Кнопка "Назад" слева вверху Telegram.
   */
  backButton: {
    show(onClick: () => void) {
      try {
        WebApp.BackButton.onClick(onClick);
        WebApp.BackButton.show();
      } catch {}
    },
    hide() {
      try {
        WebApp.BackButton.hide();
      } catch {}
    },
  },

  /**
   * Тактильная отдача — для приятного UX на мобильных.
   */
  haptic: {
    light() {
      try {
        WebApp.HapticFeedback.impactOccurred('light');
      } catch {}
    },
    success() {
      try {
        WebApp.HapticFeedback.notificationOccurred('success');
      } catch {}
    },
  },
};
