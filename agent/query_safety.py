import re

BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "ALTER", "DROP", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "ATTACH", "DETACH",
    "RENAME", "OPTIMIZE", "KILL", "SET",
]

ALLOWED_TABLES = {
    "dailies.titles",
    "dailies.viewing_events",
    "dailies.engagement_events",
    "dailies.social_signals",
    "dailies.baseline_pacing",
    "titles", "viewing_events", "engagement_events",
    "social_signals", "baseline_pacing",
}

TABLE_REF_PATTERN = re.compile(
    r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)",
    re.IGNORECASE,
)


CTE_NAME_PATTERN = re.compile(
    r"\b(?:WITH|,)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\(",
    re.IGNORECASE,
)


def extract_table_references(sql: str) -> set[str]:
    return {m.lower() for m in TABLE_REF_PATTERN.findall(sql)}


def extract_cte_names(sql: str) -> set[str]:
    """CTE names (WITH x AS (...), y AS (...)) are query-local aliases, not
    real tables -- they must be excluded from the table allowlist check."""
    return {m.lower() for m in CTE_NAME_PATTERN.findall(sql)}


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Returns (is_valid, reason). reason is 'ok' when valid, otherwise a
    human-readable rejection explanation (safe to surface back to the LLM
    step so it can revise its proposed query).
    """
    if not sql or not sql.strip():
        return False, "Empty query."

    stripped = sql.strip().rstrip(";").strip()

    if ";" in stripped:
        return False, "Multiple statements are not permitted."

    first_word = stripped.split(None, 1)[0].upper() if stripped.split(None, 1) else ""
    if first_word not in ("SELECT", "WITH"):
        return False, "Only SELECT/WITH queries are permitted."

    upper = stripped.upper()
    for kw in BLOCKED_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            return False, f"Query contains disallowed keyword: {kw}"

    if "system." in stripped.lower() or "information_schema" in stripped.lower():
        return False, "Access to system tables is not permitted."

    referenced = extract_table_references(stripped)
    cte_names = extract_cte_names(stripped)
    referenced -= cte_names
    if referenced and not referenced.issubset(ALLOWED_TABLES):
        disallowed = referenced - ALLOWED_TABLES
        return False, f"Query references tables outside the allowed dataset: {disallowed}"

    return True, "ok"


def enforce_limit(sql: str, default_limit: int = 500) -> str:
    """
    Appends a LIMIT clause to queries that don't have one and aren't
    aggregate-only (GROUP BY queries are generally already bounded in row
    count and don't need a row cap).
    """
    if re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
        return sql
    if re.search(r"\bGROUP BY\b", sql, re.IGNORECASE):
        return sql
    return f"{sql.rstrip(';').rstrip()} LIMIT {default_limit}"
