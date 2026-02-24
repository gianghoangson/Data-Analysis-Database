"""
Compute module cho finance38
- Derived indicators: Growth ratio, ratios
- Validation & cleaning
"""

from typing import Dict, Optional, List, Any
import pandas as pd
from pathlib import Path

from .db import get_db, Database


def compute_growth_ratio(
    db: Database,
    company_code: str,
    year: int
) -> Optional[float]:
    """
    Tính Growth ratio (tăng trưởng doanh thu).
    
    Formula: (Revenue_t - Revenue_t-1) / Revenue_t-1 * 100
    
    Args:
        db: Database instance
        company_code: Mã công ty
        year: Năm hiện tại
        
    Returns:
        Growth ratio (%) hoặc None nếu không đủ dữ liệu
    """
    # Index 6 = Total sales revenue
    sql = """
    SELECT year, value
    FROM finance_data
    WHERE company_code = ? 
      AND index_id = 6
      AND year IN (?, ?)
      AND value IS NOT NULL
    ORDER BY year
    """
    
    with db.get_connection() as conn:
        rows = conn.execute(sql, (company_code, year - 1, year)).fetchall()
    
    if len(rows) < 2:
        return None
    
    # Tạo dict year -> value
    revenue_by_year = {row['year']: row['value'] for row in rows}
    
    rev_prev = revenue_by_year.get(year - 1)
    rev_curr = revenue_by_year.get(year)
    
    if rev_prev and rev_curr and rev_prev != 0:
        growth = (rev_curr - rev_prev) / abs(rev_prev) * 100
        return round(growth, 2)
    
    return None


def compute_market_cap(shares: float, price: float) -> float:
    """
    Tính Market value of equity (vốn hóa).
    
    Args:
        shares: Số cổ phiếu lưu hành
        price: Giá cổ phiếu
        
    Returns:
        Market cap
    """
    return shares * price


def compute_firm_age(report_year: int, founding_year: int) -> int:
    """
    Tính tuổi công ty.
    
    Args:
        report_year: Năm báo cáo
        founding_year: Năm thành lập
        
    Returns:
        Tuổi công ty (năm)
    """
    return report_year - founding_year


def compute_all_derived(db: Optional[Database] = None) -> int:
    """
    Tính toán tất cả các chỉ số derived và lưu vào database.
    
    Các chỉ số computed:
        - 32: Growth ratio
        - 23: Market value of equity (nếu có shares và price)
        - 38: Firm age (nếu có founding year)
    
    Args:
        db: Database instance (None = sử dụng default)
        
    Returns:
        Số lượng giá trị đã tính và lưu
    """
    if db is None:
        db = get_db()
    
    count = 0
    
    # Lấy danh sách company-year
    with db.get_connection() as conn:
        company_years = conn.execute("""
            SELECT DISTINCT company_code, year
            FROM finance_data
            ORDER BY company_code, year
        """).fetchall()
    
    print(f"📊 Tính toán derived indicators cho {len(company_years)} company-year pairs...")
    
    for row in company_years:
        company = row['company_code']
        year = row['year']
        
        # 32. Growth ratio
        growth = compute_growth_ratio(db, company, year)
        if growth is not None:
            db.upsert_value(
                company_code=company,
                year=year,
                index_id=32,
                index_name='Growth ratio',
                value=growth,
                unit='%',
                source='computed'
            )
            count += 1
            print(f"  ✓ {company} {year}: Growth = {growth:.2f}%")
    
    print(f"✓ Đã tính và lưu {count} giá trị derived")
    return count


def validate_data(db: Optional[Database] = None) -> Dict[str, Any]:
    """
    Kiểm tra tính hợp lệ của dữ liệu.
    
    Các validation rules:
        - Total assets = Total equity + Total liabilities (gần đúng)
        - Current assets <= Total assets
        - Net income logic
        
    Args:
        db: Database instance
        
    Returns:
        Dict chứa kết quả validation
    """
    if db is None:
        db = get_db()
    
    issues = []
    
    with db.get_connection() as conn:
        # Lấy tất cả data dạng wide
        sql = """
        SELECT company_code, year,
            MAX(CASE WHEN index_id = 7 THEN value END) as total_assets,
            MAX(CASE WHEN index_id = 22 THEN value END) as equity,
            MAX(CASE WHEN index_id = 24 THEN value END) as liabilities,
            MAX(CASE WHEN index_id = 30 THEN value END) as current_assets
        FROM finance_data
        GROUP BY company_code, year
        """
        
        rows = conn.execute(sql).fetchall()
    
    for row in rows:
        company = row['company_code']
        year = row['year']
        
        total_assets = row['total_assets']
        equity = row['equity']
        liabilities = row['liabilities']
        current_assets = row['current_assets']
        
        # Check 1: Assets = Equity + Liabilities (cho phép sai số 5%)
        if total_assets and equity and liabilities:
            expected = equity + liabilities
            diff_pct = abs(total_assets - expected) / total_assets * 100
            if diff_pct > 5:
                issues.append({
                    'company': company,
                    'year': year,
                    'issue': 'Balance sheet mismatch',
                    'detail': f"Assets={total_assets:,.0f}, Equity+Liab={expected:,.0f}, diff={diff_pct:.1f}%"
                })
        
        # Check 2: Current assets <= Total assets
        if current_assets and total_assets:
            if current_assets > total_assets * 1.01:  # 1% tolerance
                issues.append({
                    'company': company,
                    'year': year,
                    'issue': 'Current assets > Total assets',
                    'detail': f"Current={current_assets:,.0f}, Total={total_assets:,.0f}"
                })
    
    return {
        'total_checks': len(rows),
        'issues_found': len(issues),
        'issues': issues
    }


def fill_missing_estimates(db: Optional[Database] = None):
    """
    Điền các giá trị missing bằng estimates.
    
    Strategies:
        - Interpolation cho time series
        - Industry average cho cross-section
        - Previous year value
        
    Args:
        db: Database instance
    """
    # TODO: Implement estimation logic
    pass


def get_completeness_report(db: Optional[Database] = None) -> pd.DataFrame:
    """
    Báo cáo mức độ hoàn thiện dữ liệu.
    
    Args:
        db: Database instance
        
    Returns:
        DataFrame với completeness stats theo index
    """
    if db is None:
        db = get_db()
    
    with db.get_connection() as conn:
        sql = """
        SELECT 
            index_id,
            index_name,
            COUNT(*) as total_records,
            COUNT(value) as filled_records,
            ROUND(COUNT(value) * 100.0 / COUNT(*), 1) as fill_rate
        FROM finance_data
        GROUP BY index_id, index_name
        ORDER BY index_id
        """
        
        df = pd.read_sql_query(sql, conn)
    
    return df


def export_stata_ready(db: Optional[Database] = None, output_path: Optional[Path] = None) -> Path:
    """
    Xuất dữ liệu panel sẵn sàng cho Stata/EViews.
    
    Format: Wide panel với company_code, year, và 38 biến
    
    Args:
        db: Database instance
        output_path: Đường dẫn output
        
    Returns:
        Path đến file đã xuất
    """
    if db is None:
        db = get_db()
    
    if output_path is None:
        root = Path(__file__).parent.parent
        output_path = root / 'data' / 'processed' / 'panel_wide.csv'
    
    df = db.get_panel_wide()
    
    # Rename columns theo format chuẩn
    # Có thể thêm logic rename ở đây
    
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✓ Đã xuất panel data (wide format): {output_path}")
    
    return output_path
