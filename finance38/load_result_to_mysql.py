#!/usr/bin/env python3
"""Load all CSV files from finance38/data/result into normalized MySQL schema.

Usage:
  python finance38/load_result_to_mysql.py --host 127.0.0.1 --user root --password 123456 --database finance38_result
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

# Try pymysql first (lighter weight), fallback to mysql-connector-python
try:
    import pymysql
    import pymysql.cursors as cursors
    DRIVER = "pymysql"
except ImportError:
    import mysql.connector
    DRIVER = "mysql-connector-python"


FILENAME_RE = re.compile(r"^(?P<company>[A-Z0-9]+)_(?P<year>\d{4})_result\.csv$")


@dataclass
class LoadStats:
    files: int = 0
    companies_inserted: int = 0
    indices_inserted: int = 0
    data_inserted_or_updated: int = 0
    skipped_rows: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", default="localhost", help="MySQL host")
    parser.add_argument("--port", type=int, default=3306, help="MySQL port")
    parser.add_argument("--user", default="root", help="MySQL user")
    parser.add_argument("--password", default="", help="MySQL password")
    parser.add_argument("--database", default="finance38_result", help="Database name")
    parser.add_argument(
        "--result-dir",
        default="data/result",
        help="Directory with *_result.csv files",
    )
    parser.add_argument(
        "--schema-path",
        default="db/schema_mysql_result.sql",
        help="Path to SQL schema file",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate tables before loading",
    )
    return parser.parse_args()


def parse_numeric(value_raw: Optional[str]) -> Optional[float]:
    """Parse a numeric value, handling various formats."""
    if not value_raw or not isinstance(value_raw, str):
        return None

    value_raw = value_raw.strip()
    if not value_raw:
        return None

    # Remove common separators and special characters
    cleaned = value_raw.replace(",", ".").replace(" ", "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def iter_result_files(result_dir: Path) -> list[Path]:
    """Find all *_result.csv files in the result directory."""
    files = sorted(result_dir.glob("*_result.csv"))
    return [path for path in files if FILENAME_RE.match(path.name)]


def run_schema(cursor: Any, schema_path: Path) -> None:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    sql_text = schema_path.read_text(encoding="utf-8")
    cleaned_lines: list[str] = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("--"):
            cleaned_lines.append(stripped)

    sql_statements = " ".join(cleaned_lines).split(";")
    for statement in sql_statements:
        statement = statement.strip()
        if statement:
            cursor.execute(statement)


def upsert_company(cursor: Any, company_code: str) -> bool:
    """Returns True if this is a new company (first time seeing it)."""
    # Check if company already exists
    check_sql = "SELECT COUNT(*) FROM companies WHERE company_code = %s"
    cursor.execute(check_sql, (company_code,))
    exists = cursor.fetchone()[0] > 0

    if not exists:
        sql = """
            INSERT INTO companies (company_code)
            VALUES (%s)
        """
        cursor.execute(sql, (company_code,))
    return not exists


def upsert_index(
    cursor: Any,
    index_id: int,
    index_name: str,
    name_vn: Optional[str],
    unit: Optional[str],
) -> bool:
    """Returns True if this is a new index (first time seeing it)."""
    # Check if index already exists
    check_sql = "SELECT COUNT(*) FROM indices WHERE index_id = %s"
    cursor.execute(check_sql, (index_id,))
    exists = cursor.fetchone()[0] > 0

    if not exists:
        sql = """
            INSERT INTO indices (index_id, index_name, name_vn, unit)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (index_id, index_name, name_vn, unit))
    else:
        sql = """
            UPDATE indices
            SET index_name = %s,
                name_vn = COALESCE(%s, name_vn),
                unit = COALESCE(%s, unit)
            WHERE index_id = %s
        """
        cursor.execute(sql, (index_name, name_vn, unit, index_id))

    return not exists


def upsert_data(
    cursor: Any,
    company_code: str,
    year: int,
    index_id: int,
    value_raw: Optional[str],
    value_num: Optional[float],
    source: Optional[str],
) -> None:
    sql = """
        INSERT INTO financial_data (company_code, year, index_id, value_raw, value_num, source, loaded_at)
        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE
            value_raw = VALUES(value_raw),
            value_num = VALUES(value_num),
            source = VALUES(source),
            loaded_at = CURRENT_TIMESTAMP
    """
    cursor.execute(sql, (company_code, year, index_id, value_raw, value_num, source))


def load_file(
    cursor: Any, csv_path: Path, stats: LoadStats
) -> None:
    match = FILENAME_RE.match(csv_path.name)
    if not match:
        return

    company_code = match.group("company")
    year = int(match.group("year"))

    # Upsert company (track only new companies)
    if upsert_company(cursor, company_code):
        stats.companies_inserted += 1

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                index_id_raw = (row.get("index_id") or "").strip()
                index_name = (row.get("index_name") or "").strip()
                if not index_id_raw or not index_name:
                    stats.skipped_rows += 1
                    continue

                index_id = int(index_id_raw)
                name_vn = (row.get("name_vn") or "").strip() or None
                value_raw = row.get("value")
                value_num = parse_numeric(value_raw)
                unit = (row.get("unit") or "").strip() or None
                source = (row.get("source") or "").strip() or None

                # Upsert index reference (track only new indices)
                if upsert_index(cursor, index_id, index_name, name_vn, unit):
                    stats.indices_inserted += 1

                # Upsert financial data
                upsert_data(cursor, company_code, year, index_id, value_raw, value_num, source)
                stats.data_inserted_or_updated += 1

            except (ValueError, TypeError):
                stats.skipped_rows += 1


def main() -> None:
    args = parse_args()

    result_dir = Path(args.result_dir).resolve()
    db_path = Path(args.schema_path).resolve()

    if not result_dir.exists():
        raise SystemExit(
            f"Result directory not found: {result_dir} (cwd={Path.cwd()})"
        )

    files = iter_result_files(result_dir)
    if not files:
        raise SystemExit(f"No *_result.csv files found in: {result_dir}")

    stats = LoadStats()

    conn = None
    try:
        if DRIVER == "pymysql":
            conn = pymysql.connect(
                host=args.host,
                port=args.port,
                user=args.user,
                password=args.password,
                database=args.database,
                autocommit=False,
                charset="utf8mb4",
                connect_timeout=5
            )
        else:
            conn = mysql.connector.connect(
                host=args.host,
                port=args.port,
                user=args.user,
                password=args.password,
                database=args.database,
                autocommit=False,
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
                connection_timeout=5,
                protocol='TCP'
            )
    except Exception as e:
        # Retry without database first, then create schema
        try:
            if DRIVER == "pymysql":
                conn = pymysql.connect(
                    host=args.host,
                    port=args.port,
                    user=args.user,
                    password=args.password,
                    autocommit=False,
                    charset="utf8mb4",
                    connect_timeout=5
                )
            else:
                conn = mysql.connector.connect(
                    host=args.host,
                    port=args.port,
                    user=args.user,
                    password=args.password,
                    autocommit=False,
                    charset="utf8mb4",
                    collation="utf8mb4_unicode_ci",
                    connection_timeout=5,
                    protocol='TCP'
                )
        except Exception:
            raise SystemExit(f"Cannot connect to MySQL {args.host}:{args.port} - {e}")

    try:
        cursor = conn.cursor()
        run_schema(cursor, db_path)
        cursor.execute(f"USE `{args.database}`")

        if args.truncate:
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")
            cursor.execute("TRUNCATE TABLE financial_data")
            cursor.execute("TRUNCATE TABLE indices")
            cursor.execute("TRUNCATE TABLE companies")
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")

        for csv_path in files:
            load_file(cursor, csv_path, stats)
            stats.files += 1

        conn.commit()
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            conn.close()

    print("[OK] Finished loading result CSV files to MySQL")
    print(f"  - Files processed: {stats.files}")
    print(f"  - Companies inserted: {stats.companies_inserted}")
    print(f"  - Indices inserted: {stats.indices_inserted}")
    print(f"  - Data rows inserted/updated: {stats.data_inserted_or_updated}")
    print(f"  - Rows skipped: {stats.skipped_rows}")
    print(f"  - Database: {args.database}")


if __name__ == "__main__":
    main()
