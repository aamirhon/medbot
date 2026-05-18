"""
Реальный каталог Albatros Healthcare.
Источник: прайс-лист от 01.12.2025.

Структура: BRANDS → CATEGORIES → PRODUCTS → VARIANTS

Каждый PRODUCT имеет один или несколько VARIANTS (фасовок).
VARIANT с price=None и is_orderable=False — "По запросу".
"""

# ─── Бренды ──────────────────────────────────────────────────────────────────

BRANDS = [
    {"code": "snibe",      "name": "SNIBE Maglumi",            "sort": 1},
    {"code": "dymind",     "name": "DYMIND",                   "sort": 2},
    {"code": "werfen",     "name": "Werfen (Instrumentation Laboratory)", "sort": 3},
    {"code": "bd",         "name": "BD (Becton Dickinson)",    "sort": 4},
    {"code": "urit",       "name": "URIT",                     "sort": 5},
    {"code": "lifotronic", "name": "Lifotronic",               "sort": 6},
    {"code": "randox",     "name": "RANDOX",                   "sort": 7},
]


# ─── Категории (двухуровневая иерархия) ─────────────────────────────────────

CATEGORIES = [
    # Верхний уровень — направления диагностики
    {"id": "ihla",     "name": "ИХЛА (Иммунохемилюминесценция)", "parent": None, "sort": 1},
    {"id": "biochem",  "name": "Биохимия",                       "parent": None, "sort": 2},
    {"id": "hema",     "name": "Гематология",                    "parent": None, "sort": 3},
    {"id": "hba1c",    "name": "Гликированный гемоглобин",       "parent": None, "sort": 4},
    {"id": "hemos",    "name": "Гемостаз",                       "parent": None, "sort": 5},
    {"id": "micro",    "name": "Микробиология",                  "parent": None, "sort": 6},
    {"id": "urine",    "name": "Анализ мочи",                    "parent": None, "sort": 7},
    {"id": "qc",       "name": "Контроль качества",              "parent": None, "sort": 8},
    {"id": "consum",   "name": "Расходные материалы",            "parent": None, "sort": 9},

    # ИХЛА — клинические панели
    {"id": "thyroid",      "name": "Щитовидная панель",      "parent": "ihla", "sort": 1},
    {"id": "reprod",       "name": "Репродуктивная панель",  "parent": "ihla", "sort": 2},
    {"id": "prenatal",     "name": "Пренатальный скрининг",  "parent": "ihla", "sort": 3},
    {"id": "bone",         "name": "Костный метаболизм",     "parent": "ihla", "sort": 4},
    {"id": "onco",         "name": "Онкомаркеры",            "parent": "ihla", "sort": 5},
    {"id": "cardio",       "name": "Кардиология (ИХЛА)",     "parent": "ihla", "sort": 6},
    {"id": "hyper",        "name": "Гипертония",             "parent": "ihla", "sort": 7},
    {"id": "torch",        "name": "TORCH-инфекции",         "parent": "ihla", "sort": 8},
    {"id": "pneum",        "name": "Пневмонии",              "parent": "ihla", "sort": 9},
    {"id": "ig",           "name": "Иммуноглобулины",        "parent": "ihla", "sort": 10},
    {"id": "anemia",       "name": "Анемия",                 "parent": "ihla", "sort": 11},
    {"id": "hep",          "name": "Гепатиты",               "parent": "ihla", "sort": 12},
    {"id": "infect",       "name": "Другие инфекции",        "parent": "ihla", "sort": 13},
    {"id": "metab",        "name": "Метаболизм",             "parent": "ihla", "sort": 14},
    {"id": "auto",         "name": "Аутоиммунная панель",    "parent": "ihla", "sort": 15},
    {"id": "diab",         "name": "Сахарный диабет",        "parent": "ihla", "sort": 16},
    {"id": "ebv",          "name": "Вирус Эпштейна-Барра",   "parent": "ihla", "sort": 17},
    {"id": "inflam",       "name": "Воспалительные процессы","parent": "ihla", "sort": 18},
    {"id": "drug",         "name": "Лекарственный мониторинг","parent": "ihla", "sort": 19},

    # Биохимия — группы
    {"id": "lipid",        "name": "Липиды",                 "parent": "biochem", "sort": 1},
    {"id": "liver",        "name": "Функции печени",         "parent": "biochem", "sort": 2},
    {"id": "diabbio",      "name": "Диабеты",                "parent": "biochem", "sort": 3},
    {"id": "kidney",       "name": "Функции почек",          "parent": "biochem", "sort": 4},
    {"id": "inorg",        "name": "Неорганические вещества","parent": "biochem", "sort": 5},
    {"id": "cardiobio",    "name": "Кардиология",            "parent": "biochem", "sort": 6},
    {"id": "panc",         "name": "Поджелудочная железа",   "parent": "biochem", "sort": 7},
    {"id": "anembio",      "name": "Анемия (биохимия)",      "parent": "biochem", "sort": 8},

    # Контроль качества
    {"id": "riqas",        "name": "ВОК RIQAS",              "parent": "qc", "sort": 1},
    {"id": "acusera",      "name": "ACUSERA (внутренний)",   "parent": "qc", "sort": 2},
]


# ─── Товары и варианты ────────────────────────────────────────────────────────
#
# Формат:
#   ("Полное название", "short_name", "category_id", "brand_code", [варианты])
# Каждый вариант:
#   {"sku": "...", "pack": "50 опред.", "price": 790720}
#   {"sku": "...", "pack": "100 опред.", "price": 1048320}
#   {"sku": "...", "pack": "...", "price": None}   ← "по запросу"

PRODUCTS = [
    # ════════════════════════════════════════════════════════════════════
    # ЩИТОВИДНАЯ ПАНЕЛЬ (ИХЛА, SNIBE)
    # ════════════════════════════════════════════════════════════════════
    ("TSH (ТТГ, 3-е поколение)", "TSH", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 790720},
        {"pack": "100 опред.", "price": 1048320},
    ]),
    ("T4 общий", "T4", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 790720},
        {"pack": "100 опред.", "price": 1048320},
    ]),
    ("T3 общий", "T3", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 790720},
        {"pack": "100 опред.", "price": 1048320},
    ]),
    ("FT4 (Свободный Т4)", "FT4", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 790720},
        {"pack": "100 опред.", "price": 1048320},
    ]),
    ("FT3 (Свободный Т3)", "FT3", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 790720},
        {"pack": "100 опред.", "price": 1048320},
    ]),
    ("TG (Тиреоглобулин)", "TG", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 1361920},
        {"pack": "100 опред.", "price": 1812160},
    ]),
    ("TGA (Антитела к Тиреоглобулину)", "Anti-Tg", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 1804320},
        {"pack": "100 опред.", "price": 2401280},
    ]),
    ("Anti-TPO (Антитела к Тиреопероксидазе)", "Anti-TPO", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 1722560},
        {"pack": "100 опред.", "price": 2302720},
    ]),
    ("TRAb (Антитела к рецепторам ТТГ)", "TRAb", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 3479840},
        {"pack": "100 опред.", "price": 4637920},
    ]),
    ("TMA (Микросомальные антитела щитовидной железы)", "TMA", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 2220400},
        {"pack": "100 опред.", "price": 2960440},
    ]),
    ("Rev T3 (Обратный трийодтиронин)", "rT3", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 3097920},
        {"pack": "100 опред.", "price": 4124960},
    ]),
    ("T-Uptake (Тироксин-связывающая способность)", "T-Uptake", "thyroid", "snibe", [
        {"pack": "50 опред.",  "price": 3063200},
        {"pack": "100 опред.", "price": 4082400},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # РЕПРОДУКТИВНАЯ ПАНЕЛЬ
    # ════════════════════════════════════════════════════════════════════
    ("FSH (Фолликулостимулирующий гормон)", "FSH", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 902720},
        {"pack": "100 опред.", "price": 1196160},
    ]),
    ("LH (Лютеинизирующий гормон)", "LH", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 902720},
        {"pack": "100 опред.", "price": 1196160},
    ]),
    ("Total β-HCG (Хорионический гонадотропин)", "β-HCG", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 924000},
        {"pack": "100 опред.", "price": 1228640},
    ]),
    ("PRL (Пролактин)", "PRL", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 924000},
        {"pack": "100 опред.", "price": 1228640},
    ]),
    ("Estradiol (Эстрадиол)", "E2", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 1061760},
        {"pack": "100 опред.", "price": 1412320},
    ]),
    ("Testosterone (Тестостерон)", "TST", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 1061760},
        {"pack": "100 опред.", "price": 1412320},
    ]),
    ("Free Testosterone (Свободный тестостерон)", "Free TST", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 1736000},
        {"pack": "100 опред.", "price": 2309440},
    ]),
    ("DHEA-S (ДГЭА-S)", "DHEA-S", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 1851360},
        {"pack": "100 опред.", "price": 2474080},
    ]),
    ("Progesterone (Прогестерон)", "PRG", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 1061760},
        {"pack": "100 опред.", "price": 1412320},
    ]),
    ("17α-OH Progesterone (17-гидроксипрогестерон)", "17OHP", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 1758400},
        {"pack": "100 опред.", "price": 2340800},
    ]),
    ("AMH (Антимюллеров гормон)", "AMH", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 8177120},
        {"pack": "100 опред.", "price": 10903200},
    ]),
    ("SHBG (Глобулин, связывающий половые гормоны)", "SHBG", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 1695680},
        {"pack": "100 опред.", "price": 2241120},
    ]),
    ("Androstenedione (Андростендион)", "ASD", "reprod", "snibe", [
        {"pack": "50 опред.",  "price": 3589600},
        {"pack": "100 опред.", "price": 4788000},
    ]),
    ("Inhibin B (Ингибин Б)", "Inhibin B", "reprod", "snibe", [
        {"pack": "100 опред.", "price": 11900000},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # ОНКОМАРКЕРЫ
    # ════════════════════════════════════════════════════════════════════
    ("AFP (Альфа-фетопротеин)", "AFP", "onco", "snibe", [
        {"pack": "50 опред.",  "price": 1126720},
        {"pack": "100 опред.", "price": 1506400},
    ]),
    ("CEA (Раково-эмбриональный антиген)", "CEA", "onco", "snibe", [
        {"pack": "50 опред.",  "price": 1126720},
        {"pack": "100 опред.", "price": 1506400},
    ]),
    ("Total PSA (Общий ПСА)", "PSA", "onco", "snibe", [
        {"pack": "50 опред.",  "price": 1863680},
        {"pack": "100 опред.", "price": 2487520},
    ]),
    ("Free PSA (Свободный ПСА)", "Free PSA", "onco", "snibe", [
        {"pack": "50 опред.",  "price": 1863680},
        {"pack": "100 опред.", "price": 2487520},
    ]),
    ("CA 125 (Онкомаркер рака яичников)", "CA 125", "onco", "snibe", [
        {"pack": "50 опред.",  "price": 1934240},
        {"pack": "100 опред.", "price": 2579360},
    ]),
    ("CA 15-3 (Онкомаркер молочной железы)", "CA 15-3", "onco", "snibe", [
        {"pack": "50 опред.",  "price": 1934240},
        {"pack": "100 опред.", "price": 2579360},
    ]),
    ("CA 19-9 (Маркер опухолей ЖКТ)", "CA 19-9", "onco", "snibe", [
        {"pack": "50 опред.",  "price": 1934240},
        {"pack": "100 опред.", "price": 2579360},
    ]),
    ("CYFRA 21-1 (Маркер плоскоклеточного рака лёгких)", "CYFRA 21-1", "onco", "snibe", [
        {"pack": "50 опред.",  "price": 3325280},
        {"pack": "100 опред.", "price": 4426240},
    ]),
    ("NSE (Маркер опухолей нейроэндокринного происхождения)", "NSE", "onco", "snibe", [
        {"pack": "50 опред.",  "price": 3604160},
        {"pack": "100 опред.", "price": 4801440},
    ]),
    ("HE-4 (Эпителиальный рак яичников)", "HE-4", "onco", "snibe", [
        {"pack": "50 опред.",  "price": 6597920},
        {"pack": "100 опред.", "price": 8805440},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # КАРДИОЛОГИЯ (ИХЛА)
    # ════════════════════════════════════════════════════════════════════
    ("CK-MB (Креатинкиназа-МВ)", "CK-MB", "cardio", "snibe", [
        {"pack": "50 опред.",  "price": 2739520},
        {"pack": "100 опред.", "price": 3645600},
    ]),
    ("Troponin I (Тропонин I)", "cTnI", "cardio", "snibe", [
        {"pack": "50 опред.",  "price": 2609600},
        {"pack": "100 опред.", "price": 3477600},
    ]),
    ("Myoglobin (Миоглобин)", "MYO", "cardio", "snibe", [
        {"pack": "50 опред.",  "price": 2744000},
        {"pack": "100 опред.", "price": 3654560},
    ]),
    ("hs-cTnI (Сверхчувствительный Тропонин I)", "hs-cTnI", "cardio", "snibe", [
        {"pack": "50 опред.",  "price": 2679040},
        {"pack": "100 опред.", "price": 3563840},
    ]),
    ("hs-CRP (Высокочувствительный C-реактивный белок)", "hs-CRP", "cardio", "snibe", [
        {"pack": "50 опред.",  "price": 2815680},
        {"pack": "100 опред.", "price": 3717280},
    ]),
    ("NT-proBNP (Мозговой натрийуретический пропептид)", "NT-proBNP", "cardio", "snibe", [
        {"pack": "50 опред.",  "price": 5256160},
        {"pack": "100 опред.", "price": 6999720},
    ]),
    ("D-Dimer (Д-димер)", "D-Dimer", "cardio", "snibe", [
        {"pack": "50 опред.",  "price": 3347680},
        {"pack": "100 опред.", "price": 4465440},
    ]),
    ("HCY (Гомоцистеин)", "HCY", "cardio", "snibe", [
        {"pack": "50 опред.",  "price": 7100800},
        {"pack": "100 опред.", "price": 9466800},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # TORCH
    # ════════════════════════════════════════════════════════════════════
    ("Toxo IgG (Антитела IgG к токсоплазме)", "Toxo IgG", "torch", "snibe", [
        {"pack": "50 опред.",  "price": 870240},
        {"pack": "100 опред.", "price": 1156960},
    ]),
    ("Toxo IgM (Антитела IgM к токсоплазме)", "Toxo IgM", "torch", "snibe", [
        {"pack": "50 опред.",  "price": 870240},
        {"pack": "100 опред.", "price": 1156960},
    ]),
    ("Rubella IgG (Антитела IgG к краснухе)", "Rubella IgG", "torch", "snibe", [
        {"pack": "50 опред.",  "price": 870240},
        {"pack": "100 опред.", "price": 1156960},
    ]),
    ("Rubella IgM (Антитела IgM к краснухе)", "Rubella IgM", "torch", "snibe", [
        {"pack": "50 опред.",  "price": 870240},
        {"pack": "100 опред.", "price": 1156960},
    ]),
    ("CMV IgG (Антитела IgG к цитомегаловирусу)", "CMV IgG", "torch", "snibe", [
        {"pack": "50 опред.",  "price": 870240},
        {"pack": "100 опред.", "price": 1156960},
    ]),
    ("CMV IgM (Антитела IgM к цитомегаловирусу)", "CMV IgM", "torch", "snibe", [
        {"pack": "50 опред.",  "price": 870240},
        {"pack": "100 опред.", "price": 1156960},
    ]),
    ("HSV-1/2 IgG (Антитела IgG к ВПГ 1/2)", "HSV-1/2 IgG", "torch", "snibe", [
        {"pack": "50 опред.",  "price": 870240},
        {"pack": "100 опред.", "price": 1156960},
    ]),
    ("HSV-1/2 IgM (Антитела IgM к ВПГ 1/2)", "HSV-1/2 IgM", "torch", "snibe", [
        {"pack": "50 опред.",  "price": 870240},
        {"pack": "100 опред.", "price": 1156960},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # ГЕПАТИТЫ
    # ════════════════════════════════════════════════════════════════════
    ("HBsAg (2 поколение)", "HBsAg", "hep", "snibe", [
        {"pack": "50 опред.",  "price": 944160},
        {"pack": "100 опред.", "price": 1256640},
    ]),
    ("Anti-HBs (Качественное определение)", "Anti-HBs", "hep", "snibe", [
        {"pack": "50 опред.",  "price": 887040},
        {"pack": "100 опред.", "price": 1179360},
    ]),
    ("HBeAg (е-антиген вируса Гепатита В)", "HBeAg", "hep", "snibe", [
        {"pack": "50 опред.",  "price": 887040},
        {"pack": "100 опред.", "price": 1179360},
    ]),
    ("Anti-HBe (Суммарные антитела к е-антигену)", "Anti-HBe", "hep", "snibe", [
        {"pack": "50 опред.",  "price": 887040},
        {"pack": "100 опред.", "price": 1179360},
    ]),
    ("Anti-HBc (Суммарные антитела к ядерному антигену)", "Anti-HBc", "hep", "snibe", [
        {"pack": "50 опред.",  "price": 887040},
        {"pack": "100 опред.", "price": 1179360},
    ]),
    ("Anti-HCV (Антитела к Гепатиту С)", "Anti-HCV", "hep", "snibe", [
        {"pack": "50 опред.",  "price": 1242080},
        {"pack": "100 опред.", "price": 1649760},
    ]),
    ("Anti-HAV (Антитела к Гепатиту А)", "Anti-HAV", "hep", "snibe", [
        {"pack": "50 опред.",  "price": 1629600},
        {"pack": "100 опред.", "price": 2172800},
    ]),
    ("HIV Ab/Ag Combi (Антитела и антиген к ВИЧ, 4 поколение)", "HIV Ab/Ag", "infect", "snibe", [
        {"pack": "100 опред.", "price": 3473120},
    ]),
    ("Syphilis (Антитела к Treponema pallidum)", "Syphilis", "infect", "snibe", [
        {"pack": "50 опред.",  "price": 2012640},
        {"pack": "100 опред.", "price": 2677920},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # АНЕМИЯ
    # ════════════════════════════════════════════════════════════════════
    ("Vitamin B12 (Витамин В12)", "B12", "anemia", "snibe", [
        {"pack": "50 опред.",  "price": 2590560},
        {"pack": "100 опред.", "price": 3398080},
    ]),
    ("Ferritin (Ферритин)", "Ferritin", "anemia", "snibe", [
        {"pack": "50 опред.",  "price": 1126720},
        {"pack": "100 опред.", "price": 1506400},
    ]),
    ("Folate (Фолиевая кислота)", "FA", "anemia", "snibe", [
        {"pack": "50 опред.",  "price": 1624000},
        {"pack": "100 опред.", "price": 2159360},
    ]),
    ("EPO (Эритропоэтин)", "EPO", "anemia", "snibe", [
        {"pack": "50 опред.",  "price": 4810400},
        {"pack": "100 опред.", "price": 6412000},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # САХАРНЫЙ ДИАБЕТ
    # ════════════════════════════════════════════════════════════════════
    ("C-Peptide (C-пептид)", "C-Peptide", "diab", "snibe", [
        {"pack": "50 опред.",  "price": 1983520},
        {"pack": "100 опред.", "price": 2639840},
    ]),
    ("Insulin (Инсулин)", "Insulin", "diab", "snibe", [
        {"pack": "50 опред.",  "price": 1983520},
        {"pack": "100 опред.", "price": 2639840},
    ]),
    ("Anti-GAD (Антитела к Глутаматдекарбоксилазе)", "Anti-GAD", "diab", "snibe", [
        {"pack": "50 опред.",  "price": 2985920},
        {"pack": "100 опред.", "price": 3980480},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # БИОХИМИЯ - Липиды
    # ════════════════════════════════════════════════════════════════════
    ("HDL-C (Холестерин ЛПВП)", "HDL-C", "lipid", "snibe", [
        {"pack": "320 тестов", "price": 865760},
    ]),
    ("LDL-C (Холестерин ЛПНП)", "LDL-C", "lipid", "snibe", [
        {"pack": "320 тестов", "price": 932120},
    ]),
    ("TC (Общий холестерин)", "TC", "lipid", "snibe", [
        {"pack": "300 тестов", "price": 67760},
    ]),
    ("TG (Триглицериды)", "TG-bio", "lipid", "snibe", [
        {"pack": "300 тестов", "price": 166880},
    ]),
    ("ApoA1 (Аполипопротеин А1)", "ApoA1", "lipid", "snibe", [
        {"pack": "170 тестов", "price": 1210720},
    ]),
    ("ApoB (Аполипопротеин В)", "ApoB", "lipid", "snibe", [
        {"pack": "190 тестов", "price": 1237040},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # БИОХИМИЯ - Функции печени
    # ════════════════════════════════════════════════════════════════════
    ("ALT (Аланинаминотрансфераза)", "ALT", "liver", "snibe", [
        {"pack": "300 тестов", "price": 134400},
    ]),
    ("AST (Аспартатаминотрансфераза)", "AST", "liver", "snibe", [
        {"pack": "300 тестов", "price": 134400},
    ]),
    ("ALP (Щелочная фосфатаза)", "ALP", "liver", "snibe", [
        {"pack": "300 тестов", "price": 134400},
    ]),
    ("GGT (Гамма-глутамилтрансфераза)", "GGT", "liver", "snibe", [
        {"pack": "300 тестов", "price": 160720},
    ]),
    ("TBIL (Общий билирубин)", "TBIL", "liver", "snibe", [
        {"pack": "300 тестов", "price": 94080},
    ]),
    ("TP (Общий белок)", "TP", "liver", "snibe", [
        {"pack": "320 тестов", "price": 67760},
    ]),
    ("ALB (Альбумин)", "ALB", "liver", "snibe", [
        {"pack": "250 тестов", "price": 67760},
    ]),
    ("CHE (Холинэстераза)", "CHE", "liver", "snibe", [
        {"pack": "190 тестов", "price": 1680000},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # БИОХИМИЯ - Диабет / Почки
    # ════════════════════════════════════════════════════════════════════
    ("GLU (Глюкоза)", "GLU", "diabbio", "snibe", [
        {"pack": "300 тестов", "price": 94080},
    ]),
    ("LAC (Молочная кислота)", "LAC", "diabbio", "snibe", [
        {"pack": "240 тестов", "price": 208040},
    ]),
    ("HBA1C (Гликированный гемоглобин)", "HBA1C", "diabbio", "snibe", [
        {"pack": "120 тестов", "price": 3261440},
    ]),
    ("Cr/Creatinine (Креатинин)", "Cr", "kidney", "snibe", [
        {"pack": "320 тестов", "price": 720160},
    ]),
    ("Uric Acid (Мочевая кислота)", "UA", "kidney", "snibe", [
        {"pack": "300 тестов", "price": 134400},
    ]),
    ("Urea (Мочевина)", "Urea", "kidney", "snibe", [
        {"pack": "300 тестов", "price": 94080},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # ГЕМАТОЛОГИЯ - реагенты DYMIND
    # ════════════════════════════════════════════════════════════════════
    ("CLE-P Cleanser (Клинзер)", "CLE-P", "hema", "dymind", [
        {"pack": "для DF50 CRP / DH26 / DH615", "price": 131440},
    ]),
    ("DIL-K Diluent (Дилюент)", "DIL-K", "hema", "dymind", [
        {"pack": "для DH26", "price": 651840},
    ]),
    ("LYK-1 Lyse (Лизирующий реагент)", "LYK-1", "hema", "dymind", [
        {"pack": "для DH26", "price": 512960},
    ]),
    ("DIL-C Diluent 20L", "DIL-C", "hema", "dymind", [
        {"pack": "20L для DF50 CRP", "price": 1026648},
    ]),
    ("LYD-1 Lyse 200ml", "LYD-1", "hema", "dymind", [
        {"pack": "200ml для DF50 CRP", "price": 301040},
    ]),
    ("LYD-2 Lyse 500ml", "LYD-2", "hema", "dymind", [
        {"pack": "500ml для DF50 CRP", "price": 719888},
    ]),
    ("CRP Reagent Kit (СРБ набор)", "CRP Kit", "hema", "dymind", [
        {"pack": "R 1x25ml + L1 1x75ml", "price": 978880},
    ]),
    ("DIL-N Diluent", "DIL-N", "hema", "dymind", [
        {"pack": "для DH-615", "price": 651840},
    ]),
    ("LYN-G Lyse", "LYN-G", "hema", "dymind", [
        {"pack": "для DH-615", "price": 554400},
    ]),
    ("LYN-D Lyse", "LYN-D", "hema", "dymind", [
        {"pack": "для DH-615", "price": 940000},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # ГЛИКИРОВАННЫЙ ГЕМОГЛОБИН (Lifotronic)
    # ════════════════════════════════════════════════════════════════════
    ("HbA1c Reagent Kit (для H8)", "HbA1c Kit H8", "hba1c", "lifotronic", [
        {"pack": "200 тестов", "price": 2500000},
    ]),
    ("Chromatographic Column (для H8)", "Column H8", "hba1c", "lifotronic", [
        {"pack": "на 1600 тестов", "price": 45950000},
    ]),
    ("HbA1c Reagent Kit (для H9)", "HbA1c Kit H9", "hba1c", "lifotronic", [
        {"pack": "400 тестов", "price": 4972096},
    ]),
    ("Chromatographic Column (для H9)", "Column H9", "hba1c", "lifotronic", [
        {"pack": "на 1600 тестов", "price": 46550000},
    ]),
    ("HbA1c Reagent Kit (для GH900p)", "HbA1c Kit GH900p", "hba1c", "lifotronic", [
        {"pack": "100 тестов", "price": 1200280},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # ГЕМОСТАЗ (Werfen / ACL TOP 350)
    # ════════════════════════════════════════════════════════════════════
    ("RecombiPlasTin 2G (ПВ, МНО)", "RecombiPlasTin", "hemos", "werfen", [
        {"pack": "935 тестов", "price": 2452661},
    ]),
    ("SynthASil (АЧТВ реагент)", "SynthASil", "hemos", "werfen", [
        {"pack": "870 тестов", "price": 1082062},
    ]),
    ("Q.F.A Thrombin 5ml (Фибриноген)", "QFA 5ml", "hemos", "werfen", [
        {"pack": "840 тестов",  "price": 10259194},
    ]),
    ("Q.F.A Thrombin 2ml (Фибриноген)", "QFA 2ml", "hemos", "werfen", [
        {"pack": "320 тестов",  "price": 5697984},
    ]),
    ("Thrombin Time (Тромбиновое время)", "TT", "hemos", "werfen", [
        {"pack": "208 тестов", "price": 911037},
    ]),
    ("Liquid Antithrombin XL (Антитромбин)", "AT XL", "hemos", "werfen", [
        {"pack": "296 тестов (4.5мл)", "price": 6296912},
    ]),
    ("D-Dimer HS500", "D-Dimer HS500", "hemos", "werfen", [
        {"pack": "120 тестов", "price": 7053271},
    ]),
    ("Protein C (Протеин С)", "Protein C", "hemos", "werfen", [
        {"pack": "74 тестов", "price": 7416138},
    ]),
    ("Free Protein S", "Free Protein S", "hemos", "werfen", [
        {"pack": "60 тестов", "price": 12506764},
    ]),
    ("Liquid Anti-Xa", "Anti-Xa", "hemos", "werfen", [
        {"pack": "130 тестов", "price": 16098265},
    ]),
    ("Homocysteine (Гомоцистеин)", "HCY-hemos", "hemos", "werfen", [
        {"pack": "48 тестов", "price": 12801326},
    ]),
    ("Cleaning Solution (Clean A)", "Clean A", "hemos", "werfen", [
        {"pack": "Раствор моющий", "price": 311078},
    ]),
    ("Cleaning Agent (Clean B)", "Clean B", "hemos", "werfen", [
        {"pack": "Агент моющий", "price": 132311},
    ]),
    ("Rinse solution 4L (Промывочный раствор)", "Rinse 4L", "hemos", "werfen", [
        {"pack": "4L", "price": 1747747},
    ]),
    ("CUVETTES (Кюветы)", "Cuvettes", "hemos", "werfen", [
        {"pack": "2400 шт", "price": 3325592},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # МИКРОБИОЛОГИЯ (BD Phoenix M50)
    # ════════════════════════════════════════════════════════════════════
    ("Panel Phoenix Yeast Id (Идентификация дрожжей)", "Yeast Id", "micro", "bd", [
        {"pack": "25 шт", "price": 2874120},
    ]),
    ("BD Phoenix Gram Negative Combo (UNMIC/ID-416)", "UNMIC/ID-416", "micro", "bd", [
        {"pack": "25 шт", "price": 5666926},
    ]),
    ("BD Phoenix Gram Positive Combo (PMIC/ID-94)", "PMIC/ID-94", "micro", "bd", [
        {"pack": "25 шт", "price": 5601077},
    ]),
    ("Panel Phoenix Nmic/Id 94", "NMIC/ID-94", "micro", "bd", [
        {"pack": "25 шт", "price": 5734555},
    ]),
    ("Panel Phoenix Smic/Id 11 (Стрептококки)", "SMIC/ID-11", "micro", "bd", [
        {"pack": "25 шт", "price": 5666926},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # АНАЛИЗ МОЧИ (URIT)
    # ════════════════════════════════════════════════════════════════════
    ("Maintenance Agent D22", "D22", "urine", "urit", [
        {"pack": "1L", "price": 1697841},
    ]),
    ("S11 Sheath", "S11", "urine", "urit", [
        {"pack": "20L", "price": 4420000},
    ]),
    ("D16 Detergent", "D16", "urine", "urit", [
        {"pack": "35ml", "price": 4420000},
    ]),
    ("D21 Detergent", "D21", "urine", "urit", [
        {"pack": "500ml", "price": 1560000},
    ]),
    ("FC23 Focus solution", "FC23", "urine", "urit", [
        {"pack": "8ml", "price": 2686500},
    ]),
    ("Strip 11FA (Тест-полоски)", "Strip 11FA", "urine", "urit", [
        {"pack": "100 шт", "price": 250000},
    ]),
    ("Strip 12FA (Тест-полоски)", "Strip 12FA", "urine", "urit", [
        {"pack": "100 шт", "price": 250000},
    ]),
    ("Strip 14FA (Тест-полоски)", "Strip 14FA", "urine", "urit", [
        {"pack": "100 шт", "price": 250000},
    ]),
    ("Пробирки для анализа мочи", "Tubes", "urine", "urit", [
        {"pack": "100 шт", "price": 203571},
    ]),
    ("UQ-14 Urine control", "UQ-14", "urine", "urit", [
        {"pack": "8ml × 3", "price": 392473},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # РАСХОДНЫЕ МАТЕРИАЛЫ ДЛЯ ИХЛА
    # ════════════════════════════════════════════════════════════════════
    ("Starter 1+2 (для M600, M800, M2000, M4000)", "Starter M-series", "consum", "snibe", [
        {"pack": "2×230 мл", "price": 696080},
    ]),
    ("Reaction Modules Кюветы (для M-серии)", "Reaction Modules", "consum", "snibe", [
        {"pack": "6×64 шт", "price": 1952720},
    ]),
    ("Промывочный концентрат", "Wash concentrate", "consum", "snibe", [
        {"pack": "1×714 мл", "price": 283360},
    ]),
    ("Оптический контроль", "Optical control", "consum", "snibe", [
        {"pack": "5×2 мл", "price": 652960},
    ]),
    ("Раствор для очистки труб", "Tube cleaner", "consum", "snibe", [
        {"pack": "1×500 мл", "price": 1114960},
    ]),
    ("Starter 1+2 для X3", "Starter X3", "consum", "snibe", [
        {"pack": "2×230 мл", "price": 696080},
    ]),
    ("Starter 1+2 (большая фасовка)", "Starter big", "consum", "snibe", [
        {"pack": "2×1.5 л", "price": 3529680},
    ]),
    ("Reaction Cup Кюветы", "Reaction Cup", "consum", "snibe", [
        {"pack": "546 шт", "price": 671440},
    ]),
    ("Наконечники (Pipette tips)", "Tips", "consum", "snibe", [
        {"pack": "20×192 шт", "price": 7210000},
    ]),

    # ════════════════════════════════════════════════════════════════════
    # КОНТРОЛИ И КАЛИБРАТОРЫ
    # ════════════════════════════════════════════════════════════════════
    ("HN 1530 lv.2 (Контроль)", "HN 1530", "acusera", "randox", [
        {"pack": "1×5ml", "price": 211400},
    ]),
    ("HE 1532 lv.3 (Контроль)", "HE 1532", "acusera", "randox", [
        {"pack": "1×5ml", "price": 239680},
    ]),
    ("CAL 2350 lv.2 (Калибратор)", "CAL 2350", "acusera", "randox", [
        {"pack": "1×5ml", "price": 354760},
    ]),
    ("CH 2673 (Калибратор)", "CH 2673", "acusera", "randox", [
        {"pack": "1×1ml", "price": 499800},
    ]),
    ("LE 2661, 2, 3 lv.1,2,3 (Контроль)", "LE 2661", "acusera", "randox", [
        {"pack": "1×3ml", "price": 371000},
    ]),
    ("CK 1212 (Контроль)", "CK 1212", "acusera", "randox", [
        {"pack": "1×2ml", "price": 659680},
    ]),
    ("CK 2393 (Калибратор)", "CK 2393", "acusera", "randox", [
        {"pack": "1×1ml", "price": 448280},
    ]),
    ("EGQ-HbA1c9 (Контроль HbA1c)", "EGQ-HbA1c9", "acusera", "randox", [
        {"pack": "(lv.1+2)×0.5ml", "price": 422800},
    ]),
    ("EGC-HbA1c9 (Калибратор HbA1c)", "EGC-HbA1c9", "acusera", "randox", [
        {"pack": "(lv.1-4)×0.5ml", "price": 636160},
    ]),
]
