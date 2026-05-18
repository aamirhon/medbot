-- Базовые лимиты для трёх уровней клиентов.
-- Применяются ко всем категориям (category_id IS NULL).
-- Запускать после первой синхронизации каталога из 1С.

-- Удалить старые дефолтные правила (если перезапускаем)
DELETE FROM tier_limits WHERE category_id IS NULL;

-- VIP — большие лимиты
INSERT INTO tier_limits (id, tier, category_id, max_qty_per_order, max_qty_per_month, max_amount_per_month)
VALUES (gen_random_uuid()::text, 'vip', NULL, 10000, 50000, 1000000000);

-- Стандартный — средние
INSERT INTO tier_limits (id, tier, category_id, max_qty_per_order, max_qty_per_month, max_amount_per_month)
VALUES (gen_random_uuid()::text, 'standard', NULL, 1000, 5000, 100000000);

-- Ограниченный — минимальные
INSERT INTO tier_limits (id, tier, category_id, max_qty_per_order, max_qty_per_month, max_amount_per_month)
VALUES (gen_random_uuid()::text, 'limited', NULL, 100, 500, 10000000);


-- Пример специальных лимитов для категории "Хирургические инструменты"
-- (раскомментировать после того как категория появится из 1С)
--
-- INSERT INTO tier_limits (id, tier, category_id, max_qty_per_order, max_qty_per_month, max_amount_per_month)
-- SELECT gen_random_uuid()::text, 'limited', c.id, 10, 50, 5000000
-- FROM categories c WHERE c.name = 'Хирургические инструменты';

-- Проверка:
SELECT tier, category_id, max_qty_per_order, max_qty_per_month, max_amount_per_month
FROM tier_limits
ORDER BY tier;
