from __future__ import annotations

import re

import polars as pl


def human_only(df: pl.DataFrame, organism_column: str = "organism") -> pl.DataFrame:
    return df.filter(pl.col(organism_column).str.contains("Homo sapiens", literal=True))


def reviewed_only(df: pl.DataFrame, reviewed_column: str = "reviewed") -> pl.DataFrame:
    return df.filter(pl.col(reviewed_column).fill_null(False))


def score_threshold(df: pl.DataFrame, score_column: str, threshold: int) -> pl.DataFrame:
    return df.filter(pl.col(score_column) >= threshold)


def year_at_least(df: pl.DataFrame, year_column: str, minimum: int) -> pl.DataFrame:
    return df.filter(pl.col(year_column).is_null() | (pl.col(year_column) >= minimum))


def contains_any_term(df: pl.DataFrame, columns: list[str], terms: list[str]) -> pl.DataFrame:
    if not terms:
        return df
    expr = None
    for chunk_start in range(0, len(terms), 200):
        chunk = [term for term in terms[chunk_start : chunk_start + 200] if term]
        if not chunk:
            continue
        pattern = "|".join(re.escape(term) for term in chunk)
        chunk_expr = None
        for column in columns:
            condition = pl.col(column).fill_null("").str.contains(pattern, literal=False)
            chunk_expr = condition if chunk_expr is None else (chunk_expr | condition)
        expr = chunk_expr if expr is None else (expr | chunk_expr)
    return df.filter(expr if expr is not None else pl.lit(True))
