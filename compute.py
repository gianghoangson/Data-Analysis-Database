import pandas as pd

# Điền năm thành lập của các công ty vào đây
FOUNDING_YEARS = {
    "HPG": 1992,
    "HSG": 2001,
    "VNM": 1976,
    "DCM": 2011,
    "FPT": 1988
}

def apply_calculations(df):
    """
    Nhận vào DataFrame tổng (chứa nhiều công ty, nhiều năm)
    Trả về DataFrame đã được tính toán thêm các cột (Age, Growth)
    """
    print("   🧮 Đang tính toán các chỉ tiêu phái sinh...")
    
    # 1. TÍNH TUỔI CÔNG TY (Firm Age)
    def calculate_age(row):
        symbol = str(row.get('Symbol', '')).upper()
        year = pd.to_numeric(row.get('Year'), errors='coerce')
        founding_year = FOUNDING_YEARS.get(symbol)
        
        if pd.notna(year) and founding_year:
            return year - founding_year
        return None

    df['38. Firm age'] = df.apply(calculate_age, axis=1)

    # 2. TÍNH TĂNG TRƯỞNG DOANH THU (Growth Ratio)
    # Cần sort theo công ty và năm để tính so với năm trước
    df = df.sort_values(by=['Symbol', 'Year']).reset_index(drop=True)
    
    revenue_col = "6. Total sales revenue and Net sales revenue"
    if revenue_col in df.columns:
        df[revenue_col] = pd.to_numeric(df[revenue_col], errors='coerce')
        # Công thức: (Năm nay - Năm trước) / Năm trước
        df['32. Growth ratio'] = df.groupby('Symbol')[revenue_col].pct_change()
        df['32. Growth ratio'] = df['32. Growth ratio'].round(4) # Làm tròn 4 chữ số (VD: 0.1524)
        
    return df