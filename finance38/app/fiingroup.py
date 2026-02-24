"""
FiinGroup Datafeed API module.

Lấy dữ liệu thị trường từ FiinGroup API:
- Index 4: Foreign ownership (%)
- Index 5: Total shares outstanding
- Index 23: Market value of equity

Cần API key từ FiinGroup để sử dụng.
"""

from __future__ import annotations
import os
import requests
import pandas as pd
from typing import Dict, Optional, Any
from datetime import datetime
from pathlib import Path


class FiinGroupClient:
    """Client để gọi FiinGroup Datafeed API."""
    
    def __init__(
        self, 
        base_url: str = "https://datafeed.fiingroup.vn/api",
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("FIINGROUP_API_KEY")
        self.timeout = timeout
    
    def _headers(self) -> dict:
        h = {"Accept": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h
    
    def get_hose_stock_v2(
        self, 
        ticker: str, 
        from_date: str, 
        to_date: str
    ) -> pd.DataFrame:
        """
        Lấy dữ liệu cổ phiếu HOSE.
        
        Args:
            ticker: Mã cổ phiếu (VD: HPG, VNM)
            from_date: Ngày bắt đầu (YYYY-MM-DD)
            to_date: Ngày kết thúc (YYYY-MM-DD)
            
        Returns:
            DataFrame với columns: ClosePrice, ShareIssue, ForeignTotalRoom, ForeignCurrentRoom, etc.
        """
        url = f"{self.base_url}/Market/GetHoseStockv2"
        params = {
            "Ticker": ticker,
            "FromDate": from_date,
            "ToDate": to_date,
        }
        
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            
            # Server có thể trả {data:[...]} hoặc list trực tiếp
            rows = data.get("data", data) if isinstance(data, dict) else data
            return pd.DataFrame(rows)
        
        except requests.exceptions.RequestException as e:
            print(f"  [WARN] FiinGroup API error: {e}")
            return pd.DataFrame()
    
    def get_company_profile(self, ticker: str) -> Dict[str, Any]:
        """
        Lấy thông tin công ty.
        
        Returns:
            Dict với: founding_year, employees, industry, etc.
        """
        url = f"{self.base_url}/Company/GetCompanyProfile"
        params = {"Ticker": ticker}
        
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except:
            return {}
    
    def get_ownership_structure(self, ticker: str) -> Dict[str, Any]:
        """
        Lấy cơ cấu sở hữu.
        
        Returns:
            Dict với ownership percentages
        """
        url = f"{self.base_url}/Company/GetOwnershipStructure"
        params = {"Ticker": ticker}
        
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except:
            return {}


def compute_market_cap(df: pd.DataFrame) -> Optional[float]:
    """
    Tính market cap = Close price * Share issue.
    
    Args:
        df: DataFrame từ get_hose_stock_v2()
        
    Returns:
        Market cap (VND) hoặc None
    """
    if df.empty:
        return None
    
    try:
        close_price = float(df["ClosePrice"].iloc[-1])
        share_issue = float(df["ShareIssue"].iloc[-1])
        return close_price * share_issue
    except (KeyError, IndexError, ValueError):
        return None


def compute_foreign_ownership_ratio(df: pd.DataFrame) -> Optional[float]:
    """
    Tính tỷ lệ sở hữu nước ngoài.
    
    Foreign holding = ForeignTotalRoom - ForeignCurrentRoom
    Ratio = foreign_holding / ShareIssue * 100
    
    Args:
        df: DataFrame từ get_hose_stock_v2()
        
    Returns:
        Foreign ownership % hoặc None
    """
    if df.empty:
        return None
    
    try:
        total_room = float(df["ForeignTotalRoom"].iloc[-1])
        current_room = float(df["ForeignCurrentRoom"].iloc[-1])
        share_issue = float(df["ShareIssue"].iloc[-1])
        
        foreign_holding = total_room - current_room
        ratio = (foreign_holding / share_issue) * 100
        return ratio
    except (KeyError, IndexError, ValueError, ZeroDivisionError):
        return None


def get_fiingroup_data(
    company_code: str,
    year: int,
    api_key: Optional[str] = None
) -> Dict[int, float]:
    """
    Lấy dữ liệu từ FiinGroup API cho một công ty/năm.
    
    Args:
        company_code: Mã cổ phiếu
        year: Năm
        api_key: FiinGroup API key
        
    Returns:
        Dict mapping index_id -> value:
            4: Foreign ownership (%)
            5: Total shares outstanding
            23: Market value of equity (VND)
    """
    if not api_key and not os.environ.get("FIINGROUP_API_KEY"):
        print("  [WARN] No FiinGroup API key. Set FIINGROUP_API_KEY env var or pass api_key.")
        return {}
    
    client = FiinGroupClient(api_key=api_key)
    
    # Lấy dữ liệu cuối năm
    from_date = f"{year}-12-01"
    to_date = f"{year}-12-31"
    
    print(f"  -> FiinGroup: Getting {company_code} data for {year}...")
    
    df = client.get_hose_stock_v2(company_code, from_date, to_date)
    
    data = {}
    
    if not df.empty:
        # Foreign ownership (Index 4)
        foreign_pct = compute_foreign_ownership_ratio(df)
        if foreign_pct is not None:
            data[4] = foreign_pct
            print(f"    [OK] Foreign ownership: {foreign_pct:.2f}%")
        
        # Shares outstanding (Index 5)
        if "ShareIssue" in df.columns:
            shares = float(df["ShareIssue"].iloc[-1])
            data[5] = shares
            print(f"    [OK] Shares outstanding: {shares:,.0f}")
        
        # Market cap (Index 23)
        market_cap = compute_market_cap(df)
        if market_cap is not None:
            data[23] = market_cap
            print(f"    [OK] Market cap: {market_cap:,.0f} VND")
    else:
        print(f"    [WARN] No data from FiinGroup for {company_code}")
    
    return data


# ========================
# Alternative: SSI iBoard API (free)
# ========================

def get_ssi_market_data(company_code: str, year: int) -> Dict[int, float]:
    """
    Lấy dữ liệu từ SSI iBoard (miễn phí, không cần API key).
    
    Args:
        company_code: Mã cổ phiếu
        year: Năm
        
    Returns:
        Dict với market data
    """
    import requests
    
    url = f"https://iboard.ssi.com.vn/dchart/api/1.1/defaultChart"
    params = {
        "resolution": "D",
        "symbol": company_code,
        "from": f"{year}0101",
        "to": f"{year}1231",
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }
    
    data = {}
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            result = r.json()
            
            # Extract close prices
            if 'c' in result and result['c']:
                close_prices = result['c']
                last_price = close_prices[-1] * 1000  # SSI returns in 1000 VND
                
                # Get shares from another endpoint
                info_url = f"https://iboard.ssi.com.vn/dchart/api/1.1/instruments/{company_code}"
                info_r = requests.get(info_url, headers=headers, timeout=10)
                
                if info_r.status_code == 200:
                    info = info_r.json()
                    shares = info.get('ShareIssue', 0)
                    
                    if shares > 0:
                        data[5] = shares
                        data[23] = last_price * shares
                        print(f"    [OK] SSI: Shares={shares:,.0f}, Price={last_price:,.0f}")
    
    except Exception as e:
        print(f"    [WARN] SSI API error: {e}")
    
    return data


# ========================
# TCBS API (alternative)
# ========================

def get_tcbs_data(company_code: str, year: int) -> Dict[int, float]:
    """
    Lấy dữ liệu từ TCBS API (miễn phí).
    
    Args:
        company_code: Mã cổ phiếu
        year: Năm
        
    Returns:
        Dict với ownership và market data
    """
    import requests
    
    data = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        # Company overview
        url = f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/ticker/{company_code}/overview"
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            info = r.json()
            
            # Foreign ownership
            foreign_own = info.get('foreignPercent')
            if foreign_own:
                data[4] = float(foreign_own)
                print(f"    [OK] TCBS Foreign ownership: {foreign_own}%")
            
            # Shares outstanding
            shares = info.get('sharesOutstanding') or info.get('shareOutstanding')
            if shares:
                data[5] = float(shares)
                print(f"    [OK] TCBS Shares: {shares:,.0f}")
            
            # Market cap
            market_cap = info.get('marketCap')
            if market_cap:
                data[23] = float(market_cap) * 1e9  # Usually in billion VND
                print(f"    [OK] TCBS Market cap: {data[23]:,.0f} VND")
        
        # Ownership structure
        own_url = f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/company/{company_code}/large-share-holders"
        own_r = requests.get(own_url, headers=headers, timeout=15)
        
        if own_r.status_code == 200:
            owners = own_r.json()
            
            state_pct = 0
            insider_pct = 0
            institutional_pct = 0
            
            for owner in owners.get('listShareHolder', []):
                owner_type = owner.get('type', '').lower()
                pct = owner.get('percentage', 0)
                
                if 'nhà nước' in owner_type or 'state' in owner_type:
                    state_pct += pct
                elif 'nội bộ' in owner_type or 'insider' in owner_type or 'ban' in owner_type:
                    insider_pct += pct
                elif 'tổ chức' in owner_type or 'institution' in owner_type:
                    institutional_pct += pct
            
            if insider_pct > 0:
                data[1] = insider_pct
                print(f"    [OK] TCBS Managerial: {insider_pct}%")
            
            if state_pct > 0:
                data[2] = state_pct
                print(f"    [OK] TCBS State: {state_pct}%")
            
            if institutional_pct > 0:
                data[3] = institutional_pct
                print(f"    [OK] TCBS Institutional: {institutional_pct}%")
    
    except Exception as e:
        print(f"    [WARN] TCBS API error: {e}")
    
    return data


def get_market_data_all_sources(
    company_code: str,
    year: int,
    fiingroup_api_key: Optional[str] = None
) -> Dict[int, float]:
    """
    Lấy market data từ nhiều nguồn (FiinGroup, SSI, TCBS).
    Ưu tiên: FiinGroup > TCBS > SSI
    
    Args:
        company_code: Mã cổ phiếu
        year: Năm
        fiingroup_api_key: Optional FiinGroup API key
        
    Returns:
        Dict mapping index_id -> value
    """
    data = {}
    
    # 1. Try FiinGroup (if API key available)
    if fiingroup_api_key or os.environ.get("FIINGROUP_API_KEY"):
        fiingroup_data = get_fiingroup_data(company_code, year, fiingroup_api_key)
        data.update(fiingroup_data)
    
    # 2. Try TCBS (free, good coverage)
    if not data or len(data) < 3:
        print(f"  -> Trying TCBS API for {company_code}...")
        tcbs_data = get_tcbs_data(company_code, year)
        
        # Only update missing keys
        for k, v in tcbs_data.items():
            if k not in data:
                data[k] = v
    
    # 3. Try SSI (backup)
    if 5 not in data or 23 not in data:
        print(f"  -> Trying SSI iBoard for {company_code}...")
        ssi_data = get_ssi_market_data(company_code, year)
        
        for k, v in ssi_data.items():
            if k not in data:
                data[k] = v
    
    return data


if __name__ == '__main__':
    # Test
    print("Testing FiinGroup/TCBS/SSI module...")
    
    for company in ['HPG', 'VNM', 'MSN']:
        print(f"\n=== {company} ===")
        data = get_market_data_all_sources(company, 2024)
        print(f"Result: {data}")
