import { useEffect, useRef, useState, useCallback } from "react";
import { useSearchParams, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { Brand, Category, Product, ProductFilters } from "../api";
import { getBrands, getCategories, getProducts } from "../api";
import { ProductSheet } from "../components/ProductSheet";
import styles from "./Catalog.module.css";

// ─── Вспомогательные компоненты ──────────────────────────────────────────────

function PriceTag({ price }: { price: number | null }) {
  const { t } = useTranslation();
  if (price === null) {
    return <span className={styles.priceOnRequest}>{t("catalog.on_request")}</span>;
  }
  return (
    <span className={styles.price}>
      {price.toLocaleString("ru-RU")} {t("catalog.currency")}
    </span>
  );
}

function VariantPrices({ variants }: { variants: Product["variants"] }) {
  const orderable = variants.filter((v) => v.is_orderable);
  const onRequest = variants.filter((v) => !v.is_orderable);

  if (orderable.length === 0 && onRequest.length > 0) {
    return <PriceTag price={null} />;
  }

  return (
    <div className={styles.variantPrices}>
      {orderable.map((v) => (
        <div key={v.id} className={styles.variantPriceLine}>
          <span className={styles.packSize}>{v.pack_size}</span>
          <PriceTag price={v.price} />
        </div>
      ))}
    </div>
  );
}

/** Карточка товара в режиме ПЛИТКА */
function ProductGridItem({
  product,
  onSelect,
}: {
  product: Product;
  onSelect: (id: string) => void;
}) {
  const { t } = useTranslation();

  return (
    <div className={styles.gridItem} onClick={() => onSelect(product.id)}>
      <div className={styles.gridItemName}>{product.name}</div>
      {product.brand_name && (
        <div className={styles.gridItemBrand}>{product.brand_name}</div>
      )}
      <VariantPrices variants={product.variants} />
      <div className={styles.gridItemFooter}>
        {product.is_orderable ? (
          <button
            className={styles.btnAdd}
            onClick={(e) => {
              e.stopPropagation();
              onSelect(product.id);
            }}
          >
            {t("catalog.add")}
          </button>
        ) : (
          <span className={styles.tagOnRequest}>{t("catalog.on_request")}</span>
        )}
      </div>
    </div>
  );
}

// ─── Главный компонент ────────────────────────────────────────────────────────

export default function Catalog() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();

  // ── Данные ────────────────────────────────────────────────────────────────
  const [brands, setBrands] = useState<Brand[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Фильтры ───────────────────────────────────────────────────────────────
  const [search, setSearch] = useState("");
  const [brandId, setBrandId] = useState(searchParams.get("brand") ?? "");
  const [categoryId, setCategoryId] = useState(searchParams.get("category") ?? "");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [inStockOnly, setInStockOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  const PER_PAGE = 20;

  // ── Синхронизация фильтров при смене URL (например, BottomNav → /catalog) ─
  // location.search — строка, сравнивается по значению, надёжнее чем объект searchParams
  useEffect(() => {
    setCategoryId(searchParams.get("category") ?? "");
    setBrandId(searchParams.get("brand") ?? "");
    if (!location.search) {
      setSearch("");
      setMinPrice("");
      setMaxPrice("");
      setInStockOnly(false);
    }
  }, [location.search]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Дебаунс поиска ────────────────────────────────────────────────────────
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => setDebouncedSearch(search), 400);
    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    };
  }, [search]);

  // ── Начальная загрузка брендов и категорий ─────────────────────────────────
  useEffect(() => {
    getBrands().then(setBrands).catch(console.error);
    getCategories().then(setCategories).catch(console.error);
  }, []);

  // ── Загрузка товаров при изменении фильтров ────────────────────────────────
  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const filters: ProductFilters = {
        page,
        per_page: PER_PAGE,
      };
      if (categoryId) filters.category_id = categoryId;
      if (brandId) filters.brand_id = brandId;
      if (debouncedSearch) filters.search = debouncedSearch;
      if (minPrice) filters.min_price = parseFloat(minPrice);
      if (maxPrice) filters.max_price = parseFloat(maxPrice);
      if (inStockOnly) filters.in_stock_only = true;

      const data = await getProducts(filters);
      setProducts(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(t("catalog.load_error"));
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [page, categoryId, brandId, debouncedSearch, minPrice, maxPrice, inStockOnly, t]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  // Сбрасываем страницу при смене фильтров
  useEffect(() => {
    setPage(1);
  }, [categoryId, brandId, debouncedSearch, minPrice, maxPrice, inStockOnly]);

  // ── ProductSheet ──────────────────────────────────────────────────────────
  const [sheetProductId, setSheetProductId] = useState<string | null>(null);

  const handleSelect = (id: string) => {
    setSheetProductId(id);
  };

  // ── Сброс всех фильтров ────────────────────────────────────────────────────
  const resetFilters = () => {
    setSearch("");
    setBrandId("");
    setCategoryId("");
    setMinPrice("");
    setMaxPrice("");
    setInStockOnly(false);
    setPage(1);
    setSearchParams({});
  };

  const hasActiveFilters =
    brandId || categoryId || minPrice || maxPrice || inStockOnly || debouncedSearch;

  const totalPages = Math.ceil(total / PER_PAGE);

  // ── Получаем название активной категории ──────────────────────────────────
  const activeCategoryName = categoryId
    ? categories.find((c) => c.id === categoryId)?.name
    : null;

  return (
    <div className={styles.page}>
      {/* ── Поиск ──────────────────────────────────────────────────────── */}
      <div className={styles.searchBar}>
        <input
          className={styles.searchInput}
          type="search"
          placeholder={t("catalog.search_placeholder")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button
          className={`${styles.filterToggle} ${showFilters ? styles.filterToggleActive : ""}`}
          onClick={() => setShowFilters((v) => !v)}
          aria-label={t("catalog.filters")}
        >
          <FilterIcon />
          {hasActiveFilters && <span className={styles.filterBadge} />}
        </button>
      </div>

      {/* ── Панель фильтров ────────────────────────────────────────────── */}
      {/* filterPanelHidden hides on mobile when !showFilters; CSS forces visible on tablet+ */}
      <div className={`${styles.filterPanel} ${showFilters ? '' : styles.filterPanelHidden}`}>
          {/* Бренд */}
          <div className={styles.filterRow}>
            <label className={styles.filterLabel}>{t("catalog.brand")}</label>
            <select
              className={styles.filterSelect}
              value={brandId}
              onChange={(e) => setBrandId(e.target.value)}
            >
              <option value="">{t("catalog.all_brands")}</option>
              {brands.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>

          {/* Категория */}
          <div className={styles.filterRow}>
            <label className={styles.filterLabel}>{t("catalog.category")}</label>
            <select
              className={styles.filterSelect}
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
            >
              <option value="">{t("catalog.all_categories")}</option>
              {categories
                .filter((c) => !c.parent_id) // только верхний уровень
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
            </select>
          </div>

          {/* Цена */}
          <div className={styles.filterRow}>
            <label className={styles.filterLabel}>{t("catalog.price")}</label>
            <div className={styles.priceRange}>
              <input
                className={styles.priceInput}
                type="number"
                placeholder={t("catalog.price_from")}
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                min={0}
              />
              <span className={styles.priceDash}>—</span>
              <input
                className={styles.priceInput}
                type="number"
                placeholder={t("catalog.price_to")}
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                min={0}
              />
            </div>
          </div>

          {/* В наличии */}
          <div className={styles.filterRow}>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={inStockOnly}
                onChange={(e) => setInStockOnly(e.target.checked)}
              />
              {t("catalog.in_stock_only")}
            </label>
          </div>

          {hasActiveFilters && (
            <button className={styles.resetBtn} onClick={resetFilters}>
              {t("catalog.reset_filters")}
            </button>
          )}
        </div>

      {/* ── Заголовок раздела + переключатель вида ──────────────────────── */}
      <div className={styles.toolbar}>
        <div className={styles.toolbarLeft}>
          {activeCategoryName ? (
            <span className={styles.sectionTitle}>{activeCategoryName}</span>
          ) : (
            <span className={styles.sectionTitle}>{t("catalog.title")}</span>
          )}
          {!loading && (
            <span className={styles.totalCount}>
              {t("catalog.found", { count: total })}
            </span>
          )}
        </div>
      </div>

      {/* ── Контент ───────────────────────────────────────────────────────── */}
      {loading && <div className={styles.loader}>{t("catalog.loading")}</div>}

      {!loading && error && (
        <div className={styles.errorBox}>
          <p>{error}</p>
          <button className={styles.retryBtn} onClick={fetchProducts}>
            {t("catalog.retry")}
          </button>
        </div>
      )}

      {!loading && !error && products.length === 0 && (
        <div className={styles.emptyBox}>{t("catalog.empty")}</div>
      )}

      {!loading && !error && products.length > 0 && (
        <>
          <div className={styles.gridContainer}>
            {products.map((p) => (
              <ProductGridItem key={p.id} product={p} onSelect={handleSelect} />
            ))}
          </div>

          {/* ── Пагинация ─────────────────────────────────────────────── */}
          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button
                className={styles.pageBtn}
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
              >
                ‹
              </button>
              <span className={styles.pageInfo}>
                {page} / {totalPages}
              </span>
              <button
                className={styles.pageBtn}
                disabled={page === totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                ›
              </button>
            </div>
          )}
        </>
      )}
      <ProductSheet
        productId={sheetProductId}
        onClose={() => setSheetProductId(null)}
      />
    </div>
  );
}

// ─── Иконки (SVG inline, без зависимости от библиотеки) ──────────────────────

function FilterIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="4" y1="6" x2="20" y2="6" />
      <line x1="8" y1="12" x2="16" y2="12" />
      <line x1="11" y1="18" x2="13" y2="18" />
    </svg>
  );
}

