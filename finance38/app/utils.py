"""
Utility functions cho finance38
- Parse số tiền VN (100.000.000)
- Normalize đơn vị
- Load config
"""

import re
import yaml
from pathlib import Path
from typing import Optional, Union, Dict, Any


def parse_vn_number(text: str) -> Optional[float]:
    """
    Chuyển đổi chuỗi số tiền VN sang float.
    
    VD: '100.000.000' -> 100000000.0
        '(500.000)' -> -500000.0 (số âm)
        '1,234.56' -> 1234.56
    
    Args:
        text: Chuỗi số cần parse
        
    Returns:
        float hoặc None nếu không parse được
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    
    # Xử lý số âm trong ngoặc đơn: (100.000) -> -100000
    is_negative = False
    if text.startswith('(') and text.endswith(')'):
        is_negative = True
        text = text[1:-1]
    
    # Xử lý dấu trừ ở đầu
    if text.startswith('-'):
        is_negative = True
        text = text[1:]
    
    # Loại bỏ các ký tự không phải số
    # BCTC VN dùng dấu chấm (.) làm separator hàng nghìn  
    clean_text = re.sub(r'[^\d]', '', text)
    
    if not clean_text:
        return None
    
    try:
        value = float(clean_text)
        return -value if is_negative else value
    except ValueError:
        return None


def extract_numbers_from_line(line: str, min_value: float = 1000) -> list[float]:
    """
    Trích xuất tất cả các số từ một dòng text.
    
    Args:
        line: Dòng text
        min_value: Giá trị tối thiểu để lọc số rác (số trang, thuyết minh)
        
    Returns:
        List các số đã parse, đã lọc theo min_value
    """
    # Regex cải tiến: bắt số VN có nhiều nhóm 3 chữ số  
    # VD: 109.842.249.570.282 hoặc (75.225.243.262.689)
    pattern = r'\(?\d{1,3}(?:[.,]\d{3})+\)?'
    matches = re.findall(pattern, line)
    
    numbers = []
    for match in matches:
        value = parse_vn_number(match)
        if value is not None and abs(value) >= min_value:
            numbers.append(value)
    
    return numbers


def normalize_unit(value: float, unit: str = 'VND', target_unit: str = 'VND') -> float:
    """
    Chuẩn hóa đơn vị tiền tệ.
    
    Args:
        value: Giá trị gốc
        unit: Đơn vị gốc (VND, trieu, ty)
        target_unit: Đơn vị đích (VND, trieu, ty)
        
    Returns:
        Giá trị đã chuẩn hóa
    """
    # Chuyển về VND trước
    multipliers = {
        'VND': 1,
        'dong': 1,
        'trieu': 1_000_000,
        'ty': 1_000_000_000,
        'nghin': 1_000,
    }
    
    unit_lower = unit.lower()
    target_lower = target_unit.lower()
    
    # Chuyển về VND
    value_vnd = value * multipliers.get(unit_lower, 1)
    
    # Chuyển sang đơn vị đích
    return value_vnd / multipliers.get(target_lower, 1)


def load_mapping(mapping_path: Optional[Path] = None) -> Dict[int, Dict[str, Any]]:
    """
    Load mapping_index.yaml
    
    Args:
        mapping_path: Đường dẫn file mapping (mặc định: mapping/mapping_index.yaml)
        
    Returns:
        Dictionary mapping index_id -> config
    """
    if mapping_path is None:
        # Tìm từ thư mục project root
        root = Path(__file__).parent.parent
        mapping_path = root / 'mapping' / 'mapping_index.yaml'
    
    if not mapping_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file mapping: {mapping_path}")
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = yaml.safe_load(f)
    
    return mapping


def get_pdf_indices(mapping: Dict[int, Dict]) -> Dict[int, Dict]:
    """
    Lọc ra các index có source='pdf'
    
    Args:
        mapping: Full mapping dict
        
    Returns:
        Dict chỉ chứa các index trích từ PDF
    """
    return {
        idx: config 
        for idx, config in mapping.items() 
        if config.get('source') == 'pdf'
    }


def clean_company_code(filename: str) -> tuple[str, int]:
    """
    Trích xuất mã công ty và năm từ tên file.
    
    VD: 'HPG_2024.pdf' -> ('HPG', 2024)
        'VNM_2023.PDF' -> ('VNM', 2023)
    
    Args:
        filename: Tên file PDF
        
    Returns:
        Tuple (company_code, year)
    """
    name = Path(filename).stem  # Bỏ .pdf
    parts = name.split('_')
    
    if len(parts) >= 2:
        company_code = parts[0].upper()
        try:
            year = int(parts[-1])
            return company_code, year
        except ValueError:
            pass
    
    raise ValueError(f"Không thể parse tên file: {filename}. Format yêu cầu: CODE_YEAR.pdf")


def format_value(value: Optional[float], unit: str = 'VND') -> str:
    """
    Format giá trị để hiển thị.
    
    Args:
        value: Giá trị
        unit: Đơn vị
        
    Returns:
        Chuỗi đã format
    """
    if value is None:
        return "N/A"
    
    if unit in ('VND', 'dong'):
        if abs(value) >= 1e12:
            return f"{value/1e12:,.2f} nghìn tỷ"
        elif abs(value) >= 1e9:
            return f"{value/1e9:,.2f} tỷ"
        elif abs(value) >= 1e6:
            return f"{value/1e6:,.2f} triệu"
        else:
            return f"{value:,.0f} đồng"
    elif unit == '%':
        return f"{value:.2f}%"
    elif unit == 'shares':
        return f"{value:,.0f} cp"
    elif unit == 'people':
        return f"{value:,.0f} người"
    else:
        return f"{value:,.2f}"


# Năm thành lập các công ty
COMPANY_FOUNDING_YEARS = {
    'EVG': 2009,   # Tập đoàn EverLand
    'HAG': 1993,   # Hoàng Anh Gia Lai
    'HPG': 1992,   # Tập đoàn Hòa Phát
    'HSG': 2001,   # Tập đoàn Hoa Sen
    'KDC': 1993,   # Tập đoàn KIDO
    'MSN': 2004,   # Tập đoàn Masan
    'NTP': 1960,   # Nhựa Tiền Phong
    'PLX': 1956,   # Petrolimex
    'PNJ': 1988,   # Vàng bạc Đá quý Phú Nhuận
    'SAB': 1977,   # Sabeco
    'VNM': 1976,   # Vinamilk
    'NAF': 1995,   # Nafoods Group
    'TRA': 1972,   # Traphaco
    'DCM': 2011,   # CTCP Phân bón Dầu khí Cà Mau
    'VOS': 1970  # CTCP Vận tải Biển Việt Nam
}


def get_founding_year(company_code: str) -> Optional[int]:
    """
    Lấy năm thành lập công ty.
    
    Args:
        company_code: Mã chứng khoán
        
    Returns:
        Năm thành lập hoặc None
    """
    return COMPANY_FOUNDING_YEARS.get(company_code.upper())
