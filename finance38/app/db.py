"""
Database module cho finance38
- Connect SQLite
- Init schema
- Upsert data
- Export panel data
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Any
import pandas as pd
from contextlib import contextmanager


class Database:
    """SQLite database wrapper cho finance38"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Khởi tạo database connection.
        
        Args:
            db_path: Đường dẫn đến file SQLite (mặc định: data/processed/finance38.sqlite)
        """
        if db_path is None:
            root = Path(__file__).parent.parent
            db_path = root / 'data' / 'processed' / 'finance38.sqlite'
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    @contextmanager
    def get_connection(self):
        """Context manager cho database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_schema(self, schema_path: Optional[Path] = None):
        """
        Khởi tạo database schema từ file SQL.
        
        Args:
            schema_path: Đường dẫn file schema (mặc định: db/schema_sqlite.sql)
        """
        if schema_path is None:
            root = Path(__file__).parent.parent
            schema_path = root / 'db' / 'schema_sqlite.sql'
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file không tồn tại: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
        
        print(f"[OK] Da khoi tao schema tai: {self.db_path}")
    
    def upsert_value(
        self,
        company_code: str,
        year: int,
        index_id: int,
        index_name: str,
        value: Optional[float],
        unit: str = 'VND',
        source: str = 'pdf'
    ):
        """
        Insert hoặc update một giá trị chỉ số.
        
        Args:
            company_code: Mã công ty
            year: Năm báo cáo
            index_id: ID chỉ số (1-38)
            index_name: Tên chỉ số
            value: Giá trị
            unit: Đơn vị
            source: Nguồn dữ liệu (pdf, yahoo, computed, manual)
        """
        sql = """
        INSERT INTO finance_data (company_code, year, index_id, index_name, value, unit, source, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(company_code, year, index_id) DO UPDATE SET
            value = excluded.value,
            unit = excluded.unit,
            source = excluded.source,
            updated_at = CURRENT_TIMESTAMP
        """
        
        with self.get_connection() as conn:
            conn.execute(sql, (company_code, year, index_id, index_name, value, unit, source))
    
    def upsert_batch(self, records: List[Dict[str, Any]]):
        """
        Upsert nhiều bản ghi cùng lúc.
        
        Args:
            records: List các dict với keys: company_code, year, index_id, index_name, value, unit, source
        """
        sql = """
        INSERT INTO finance_data (company_code, year, index_id, index_name, value, unit, source, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(company_code, year, index_id) DO UPDATE SET
            value = excluded.value,
            unit = excluded.unit,
            source = excluded.source,
            updated_at = CURRENT_TIMESTAMP
        """
        
        with self.get_connection() as conn:
            for record in records:
                conn.execute(sql, (
                    record['company_code'],
                    record['year'],
                    record['index_id'],
                    record['index_name'],
                    record.get('value'),
                    record.get('unit', 'VND'),
                    record.get('source', 'pdf')
                ))
        
        print(f"[OK] Da upsert {len(records)} ban ghi")
    
    def add_company(
        self,
        company_code: str,
        company_name: Optional[str] = None,
        founding_year: Optional[int] = None,
        industry: Optional[str] = None,
        exchange: str = 'HSX'
    ):
        """
        Thêm hoặc update thông tin công ty.
        """
        sql = """
        INSERT INTO companies (company_code, company_name, founding_year, industry, exchange)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(company_code) DO UPDATE SET
            company_name = COALESCE(excluded.company_name, companies.company_name),
            founding_year = COALESCE(excluded.founding_year, companies.founding_year),
            industry = COALESCE(excluded.industry, companies.industry),
            exchange = COALESCE(excluded.exchange, companies.exchange)
        """
        
        with self.get_connection() as conn:
            conn.execute(sql, (company_code, company_name, founding_year, industry, exchange))
    
    def log_processing(
        self,
        company_code: str,
        year: int,
        pdf_filename: str,
        status: str,
        extracted_count: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Ghi log xử lý PDF.
        """
        sql = """
        INSERT INTO processing_log (company_code, year, pdf_filename, status, extracted_count, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        with self.get_connection() as conn:
            conn.execute(sql, (company_code, year, pdf_filename, status, extracted_count, error_message))
    
    def get_company_data(self, company_code: str,  year: Optional[int] = None) -> pd.DataFrame:
        """
        Lấy dữ liệu của một công ty.
        
        Args:
            company_code: Mã công ty
            year: Năm (None = tất cả các năm)
            
        Returns:
            DataFrame với các cột: year, index_id, index_name, value, unit, source
        """
        sql = """
        SELECT year, index_id, index_name, value, unit, source
        FROM finance_data
        WHERE company_code = ?
        """
        params = [company_code]
        
        if year is not None:
            sql += " AND year = ?"
            params.append(year)
        
        sql += " ORDER BY year, index_id"
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(sql, conn, params=params)
        
        return df
    
    def get_panel_wide(self) -> pd.DataFrame:
        """
        Xuất dữ liệu panel dạng wide format.
        
        Returns:
            DataFrame với các cột: company_code, year, [38 index columns]
        """
        sql = """
        SELECT company_code, year, index_id, value
        FROM finance_data
        ORDER BY company_code, year, index_id
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(sql, conn)
        
        if df.empty:
            return df
        
        # Pivot to wide format
        df_wide = df.pivot_table(
            index=['company_code', 'year'],
            columns='index_id',
            values='value',
            aggfunc='first'
        ).reset_index()
        
        # Rename columns
        df_wide.columns.name = None
        
        return df_wide
    
    def get_panel_long(self) -> pd.DataFrame:
        """
        Xuất dữ liệu panel dạng long format.
        
        Returns:
            DataFrame với các cột: company_code, year, index_id, index_name, value, unit
        """
        sql = """
        SELECT company_code, year, index_id, index_name, value, unit, source
        FROM finance_data
        ORDER BY company_code, year, index_id
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(sql, conn)
        
        return df
    
    def export_panel_csv(self, output_path: Optional[Path] = None, format: str = 'long'):
        """
        Xuất panel data ra CSV.
        
        Args:
            output_path: Đường dẫn file output (mặc định: data/processed/panel_long.csv)
            format: 'long' hoặc 'wide'
        """
        if output_path is None:
            root = Path(__file__).parent.parent
            output_path = root / 'data' / 'processed' / f'panel_{format}.csv'
        
        if format == 'wide':
            df = self.get_panel_wide()
        else:
            df = self.get_panel_long()
        
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✓ Đã xuất {len(df)} dòng ra: {output_path}")
        
        return output_path
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Lấy thống kê database.
        
        Returns:
            Dict chứa các thống kê
        """
        with self.get_connection() as conn:
            # Số công ty
            n_companies = conn.execute(
                "SELECT COUNT(DISTINCT company_code) FROM finance_data"
            ).fetchone()[0]
            
            # Số năm
            years = conn.execute(
                "SELECT MIN(year), MAX(year) FROM finance_data"
            ).fetchone()
            
            # Số bản ghi
            n_records = conn.execute(
                "SELECT COUNT(*) FROM finance_data"
            ).fetchone()[0]
            
            # Completeness by index
            completeness = conn.execute("""
                SELECT index_id, index_name, 
                       COUNT(value) as filled,
                       COUNT(*) as total
                FROM finance_data
                GROUP BY index_id, index_name
                ORDER BY index_id
            """).fetchall()
        
        return {
            'n_companies': n_companies,
            'year_range': (years[0], years[1]) if years[0] else (None, None),
            'n_records': n_records,
            'completeness': [dict(row) for row in completeness]
        }


# Singleton instance
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """Lấy database instance (singleton)."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def init_database():
    """Khởi tạo database với schema mặc định."""
    db = get_db()
    db.init_schema()
    return db
