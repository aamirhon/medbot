import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { orderApi } from '../api';
import type { Order } from '../api';
import { getStatusLabel, getStatusColor } from '../utils/orderStatus';
import { fixPdfUrl } from '../utils/pdfUrl';
import { formatMoney, formatDate } from '../utils/format';
import styles from './OrderDetails.module.css';

export default function OrderDetails() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const justCreated = searchParams.get('just_created') === '1';
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    orderApi
      .get(id)
      .then(setOrder)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className={styles.centered}>
        <div className={styles.spinner} />
      </div>
    );
  }

  if (!order) {
    return (
      <div className={styles.centered}>
        <p className={styles.emptyText}>{t('common.error')}</p>
      </div>
    );
  }

  const invoiceUrl = fixPdfUrl(order.invoice_url);
  const contractUrl = fixPdfUrl(order.contract_url);
  const hasDocs = !!(invoiceUrl || contractUrl);

  return (
    <div className={styles.page}>
      {justCreated && order.status === 'invoiced' && (
        <div className={styles.successBanner}>✓ {t('order_created')}</div>
      )}

      <div className={styles.header}>
        <h2 className={styles.orderTitle}>
          {order.invoice_number
            ? `${t('order_number')} № ${order.invoice_number}`
            : `${t('order_number')} от ${formatDate(order.created_at)}`}
        </h2>
        <span
          className={styles.statusBadge}
          style={{ background: getStatusColor(order.status) }}
        >
          {getStatusLabel(order.status, t)}
        </span>
        <div className={styles.orderDate}>{formatDate(order.created_at)}</div>
      </div>

      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>{t('documents')}</h3>
        {hasDocs ? (
          <div className={styles.docButtons}>
            {invoiceUrl && (
              <button
                className={styles.docBtn}
                onClick={() => window.open(invoiceUrl, '_blank', 'noopener')}
              >
                📄 {t('download_invoice')}
              </button>
            )}
            {contractUrl && (
              <button
                className={styles.docBtn}
                onClick={() => window.open(contractUrl, '_blank', 'noopener')}
              >
                📄 {t('download_contract')}
              </button>
            )}
          </div>
        ) : (
          <p className={styles.docsHint}>{t('documents_preparing')}</p>
        )}
      </section>

      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>{t('order_composition')}</h3>
        <div className={styles.itemsList}>
          {order.items.map((item) => (
            <div key={item.id} className={styles.orderItem}>
              <div className={styles.itemLeft}>
                <div className={styles.itemName}>{item.product_name}</div>
                <div className={styles.itemPack}>{item.pack_size}</div>
              </div>
              <div className={styles.itemRight}>
                × {item.quantity} = {formatMoney(item.subtotal)}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.totalRow}>
          <span>{t('order_total')}:</span>
          <strong>{formatMoney(order.total_amount)}</strong>
        </div>
      </section>

      {order.comment && (
        <section className={styles.section}>
          <div className={styles.commentBlock}>
            <span className={styles.commentLabel}>{t('comment_label')}:</span>
            {' '}{order.comment}
          </div>
        </section>
      )}

      <div className={styles.paymentHint}>{t('payment_hint')}</div>
    </div>
  );
}
