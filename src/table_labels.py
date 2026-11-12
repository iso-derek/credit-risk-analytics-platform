"""Readable column labels and number formats for Streamlit tables.

Display-only: the underlying data keeps its original column names, so
exports, tests and downstream code are unaffected.
"""
from __future__ import annotations

import re

import pandas as pd
import streamlit as st

ACRONYMS = {
    'id': 'ID', 'pd': 'PD', 'ead': 'EAD', 'lgd': 'LGD', 'psi': 'PSI', 'hhi': 'HHI',
    'roc': 'ROC', 'auc': 'AUC', 'pr': 'PR', 'ci': 'CI', 'usd': 'USD', 'fx': 'FX',
    'url': 'URL', 'utc': 'UTC', 'cagr': 'CAGR', 'cik': 'CIK', 'gdp': 'GDP', 'cpi': 'CPI',
    'eps': 'EPS', 'qa': 'QA', 'api': 'API', 'etf': 'ETF', 'ttm': 'TTM', 'pnl': 'P&L',
}
PERCENT_WORDS = {'rate', 'share', 'probability', 'pd', 'weight', 'contribution', 'precision', 'return'}
MONEY_WORDS = {'ead', 'loss', 'exposure', 'amount', 'spend', 'usd', 'income', 'balance', 'pnl'}


def readable(name: object) -> object:
    """Turn ``snake_case`` into a sentence-case label; leave readable names alone."""
    if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9_]+', name):
        return name
    words = [ACRONYMS.get(word, word) for word in name.split('_') if word]
    if not words:
        return name
    text = ' '.join(words)
    return text[0].upper() + text[1:]


def _words(name: str) -> set[str]:
    return set(name.lower().split('_'))


def _number_format(name: str) -> str | None:
    words = _words(name)
    if words & {'zscore', 'score', 'per', 'bps', 'pct', 'percent'}:
        return None  # scores, ratios per unit and values already in percent or bps
    if words & PERCENT_WORDS:
        return 'percent'
    if words & MONEY_WORDS:
        return 'accounting'
    return None


def table_config(data, overrides: dict | None = None, index_label: str | None = None) -> dict:
    """Build a ``column_config`` that labels every column readably.

    ``overrides`` entries win; if one has no label, the readable label is added.
    Styler inputs keep their own number formatting and only receive labels.
    """
    styled = not isinstance(data, pd.DataFrame) and isinstance(getattr(data, 'data', None), pd.DataFrame)
    frame = data.data if styled else data
    overrides = dict(overrides or {})
    if not isinstance(frame, pd.DataFrame):
        return overrides
    config: dict = {}
    for column in frame.columns:
        if not isinstance(column, (str, int)):
            continue
        label = readable(column)
        if column in overrides:
            entry = overrides.pop(column)
            if entry is not None and not isinstance(entry, str):
                entry = dict(entry)
                if not entry.get('label'):
                    entry['label'] = label
            config[column] = entry
            continue
        number_format = None if styled or not isinstance(column, str) else _number_format(column)
        if number_format and pd.api.types.is_numeric_dtype(frame[column]) and not pd.api.types.is_bool_dtype(frame[column]):
            config[column] = st.column_config.NumberColumn(label, format=number_format)
        elif label != column:
            config[column] = st.column_config.Column(label)
    if index_label:
        config['_index'] = st.column_config.Column(index_label)
    config.update(overrides)
    return config
