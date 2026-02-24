"""
External data module cho finance38
- Yahoo Finance: Market cap, shares outstanding, price
- CafeF: Ownership structure, employee count, founding year
- Vietstock: Ownership data
- Firm age
"""

from typing import Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import re
import time

from .utils import get_founding_year


# ========================
# CafeF Scraper
# ========================

def scrape_cafef_profile(company_code: str) -> Dict[str, Any]:
    """
    Scrape company profile từ CafeF.
    
    URL: https://cafef.vn/du-lieu/hose/{code}-ten-cong-ty.chn
    
    Returns:
        Dict với keys: founding_year, employees, foreign_ownership, state_ownership, etc.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("  [WARN] Cần: pip install requests beautifulsoup4")
        return {}
    
    # CafeF URL pattern
    base_url = f"https://cafef.vn/du-lieu/ajax/pagenew/DataCompany/profile.ashx?symbol={company_code}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/html, */*',
        'Referer': f'https://cafef.vn/du-lieu/hose/{company_code.lower()}.chn'
    }
    
    data = {}
    
    try:
        # Get profile page
        profile_url = f"https://cafef.vn/du-lieu/hose/{company_code.lower()}.chn"
        
        resp = requests.get(profile_url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        
        if resp.status_code != 200:
            print(f"  [WARN] CafeF returned {resp.status_code}")
            return {}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Parse thông tin cơ bản
        # Tìm bảng thông tin công ty
        info_table = soup.find('table', class_='dInfo')
        if info_table:
            rows = info_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if 'năm thành lập' in label or 'thành lập' in label:
                        match = re.search(r'(\d{4})', value)
                        if match:
                            data['founding_year'] = int(match.group(1))
                    
                    elif 'nhân viên' in label or 'lao động' in label:
                        match = re.search(r'[\d,\.]+', value.replace(',', ''))
                        if match:
                            data['employees'] = int(float(match.group().replace('.', '')))
        
        # Parse ownership structure
        ownership_section = soup.find('div', id='divOwnerStructure') or soup.find('div', class_='owner-structure')
        if ownership_section:
            text = ownership_section.get_text()
            
            # Foreign ownership
            match = re.search(r'(?:nước ngoài|foreign)[^\d]*(\d+[,.]?\d*)\s*%', text, re.IGNORECASE)
            if match:
                data['foreign_ownership'] = float(match.group(1).replace(',', '.'))
            
            # State ownership
            match = re.search(r'(?:nhà nước|state)[^\d]*(\d+[,.]?\d*)\s*%', text, re.IGNORECASE)
            if match:
                data['state_ownership'] = float(match.group(1).replace(',', '.'))
        
        # Try alternative: ownership from summary box
        summary_box = soup.find('div', class_='summary') or soup.find('div', id='pnCompanyInfo')
        if summary_box:
            text = summary_box.get_text()
            
            if 'foreign_ownership' not in data:
                match = re.search(r'(?:SHNN|Sở hữu NN|Foreign)[:\s]*(\d+[,.]?\d*)\s*%', text)
                if match:
                    data['foreign_ownership'] = float(match.group(1).replace(',', '.'))
        
    except Exception as e:
        print(f"  [WARN] CafeF error: {e}")
    
    return data


def scrape_cafef_ownership(company_code: str) -> Dict[str, float]:
    """
    Scrape cơ cấu cổ đông từ CafeF.
    
    URL: https://cafef.vn/du-lieu/hose/{code}-ten.chn#owner
    
    Returns:
        Dict với: state_pct, foreign_pct, institutional_pct, insider_pct
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return {}
    
    # Try API endpoint for ownership
    api_url = f"https://cafef.vn/du-lieu/ajax/pagenew/DataCompany/ownerstructure.ashx?symbol={company_code}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'https://cafef.vn/du-lieu/hose/{company_code.lower()}.chn'
    }
    
    data = {}
    
    try:
        resp = requests.get(api_url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Parse ownership table
            rows = soup.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value_text = cells[-1].get_text(strip=True)
                    
                    # Extract percentage
                    match = re.search(r'(\d+[,.]?\d*)', value_text)
                    if match:
                        pct = float(match.group(1).replace(',', '.'))
                        
                        if 'nhà nước' in label or 'state' in label:
                            data['state_pct'] = pct
                        elif 'nước ngoài' in label or 'foreign' in label:
                            data['foreign_pct'] = pct
                        elif 'tổ chức' in label or 'institution' in label:
                            data['institutional_pct'] = pct
                        elif 'nội bộ' in label or 'insider' in label or 'ban điều hành' in label:
                            data['insider_pct'] = pct
    
    except Exception as e:
        print(f"  [WARN] CafeF ownership error: {e}")
    
    return data


# ========================
# Vietstock Scraper
# ========================

def scrape_vietstock_profile(company_code: str) -> Dict[str, Any]:
    """
    Scrape company profile từ Vietstock.
    
    URL: https://finance.vietstock.vn/HPG/profile.htm
    
    Returns:
        Dict với: founding_year, employees, industry
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return {}
    
    url = f"https://finance.vietstock.vn/{company_code}/profile.htm"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
    }
    
    data = {}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        
        if resp.status_code != 200:
            return {}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find company info section
        info_section = soup.find('div', class_='company-info') or soup.find('table', class_='info-table')
        
        if info_section:
            text = info_section.get_text()
            
            # Founding year
            match = re.search(r'(?:Năm thành lập|Ngày thành lập)[:\s]*(\d{4})', text)
            if match:
                data['founding_year'] = int(match.group(1))
            
            # Employees
            match = re.search(r'(?:Số nhân viên|Số lao động)[:\s]*([\d,\.]+)', text)
            if match:
                data['employees'] = int(match.group(1).replace(',', '').replace('.', ''))
        
        # Parse all text for patterns
        full_text = soup.get_text()
        
        if 'founding_year' not in data:
            match = re.search(r'thành lập[^\d]*(\d{4})', full_text, re.IGNORECASE)
            if match:
                data['founding_year'] = int(match.group(1))
        
    except Exception as e:
        print(f"  [WARN] Vietstock error: {e}")
    
    return data


def scrape_vietstock_ownership(company_code: str) -> Dict[str, float]:
    """
    Scrape ownership từ Vietstock.
    
    URL: https://finance.vietstock.vn/HPG/co-cau-co-dong.htm
    
    Returns:
        Dict với ownership percentages
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return {}
    
    url = f"https://finance.vietstock.vn/{company_code}/co-cau-co-dong.htm"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
    }
    
    data = {}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        
        if resp.status_code != 200:
            return {}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        
        # Parse ownership patterns
        patterns = [
            (r'(?:Cổ đông nhà nước|Sở hữu nhà nước)[^\d]*(\d+[,.]?\d*)\s*%', 'state_pct'),
            (r'(?:Cổ đông nước ngoài|Sở hữu nước ngoài|SHNN)[^\d]*(\d+[,.]?\d*)\s*%', 'foreign_pct'),
            (r'(?:Cổ đông tổ chức|Tổ chức trong nước)[^\d]*(\d+[,.]?\d*)\s*%', 'institutional_pct'),
            (r'(?:Ban điều hành|Nội bộ|Insider)[^\d]*(\d+[,.]?\d*)\s*%', 'insider_pct'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[key] = float(match.group(1).replace(',', '.'))
        
    except Exception as e:
        print(f"  [WARN] Vietstock ownership error: {e}")
    
    return data


# ========================
# Combined Scraper
# ========================

def get_ownership_from_web(company_code: str) -> Dict[int, float]:
    """
    Lấy dữ liệu sở hữu từ CafeF và Vietstock.
    
    Returns:
        Dict mapping index_id -> value:
            1: Managerial ownership (%)
            2: State ownership (%)
            3: Institutional ownership (%)
            4: Foreign ownership (%)
    """
    print(f"  -> Crawling ownership data for {company_code}...")
    
    data = {}
    
    # Try CafeF first
    cafef_data = scrape_cafef_ownership(company_code)
    time.sleep(0.5)  # Rate limiting
    
    # Try Vietstock as backup
    vietstock_data = scrape_vietstock_ownership(company_code)
    
    # Merge data (prefer CafeF, fallback to Vietstock)
    merged = {**vietstock_data, **cafef_data}
    
    # Map to index IDs
    if 'insider_pct' in merged:
        data[1] = merged['insider_pct']  # Managerial ownership
        print(f"    [OK] Managerial ownership: {merged['insider_pct']:.2f}%")
    
    if 'state_pct' in merged:
        data[2] = merged['state_pct']  # State ownership
        print(f"    [OK] State ownership: {merged['state_pct']:.2f}%")
    
    if 'institutional_pct' in merged:
        data[3] = merged['institutional_pct']  # Institutional ownership
        print(f"    [OK] Institutional ownership: {merged['institutional_pct']:.2f}%")
    
    if 'foreign_pct' in merged:
        data[4] = merged['foreign_pct']  # Foreign ownership
        print(f"    [OK] Foreign ownership: {merged['foreign_pct']:.2f}%")
    
    if not data:
        print(f"    [WARN] Could not scrape ownership for {company_code}")
    
    return data


def get_company_info_from_web(company_code: str) -> Dict[str, Any]:
    """
    Lấy thông tin công ty từ web (founding year, employees).
    
    Returns:
        Dict với: founding_year, employees
    """
    print(f"  -> Crawling company info for {company_code}...")
    
    # Try CafeF
    cafef_data = scrape_cafef_profile(company_code)
    time.sleep(0.5)
    
    # Try Vietstock
    vietstock_data = scrape_vietstock_profile(company_code)
    
    # Merge
    merged = {**vietstock_data, **cafef_data}
    
    if 'founding_year' in merged:
        print(f"    [OK] Founding year: {merged['founding_year']}")
    
    if 'employees' in merged:
        print(f"    [OK] Employees: {merged['employees']:,}")
    
    return merged


def get_market_data(
    company_code: str,
    year: int,
    founding_year: Optional[int] = None
) -> Dict[int, float]:
    """
    Lấy dữ liệu thị trường từ Yahoo Finance.
    
    Args:
        company_code: Mã chứng khoán (VD: HPG, VNM)
        year: Năm báo cáo
        founding_year: Năm thành lập (để tính firm age)
        
    Returns:
        Dict mapping index_id -> value:
            5: Total share outstanding
            23: Market value of equity
            38: Firm age
    """
    try:
        import yfinance as yf
    except ImportError:
        print("⚠ Cần cài đặt yfinance: pip install yfinance")
        return {}
    
    ticker_symbol = f"{company_code}.VN"
    data = {}
    
    try:
        print(f"  → Lấy dữ liệu Yahoo Finance cho {ticker_symbol}...")
        
        # Lấy giá cuối năm
        start_date = f"{year}-12-20"
        end_date = f"{year}-12-31"
        
        df_price = yf.download(
            ticker_symbol, 
            start=start_date, 
            end=end_date, 
            progress=False
        )
        
        if not df_price.empty:
            # Giá đóng cửa cuối năm
            close_price = float(df_price['Close'].iloc[-1])
            
            # Lấy info
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # Số cổ phiếu lưu hành
            shares = info.get('sharesOutstanding', 0)
            if shares and shares > 0:
                data[5] = shares  # Total share outstanding
                data[23] = close_price * shares  # Market value of equity
                print(f"    ✓ Shares: {shares:,.0f}")
                print(f"    ✓ Market cap: {data[23]:,.0f} VND")
            else:
                print(f"    ⚠ Không lấy được số cổ phiếu")
        else:
            print(f"    ⚠ Không có dữ liệu giá cho năm {year}")
        
    except Exception as e:
        print(f"    ✗ Lỗi Yahoo Finance: {e}")
    
    # Firm age
    if founding_year is None:
        founding_year = get_founding_year(company_code)
    
    if founding_year:
        data[38] = year - founding_year  # Firm age
        print(f"    ✓ Firm age: {data[38]} years (founded {founding_year})")
    
    return data


def get_ownership_data(company_code: str, year: int) -> Dict[int, float]:
    """
    Lấy dữ liệu sở hữu từ CafeF/Vietstock.
    
    Args:
        company_code: Mã công ty
        year: Năm
        
    Returns:
        Dict mapping index_id -> value:
            1: Managerial ownership
            2: State ownership
            3: Institutional ownership
            4: Foreign ownership
    """
    # Scrape từ CafeF và Vietstock
    return get_ownership_from_web(company_code)


def get_employee_count(company_code: str, year: int) -> Optional[int]:
    """
    Lấy số lượng nhân viên từ web.
    
    Args:
        company_code: Mã công ty
        year: Năm
        
    Returns:
        Số nhân viên hoặc None
    """
    info = get_company_info_from_web(company_code)
    return info.get('employees')


def get_all_external_data(
    company_code: str,
    year: int,
    founding_year: Optional[int] = None
) -> Dict[int, float]:
    """
    Lấy tất cả external data cho một công ty/năm.
    
    Args:
        company_code: Mã công ty
        year: Năm báo cáo
        founding_year: Năm thành lập
        
    Returns:
        Dict mapping index_id -> value
    """
    all_data = {}
    
    # 1. Company info from web (founding year, employees)
    company_info = get_company_info_from_web(company_code)
    
    if founding_year is None and 'founding_year' in company_info:
        founding_year = company_info['founding_year']
    
    if 'employees' in company_info:
        all_data[36] = company_info['employees']  # Number of employees
    
    time.sleep(0.5)  # Rate limiting
    
    # 2. Ownership data from CafeF/Vietstock
    ownership_data = get_ownership_from_web(company_code)
    all_data.update(ownership_data)
    
    time.sleep(0.5)
    
    # 3. Market data (Yahoo Finance)
    market_data = get_market_data(company_code, year, founding_year)
    all_data.update(market_data)
    
    # 4. Try FiinGroup/TCBS/SSI for market data (if Yahoo failed)
    if 5 not in all_data or 23 not in all_data:
        try:
            from .fiingroup import get_market_data_all_sources
            fiingroup_data = get_market_data_all_sources(company_code, year)
            for k, v in fiingroup_data.items():
                if k not in all_data:
                    all_data[k] = v
        except ImportError:
            pass
    
    # 5. World Bank Enterprise Survey for innovation data (Index 18-20)
    try:
        from .worldbank import get_all_wbes_data
        wbes_data = get_all_wbes_data(year)
        for k, v in wbes_data.items():
            if k not in all_data:
                all_data[k] = v
    except ImportError:
        pass
    
    return all_data


# ========================
# Parse Annual Report PDF
# ========================

def get_annual_report_data(pdf_path: str, year: int) -> Dict[int, float]:
    """
    Parse Annual Report PDF để extract thêm data.
    
    Args:
        pdf_path: Đường dẫn PDF Annual Report
        year: Năm báo cáo
        
    Returns:
        Dict mapping index_id -> value
    """
    try:
        from .annual_report import parse_annual_report
        return parse_annual_report(pdf_path, year)
    except ImportError:
        print("  [WARN] annual_report module not available")
        return {}


# ========================
# Manual data input helper
# ========================

def load_manual_data(file_path: Path) -> Dict[str, Dict[int, Dict[int, float]]]:
    """
    Load manual input data từ CSV file.
    
    Format CSV:
        company_code,year,index_id,value
        HPG,2020,1,5.5
        HPG,2020,2,0
        ...
    
    Args:
        file_path: Đường dẫn CSV
        
    Returns:
        Nested dict: company_code -> year -> index_id -> value
    """
    import pandas as pd
    
    if not file_path.exists():
        return {}
    
    df = pd.read_csv(file_path)
    
    result = {}
    for _, row in df.iterrows():
        company = row['company_code']
        year = int(row['year'])
        index_id = int(row['index_id'])
        value = row['value']
        
        if company not in result:
            result[company] = {}
        if year not in result[company]:
            result[company][year] = {}
        
        result[company][year][index_id] = value
    
    return result


def create_manual_template(output_path: Path, companies: list, years: list):
    """
    Tạo template CSV để nhập manual data.
    
    Args:
        output_path: Đường dẫn output
        companies: List mã công ty
        years: List năm
    """
    import pandas as pd
    
    # Các index cần manual input
    manual_indices = [
        (1, 'Managerial ownership', '%'),
        (2, 'State ownership', '%'),
        (3, 'Institutional ownership', '%'),
        (4, 'Foreign ownership', '%'),
        (19, 'Product innovation', 'binary'),
        (20, 'Process innovation', 'binary'),
    ]
    
    rows = []
    for company in companies:
        for year in years:
            for idx, name, unit in manual_indices:
                rows.append({
                    'company_code': company,
                    'year': year,
                    'index_id': idx,
                    'index_name': name,
                    'unit': unit,
                    'value': ''
                })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✓ Đã tạo template: {output_path}")
    print(f"  → Điền giá trị vào cột 'value' và lưu lại")
