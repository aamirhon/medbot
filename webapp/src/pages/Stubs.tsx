/**
 * Stubs.tsx — заглушки для страниц, которые ещё не реализованы.
 * Catalog убран отсюда — он теперь в pages/Catalog.tsx.
 */
import { useTranslation } from "react-i18next";

function StubPage({ labelKey }: { labelKey: string }) {
  const { t } = useTranslation();
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "60vh",
        color: "var(--tg-theme-hint-color, #8e8e93)",
        fontSize: 16,
      }}
    >
      {t(labelKey)} — {t("common.coming_soon")}
    </div>
  );
}

export function CartStub() {
  return <StubPage labelKey="nav.cart" />;
}

export function OrdersStub() {
  return <StubPage labelKey="nav.orders" />;
}
