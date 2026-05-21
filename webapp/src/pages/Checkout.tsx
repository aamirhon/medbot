import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { AxiosError } from 'axios';
import { useCart } from '../context/CartContext';
import { useOrders } from '../context/OrdersContext';
import { getMe, orderApi } from '../api';
import type { Me } from '../api';
import { formatMoney } from '../utils/format';
import styles from './Checkout.module.css';

export default function Checkout() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { cart, refreshCart } = useCart();
  const { refreshOrders } = useOrders();
  const [org, setOrg] = useState<Me['organization'] | null>(null);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMe().then((me) => setOrg(me.organization)).catch(() => {});
  }, []);

  useEffect(() => {
    if (cart !== null && cart.items.length === 0) {
      navigate('/cart', { replace: true });
    }
  }, [cart, navigate]);

  if (!cart || cart.items.length === 0) return null;

  const hasUnavailable = cart.has_unavailable;

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const order = await orderApi.create(comment);
      await Promise.all([refreshCart(), refreshOrders()]);
      navigate(`/orders/${order.id}?just_created=1`);
    } catch (err) {
      const e = err as AxiosError<{ detail: string }>;
      setError(e.response?.data?.detail ?? t('common.error'));
      setSubmitting(false);
    }
  };

  return (
    <div className={styles.page}>
      {hasUnavailable && (
        <div className={styles.unavailableWarning}>
          <span>{t('unavailable_in_cart')}</span>
          <button className={styles.toCartLink} onClick={() => navigate('/cart')}>
            {t('to_cart')}
          </button>
        </div>
      )}

      {org && (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>{t('recipient')}</h3>
          <div className={styles.orgName}>{org.name}</div>
          <div className={styles.orgInn}>ИНН: {org.inn}</div>
        </section>
      )}

      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>{t('order_composition')}</h3>
        <div className={styles.itemsList}>
          {cart.items.map((item) => (
            <div key={item.id} className={styles.orderItem}>
              <span className={styles.itemDesc}>
                {item.product_name} ({item.pack_size}) × {item.quantity} шт.
              </span>
              <span className={styles.itemSubtotal}>{formatMoney(item.subtotal)}</span>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.totalRow}>
          <span>{t('total')}:</span>
          <strong>{formatMoney(cart.total_amount)}</strong>
        </div>
      </section>

      <section className={styles.section}>
        <textarea
          className={styles.commentInput}
          placeholder={t('comment_placeholder')}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          maxLength={500}
          rows={3}
        />
      </section>

      {error && <div className={styles.errorBlock}>{error}</div>}

      <div className={styles.submitArea}>
        <button
          className={styles.submitBtn}
          onClick={handleSubmit}
          disabled={submitting || hasUnavailable}
        >
          {submitting ? t('creating_order') : t('confirm_order')}
        </button>
        <p className={styles.hint}>{t('checkout_hint')}</p>
      </div>
    </div>
  );
}
