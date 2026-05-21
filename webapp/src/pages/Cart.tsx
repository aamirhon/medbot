import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";
import styles from "./Cart.module.css";

export default function Cart() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { cart, loading, updateItem, removeItem, clearCart } = useCart();
  const [confirmClear, setConfirmClear] = useState(false);

  if (loading && cart === null) {
    return (
      <div className={styles.centered}>
        <div className={styles.spinner} />
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className={styles.centered}>
        <p className={styles.emptyText}>{t("cart_empty")}</p>
        <button className={styles.toCatalogBtn} onClick={() => navigate("/catalog")}>
          {t("to_catalog")}
        </button>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.list}>
        {cart.items.map((item) => (
          <div key={item.id} className={styles.item}>
            <div className={styles.itemHeader}>
              <div className={styles.itemName}>
                {item.product_name} {item.pack_size}
              </div>
              <button
                className={styles.removeBtn}
                onClick={() => removeItem(item.id)}
                aria-label="Удалить"
              >
                ✕
              </button>
            </div>

            <div className={styles.itemSku}>{item.sku}</div>

            {(!item.in_stock || !item.is_orderable) && (
              <div className={styles.warning}>{t("out_of_stock")}</div>
            )}

            <div className={styles.itemFooter}>
              <div className={styles.counter}>
                <button
                  className={styles.counterBtn}
                  onClick={() => {
                    if (item.quantity === 1) {
                      removeItem(item.id);
                    } else {
                      updateItem(item.id, item.quantity - 1);
                    }
                  }}
                >
                  −
                </button>
                <span className={styles.counterVal}>{item.quantity}</span>
                <button
                  className={styles.counterBtn}
                  onClick={() => updateItem(item.id, item.quantity + 1)}
                  disabled={item.quantity >= item.stock_qty}
                >
                  +
                </button>
              </div>

              <div className={styles.prices}>
                <div className={styles.unitPrice}>
                  {item.unit_price.toLocaleString("ru-RU")} {t("catalog.currency")}
                </div>
                <div className={styles.subtotal}>
                  {item.subtotal.toLocaleString("ru-RU")} {t("catalog.currency")}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className={styles.footer}>
        <div className={styles.footerTotal}>
          {t("total")}:{" "}
          <strong>{cart.total_amount.toLocaleString("ru-RU")} {t("catalog.currency")}</strong>
        </div>
        <button className={styles.checkoutBtn} disabled>
          {t("checkout")} — {t("coming_soon")}
        </button>
        <button className={styles.clearBtn} onClick={() => setConfirmClear(true)}>
          {t("clear_cart")}
        </button>
      </div>

      {confirmClear && (
        <div className={styles.confirmOverlay} onClick={() => setConfirmClear(false)}>
          <div className={styles.confirmSheet} onClick={(e) => e.stopPropagation()}>
            <p className={styles.confirmTitle}>{t("confirm_clear_title")}</p>
            <p className={styles.confirmBody}>{t("confirm_clear_body")}</p>
            <div className={styles.confirmActions}>
              <button
                className={styles.confirmCancel}
                onClick={() => setConfirmClear(false)}
              >
                {t("cancel")}
              </button>
              <button
                className={styles.confirmOk}
                onClick={() => { clearCart(); setConfirmClear(false); }}
              >
                {t("clear_cart")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
