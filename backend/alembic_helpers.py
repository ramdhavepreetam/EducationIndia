from __future__ import annotations

from pathlib import Path

from alembic import op


def sql_file(name: str) -> str:
    repo_root = Path(__file__).resolve().parents[1]
    return (repo_root / "database" / name).read_text(encoding="utf-8")


def execute_sql_script(sql: str) -> None:
    bind = op.get_bind()
    for statement in split_sql_statements(sql):
        bind.exec_driver_sql(statement)


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    i = 0
    quote: str | None = None
    dollar_quote: str | None = None
    line_comment = False
    block_comment = False

    while i < len(sql):
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ""

        if line_comment:
            current.append(ch)
            if ch == "\n":
                line_comment = False
            i += 1
            continue

        if block_comment:
            current.append(ch)
            if ch == "*" and nxt == "/":
                current.append(nxt)
                block_comment = False
                i += 2
            else:
                i += 1
            continue

        if dollar_quote:
            if sql.startswith(dollar_quote, i):
                current.append(dollar_quote)
                i += len(dollar_quote)
                dollar_quote = None
            else:
                current.append(ch)
                i += 1
            continue

        if quote:
            current.append(ch)
            if ch == quote:
                if nxt == quote:
                    current.append(nxt)
                    i += 2
                    continue
                quote = None
            i += 1
            continue

        if ch == "-" and nxt == "-":
            current.append(ch)
            current.append(nxt)
            line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            current.append(ch)
            current.append(nxt)
            block_comment = True
            i += 2
            continue

        if ch in ("'", '"'):
            current.append(ch)
            quote = ch
            i += 1
            continue

        if ch == "$":
            end = sql.find("$", i + 1)
            if end != -1:
                tag = sql[i : end + 1]
                if tag == "$$" or tag[1:-1].replace("_", "").isalnum():
                    current.append(tag)
                    dollar_quote = tag
                    i = end + 1
                    continue

        if ch == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements
