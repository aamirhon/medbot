import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useOrders } from '../context/OrdersContext';
import { getStatusLabel, getStatusColor } from '../utils/orderStatus';
import { formatMoney, formatDate } from '../utils/format';
import styles from './Orders.module.css';

export default function Orders() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { orders, loading, markOrdersSeen, refreshOrders } = useOrders();

  useEffect(() => {
    refreshOrders();
    markOrdersSeen();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading && orders === null) {
    return (
      <div className={styles.centered}>
        <div className={styles.spinner} />
      </div>
    );
  }

  if (!orders || orders.length === 0) {
    return (
      <div className={styles.centered}>
        <p className={styles.emptyText}>{t('no_orders')}</p>
        <button className={styles.toCatalogBtn} onClick={() => navigate('/catalog')}>
          {t('to_catalog')}
        </button>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {orders.map((order) => (
        <div
          key={order.id}
          className={styles.card}
          onClick={() => navigate(`/orders/${order.id}`)}
        >
          <div className={styles.cardTop}>
            <span className={styles.cardTitle}>
              {order.invoice_number
                ? `${t('order_number')} № ${order.invoice_number}`
                : `${t('order_number')} от ${formatDate(order.created_at)}`}
            </span>
            <span
              className={styles.statusBadge}
              style={{ background: getStatusColor(order.status) }}
            >
              {getStatusLabel(order.status, t)}
            </span>
          </div>
          <div className={styles.cardMid}>
            {order.items_count} {t('positions')} · {formatDate(order.created_at)}
          </div>
          <div className={styles.cardBot}>
            <span className={styles.cardAmount}>{formatMoney(order.total_amount)}</span>
            <button
              className={styles.detailsBtn}
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/orders/${order.id}`);
              }}
            >
              {t('details')}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
