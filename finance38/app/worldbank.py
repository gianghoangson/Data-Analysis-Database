"""
World Bank Enterprise Survey data module.

Lấy dữ liệu innovation từ World Bank Enterprise Surveys:
- Index 18: R&D expenditure (% of firms)
- Index 19: Product innovation (binary/%)
- Index 20: Process innovation (binary/%)

Data source: https://www.enterprisesurveys.org/
"""

from __future__ import annotations
import pandas as pd
from typing import Dict, Optional, Any
from pathlib import Path

# World Bank Enterprise Survey URLs
WBES_CSV_URL = "https://datacatalogfiles.worldbank.org/ddh-published-v2/0037947/5/DR0094302/indicators_long_view_November_11_2024.csv"
WBES_META_XLS_URL = "https://datacatalogfiles.worldbank.org/ddh-published-v2/0037947/5/DR0094304/Indicator%20and%20Topic%20Names.xls"

# Indicator codes for Vietnam Enterprise Survey
# These codes map to our index IDs
INDICATOR_MAPPING = {
    # R&D related indicators
    'H8': 'rd_spending',           # Percent of firms spending on R&D
    'h8': 'rd_spending',
    
    # Product innovation
    'H1': 'product_innovation',    # Percent of firms that introduced a new product/service
    'h1': 'product_innovation', 
    
    # Process innovation  
    'H5': 'process_innovation',    # Percent of firms that introduced a process innovation
    'h5': 'process_innovation',
}

# Cache directory
CACHE_DIR = Path(__file__).parent.parent / 'data' / 'cache'


def load_wbes_indicators(cache_csv_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load WB Enterprise Surveys indicators (country-level, annual).
    
    Args:
        cache_csv_path: Optional path to cache CSV locally
        
    Returns:
        DataFrame with WBES indicators
    """
    if cache_csv_path is None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_csv_path = str(CACHE_DIR / 'wbes_indicators.csv')
    
    # Try cache first
    try:
        df = pd.read_csv(cache_csv_path)
        print(f"  [OK] Loaded WBES from cache: {len(df)} rows")
        return df
    except FileNotFoundError:
        pass
    
    # Download from World Bank
    print(f"  -> Downloading WBES indicators from World Bank...")
    try:
        # Try different encodings
        for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(WBES_CSV_URL, encoding=encoding)
                df.to_csv(cache_csv_path, index=False, encoding='utf-8')
                print(f"  [OK] Downloaded and cached: {len(df)} rows (encoding: {encoding})")
                return df
            except UnicodeDecodeError:
                continue
        print(f"  [WARN] Could not decode WBES CSV with any encoding")
        return pd.DataFrame()
    except Exception as e:
        print(f"  [WARN] Could not download WBES: {e}")
        return pd.DataFrame()


def load_wbes_indicator_names(cache_xls_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load indicator metadata (names, descriptions).
    """
    if cache_xls_path is None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_xls_path = str(CACHE_DIR / 'wbes_indicator_names.xlsx')
    
    try:
        return pd.read_excel(cache_xls_path)
    except FileNotFoundError:
        pass
    
    try:
        meta = pd.read_excel(WBES_META_XLS_URL)
        meta.to_excel(cache_xls_path, index=False)
        return meta
    except Exception as e:
        print(f"  [WARN] Could not download WBES metadata: {e}")
        return pd.DataFrame()


def _consider(cols_map: dict, candidates: list) -> Optional[str]:
    """Helper to find column name from candidates."""
    for k in candidates:
        if k in cols_map:
            return cols_map[k]
    return None


def get_vietnam_innovation_data(year: int) -> Dict[int, float]:
    """
    Lấy dữ liệu innovation cho Vietnam từ WBES.
    
    Args:
        year: Năm cần lấy (sẽ tìm survey gần nhất)
        
    Returns:
        Dict mapping index_id -> value:
            18: R&D expenditure (% firms)
            19: Product innovation (% firms)
            20: Process innovation (% firms)
    """
    print(f"  -> Loading World Bank Enterprise Survey data...")
    
    wbes = load_wbes_indicators()
    
    if wbes.empty:
        return {}
    
    # Normalize column names
    cols = {c.lower(): c for c in wbes.columns}
    
    # Find relevant columns
    country_col = cols.get('economy') or _consider(cols, ['country', 'economy_name', 'economyname'])
    year_col = cols.get('year') or _consider(cols, ['survey_year', 'time'])
    ind_col = cols.get('indicator') or _consider(cols, ['indicator_code', 'series', 'indcode'])
    value_col = cols.get('value') or _consider(cols, ['estimate', 'indicator_value'])
    
    if not all([country_col, year_col, ind_col, value_col]):
        print(f"  [WARN] Could not identify WBES columns")
        print(f"    Available: {list(wbes.columns)}")
        return {}
    
    # Filter for Vietnam
    df = wbes[wbes[country_col].astype(str).str.lower().str.contains('vietnam', na=False)]
    
    if df.empty:
        print(f"  [WARN] No Vietnam data in WBES")
        return {}
    
    # Find nearest survey year
    available_years = df[year_col].dropna().unique()
    print(f"    Available Vietnam survey years: {sorted(available_years)}")
    
    # Find closest year
    nearest_year = min(available_years, key=lambda y: abs(int(y) - year))
    df = df[df[year_col] == nearest_year]
    
    print(f"    Using survey year: {nearest_year} (requested: {year})")
    
    data = {}
    
    # Extract innovation indicators
    for _, row in df.iterrows():
        indicator = str(row[ind_col]).strip()
        value = row[value_col]
        
        if pd.isna(value):
            continue
        
        # R&D spending (Index 18)
        if indicator.lower() in ['h8', 'rd', 'r&d'] or 'r&d' in str(row.get('indicator_name', '')).lower():
            data[18] = float(value)
            print(f"    [OK] R&D expenditure: {value}%")
        
        # Product innovation (Index 19)
        elif indicator.lower() in ['h1'] or 'product' in str(row.get('indicator_name', '')).lower():
            data[19] = float(value)
            print(f"    [OK] Product innovation: {value}%")
        
        # Process innovation (Index 20)
        elif indicator.lower() in ['h5'] or 'process' in str(row.get('indicator_name', '')).lower():
            data[20] = float(value)
            print(f"    [OK] Process innovation: {value}%")
    
    return data


def get_innovation_by_indicator_name(year: int) -> Dict[int, float]:
    """
    Tìm innovation data bằng tên indicator thay vì code.
    """
    wbes = load_wbes_indicators()
    
    if wbes.empty:
        return {}
    
    # Find columns
    cols = {c.lower(): c for c in wbes.columns}
    country_col = cols.get('economy') or _consider(cols, ['country', 'economyname'])
    year_col = cols.get('year') or _consider(cols, ['survey_year'])
    name_col = cols.get('indicator_name') or _consider(cols, ['indicatorlabel', 'name'])
    value_col = cols.get('value') or _consider(cols, ['estimate'])
    
    if not name_col or not value_col:
        return {}
    
    # Filter Vietnam
    df = wbes[wbes[country_col].astype(str).str.lower().str.contains('vietnam', na=False)]
    
    if df.empty:
        return {}
    
    data = {}
    
    # Search by indicator name patterns
    search_patterns = {
        18: ['r&d', 'research and development', 'spending on r&d'],
        19: ['product innovation', 'introduced a new product', 'new product or service'],
        20: ['process innovation', 'introduced a process', 'new process'],
    }
    
    for idx, patterns in search_patterns.items():
        for pattern in patterns:
            matches = df[df[name_col].astype(str).str.lower().str.contains(pattern, na=False)]
            if not matches.empty:
                # Get most recent value
                if year_col:
                    matches = matches.sort_values(year_col, ascending=False)
                value = matches[value_col].iloc[0]
                if pd.notna(value):
                    data[idx] = float(value)
                    print(f"    [OK] Index {idx}: {value} (from: {matches[name_col].iloc[0][:50]})")
                    break
    
    return data


def get_all_wbes_data(year: int) -> Dict[int, float]:
    """
    Main function: lấy tất cả WBES data cho Vietnam.
    
    Args:
        year: Năm báo cáo
        
    Returns:
        Dict mapping index_id -> value
    """
    print(f"\n[WBES] Getting World Bank Enterprise Survey data...")
    
    # Try direct indicator codes first
    data = get_vietnam_innovation_data(year)
    
    # Fallback to name-based search
    if not data:
        data = get_innovation_by_indicator_name(year)
    
    if data:
        print(f"  [OK] Found {len(data)} innovation indicators from WBES")
    else:
        print(f"  [WARN] No innovation data found for Vietnam")
    
    return data


# ========================
# Test/Debug functions
# ========================

def list_vietnam_indicators():
    """List all available indicators for Vietnam."""
    wbes = load_wbes_indicators()
    
    if wbes.empty:
        return
    
    cols = {c.lower(): c for c in wbes.columns}
    country_col = cols.get('economy') or _consider(cols, ['country'])
    
    df = wbes[wbes[country_col].astype(str).str.lower().str.contains('vietnam', na=False)]
    
    print(f"\nVietnam indicators ({len(df)} rows):")
    print(f"Columns: {list(df.columns)}")
    
    # Show unique indicators
    ind_col = cols.get('indicator') or _consider(cols, ['indicator_code', 'series'])
    if ind_col:
        print(f"\nUnique indicators: {df[ind_col].nunique()}")
        print(df[ind_col].value_counts().head(20))


if __name__ == '__main__':
    # Test
    print("Testing WBES module...")
    
    # List available indicators
    list_vietnam_indicators()
    
    # Get innovation data
    data = get_all_wbes_data(2020)
    print(f"\nResult: {data}")
