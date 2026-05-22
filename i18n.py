"""
Minimal i18n helper.

Usage:
    from i18n import t
    t("menu.orders", lang="ru")                     → "📋 Мои заказы"
    t("greeting", "uz", organization_name="Hilol")  → "Salom, Hilol!"
"""
import json
import os

_LOCALES: dict[str, dict] = {}


def _load() -> None:
    base = os.path.join(os.path.dirname(__file__), "locales")
    for lang in ("ru", "uz"):
        with open(os.path.join(base, f"{lang}.json"), encoding="utf-8") as fh:
            _LOCALES[lang] = json.load(fh)


_load()


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Resolve a dot-separated key from the locale dict and interpolate kwargs."""
    data = _LOCALES.get(lang) or _LOCALES["ru"]
    node: object = data
    for part in key.split("."):
        if not isinstance(node, dict):
            return key
        node = node.get(part, key)
    if not isinstance(node, str):
        return key
    return node.format(**kwargs) if kwargs else node
