import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getProduct } from "../api";
import type { Product, Variant } from "../api";
import { useCart } from "../context/CartContext";
import styles from "./ProductSheet.module.css";

interface ProductSheetProps {
  productId: string | null;
  onClose: () => void;
}

export function ProductSheet({ productId, onClose }: ProductSheetProps) {
  const { t } = useTranslation();
  const { addItem } = useCart();

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState<Variant | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [status, setStatus] = useState<"idle" | "adding" | "added" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!productId) {
      setProduct(null);
      setSelectedVariant(null);
      setQuantity(1);
      setStatus("idle");
      setErrorMsg("");
      return;
    }

    setLoading(true);
    setStatus("idle");
    setErrorMsg("");

    getProduct(productId)
      .then((p) => {
        setProduct(p);
        const firstOrderable = p.variants.find((v) => v.is_orderable) ?? null;
        setSelectedVariant(firstOrderable);
        setQuantity(1);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [productId]);

  const handleVariantSelect = (v: Variant) => {
    if (!v.is_orderable) return;
    setSelectedVariant(v);
    setQuantity(1);
    setStatus("idle");
    setErrorMsg("");
  };

  const handleAdd = async () => {
    if (!selectedVariant) return;
    setStatus("adding");
    try {
      await addItem(selectedVariant.id, quantity);
      setStatus("added");
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        t("common.error");
      setErrorMsg(msg);
      setStatus("error");
    }
  };

  if (productId === null) return null;

  const allOnRequest =
    product !== null && product.variants.every((v) => !v.is_orderable);

  const maxQty = selectedVariant?.stock_qty ?? 1;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.sheet} onClick={(e) => e.stopPropagation()}>
        <div className={styles.handle} />

        {loading && <div className={styles.skeleton}>{t("common.loading")}</div>}

        {!loading && product && (
          <>
            <h2 className={styles.productName}>{product.name}</h2>
            {product.brand_name && (
              <p className={styles.brand}>{product.brand_name}</p>
            )}

            <div className={styles.variants}>
              {product.variants.map((v) => (
                <button
                  key={v.id}
                  className={[
                    styles.variantBtn,
                    selectedVariant?.id === v.id ? styles.variantBtnSelected : "",
                    !v.is_orderable ? styles.variantBtnDisabled : "",
                  ]
                    .join(" ")
                    .trim()}
                  onClick={() => handleVariantSelect(v)}
                  disabled={!v.is_orderable}
                >
                  {v.is_orderable
                    ? `${v.pack_size} — ${v.price?.toLocaleString("ru-RU")} ${t("catalog.currency")}`
                    : `${v.pack_size} — ${t("on_request")}`}
                </button>
              ))}
            </div>

            {allOnRequest ? (
              <p className={styles.contactMsg}>{t("contact_manager")}</p>
            ) : (
              <>
                <div className={styles.counter}>
                  <button
                    className={styles.counterBtn}
                    onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                    disabled={quantity <= 1}
                  >
                    −
                  </button>
                  <span className={styles.counterVal}>{quantity}</span>
                  <button
                    className={styles.counterBtn}
                    onClick={() => setQuantity((q) => Math.min(maxQty, q + 1))}
                    disabled={quantity >= maxQty}
                  >
                    +
                  </button>
                </div>

                {selectedVariant?.price != null && (
                  <p className={styles.totalLine}>
                    {t("total")}:{" "}
                    {(selectedVariant.price * quantity).toLocaleString("ru-RU")}{" "}
                    {t("catalog.currency")}
                  </p>
                )}

                {status === "added" ? (
                  <div className={styles.addedMsg}>✓ {t("added")}</div>
                ) : (
                  <button
                    className={styles.addBtn}
                    onClick={handleAdd}
                    disabled={status === "adding" || !selectedVariant}
                  >
                    {status === "adding" ? t("common.loading") : t("add_to_cart")}
                  </button>
                )}

                {status === "error" && (
                  <p className={styles.errorMsg}>{errorMsg}</p>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
