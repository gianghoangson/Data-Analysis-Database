"""
Annual Report PDF Parser module.

Parse thông tin từ báo cáo thường niên PDF:
- Index 36: Number of employees
- Index 38: Firm age (từ founding year)
- Index 1-4: Ownership structure (nếu parse được)
- Index 18: R&D expenditure
- Index 34: Dividend payment
"""

from __future__ import annotations
import re
import requests
from pathlib import Path
from typing import Dict, Optional, Any, List
import io

# Try import fitz (PyMuPDF)
try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("[WARN] PyMuPDF not installed. Run: pip install PyMuPDF")


def download_pdf(url: str, out_path: str) -> str:
    """
    Download PDF từ URL.
    
    Args:
        url: URL của PDF
        out_path: Đường dẫn lưu file
        
    Returns:
        Path đã lưu
    """
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    with requests.get(url, stream=True, headers=headers, timeout=60) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
    
    return str(out)


def extract_text_pymupdf(pdf_path: str, max_pages: int = 50, use_ocr: bool = True) -> str:
    """
    Extract text từ PDF sử dụng PyMuPDF, với OCR fallback cho scanned PDFs.
    
    Args:
        pdf_path: Đường dẫn PDF
        max_pages: Số trang tối đa để extract
        use_ocr: Có sử dụng OCR nếu PDF là scan không
        
    Returns:
        Text đã extract
    """
    if not HAS_PYMUPDF:
        return ""
    
    doc = fitz.open(pdf_path)
    texts = []
    
    # First try normal text extraction
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        page_text = page.get_text("text")
        texts.append(page_text)
    
    combined = "\n".join(texts)
    
    # Check if PDF is scanned (very little text extracted)
    if len(combined.strip()) < 500 and use_ocr:
        print("    PDF appears to be scanned, using OCR...")
        
        try:
            import pytesseract
            from PIL import Image
            import io
            
            # Configure tesseract
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            ocr_texts = []
            dpi = 150
            
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                
                # Render page to image
                mat = fitz.Matrix(dpi/72, dpi/72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.open(io.BytesIO(pix.tobytes('png')))
                
                # OCR
                try:
                    text = pytesseract.image_to_string(img, lang='vie')
                    ocr_texts.append(text)
                except:
                    continue
            
            combined = "\n".join(ocr_texts)
            print(f"    OCR extracted {len(combined):,} chars")
            
        except ImportError:
            print("    [WARN] OCR not available. Install: pip install pytesseract Pillow")
        except Exception as e:
            print(f"    [WARN] OCR error: {e}")
    
    return combined


def find_employees(text: str) -> Optional[int]:
    """
    Tìm số lượng nhân viên từ text.
    
    Patterns:
    - "Tổng số lao động: 5,000 người"
    - "Số lượng nhân viên: 5.000"
    - "employees: 5,000"
    
    Returns:
        Số nhân viên hoặc None
    """
    # More specific patterns first (to avoid false positives)
    patterns = [
        # Vietnamese - specific patterns
        r"tổng\s*số\s*(?:lao\s*động|nhân\s*viên|cán\s*bộ)[:\s]*(\d{1,3}(?:[.,]\d{3})+|\d{3,6})\s*(?:người)?",
        r"số\s*lượng\s*(?:lao\s*động|nhân\s*viên|cán\s*bộ)[:\s]*(\d{1,3}(?:[.,]\d{3})+|\d{3,6})",
        r"nhân\s*sự[:\s]*(\d{1,3}(?:[.,]\d{3})+|\d{3,6})\s*(?:người)?",
        r"(?:có|với)\s*(\d{1,3}(?:[.,]\d{3})+|\d{4,6})\s*(?:lao\s*động|nhân\s*viên|cán\s*bộ)",
        
        # English - specific patterns
        r"total\s*(?:number\s*of\s*)?employees?[:\s]*(\d{1,3}(?:[,]\d{3})+|\d{3,6})",
        r"number\s*of\s*employees?[:\s]*(\d{1,3}(?:[,]\d{3})+|\d{3,6})",
        r"workforce\s*(?:of)?[:\s]*(\d{1,3}(?:[,]\d{3})+|\d{3,6})",
        r"headcount[:\s]*(\d{1,3}(?:[,]\d{3})+|\d{3,6})",
        r"(\d{1,3}(?:[,]\d{3})+|\d{4,6})\s*employees?",
        
        # Table header patterns (look for employee count in HR section)
        r"(?:nguồn\s*)?nhân\s*lực[^\d]{0,20}(\d{1,3}(?:[.,]\d{3})+|\d{4,6})",
        r"human\s*resources?[^\d]{0,20}(\d{1,3}(?:[,]\d{3})+|\d{4,6})",
    ]
    
    candidates = []
    
    for p in patterns:
        for m in re.finditer(p, text, flags=re.IGNORECASE):
            s = m.group(1)
            # Remove separators and convert to int
            s = re.sub(r"[^\d]", "", s)
            if s:
                val = int(s)
                # Sanity check: employees should be reasonable (100 to 500k for large VN companies)
                if 100 <= val <= 500_000:
                    candidates.append(val)
    
    if candidates:
        # Return the largest reasonable value (small numbers might be codes)
        return max(candidates)
    
    return None


def find_founding_year(text: str) -> Optional[int]:
    """
    Tìm năm thành lập từ text.
    
    Patterns:
    - "Founded in 1992"
    - "Thành lập năm 1992"
    - "Established 1992"
    
    Returns:
        Năm thành lập hoặc None
    """
    patterns = [
        # English patterns
        r"(?:founded|established|incorporated)\s*(?:in|on)?\s*([12][0-9]{3})",
        r"since\s+([12][0-9]{3})",
        r"(?:year\s+of\s+)?establishment[:\s]*([12][0-9]{3})",
        
        # Vietnamese patterns  
        r"thành\s*lập\s*(?:năm|từ|vào)?\s*([12][0-9]{3})",
        r"năm\s*thành\s*lập[:\s]*([12][0-9]{3})",
        r"được\s*thành\s*lập\s*(?:năm|từ|vào)?\s*([12][0-9]{3})",
        r"ra\s*đời\s*(?:năm|từ|vào)?\s*([12][0-9]{3})",
        r"hoạt\s*động\s*từ\s*(?:năm)?\s*([12][0-9]{3})",
    ]
    
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            y = int(m.group(1))
            # Sanity check
            if 1800 <= y <= 2025:
                return y
    
    return None


def find_ownership_structure(text: str) -> Dict[str, float]:
    """
    Tìm cơ cấu sở hữu từ text.
    
    Returns:
        Dict với: state_pct, foreign_pct, institutional_pct, insider_pct
    """
    data = {}
    
    # State ownership patterns
    state_patterns = [
        r"(?:State|Nhà\s*nước|SHNN)[^\d]*?(\d+[,.]?\d*)\s*%",
        r"(?:Sở\s*hữu\s*)?Nhà\s*nước[^\d]*?(\d+[,.]?\d*)\s*%",
        r"(?:Cổ\s*đông\s*)?Nhà\s*nước[^\d]*?(\d+[,.]?\d*)\s*%",
    ]
    for p in state_patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            data['state_pct'] = float(m.group(1).replace(',', '.'))
            break
    
    # Foreign ownership patterns
    foreign_patterns = [
        r"(?:Foreign|Nước\s*ngoài|SHNN)[^\d]*?(\d+[,.]?\d*)\s*%",
        r"(?:Sở\s*hữu\s*)?(?:Nước\s*ngoài|ngoại)[^\d]*?(\d+[,.]?\d*)\s*%",
        r"(?:Cổ\s*đông\s*)?(?:Nước\s*ngoài|ngoại)[^\d]*?(\d+[,.]?\d*)\s*%",
    ]
    for p in foreign_patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            val = float(m.group(1).replace(',', '.'))
            if val <= 100:  # Sanity check
                data['foreign_pct'] = val
                break
    
    # Institutional ownership
    inst_patterns = [
        r"(?:Institutional|Tổ\s*chức)[^\d]*?(\d+[,.]?\d*)\s*%",
        r"(?:Cổ\s*đông\s*)?(?:Tổ\s*chức|pháp\s*nhân)[^\d]*?(\d+[,.]?\d*)\s*%",
    ]
    for p in inst_patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            data['institutional_pct'] = float(m.group(1).replace(',', '.'))
            break
    
    # Insider/Management ownership
    insider_patterns = [
        r"(?:Insider|Management|Ban\s*điều\s*hành|Nội\s*bộ)[^\d]*?(\d+[,.]?\d*)\s*%",
        r"(?:Cổ\s*đông\s*)?(?:Nội\s*bộ|sáng\s*lập)[^\d]*?(\d+[,.]?\d*)\s*%",
    ]
    for p in insider_patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            data['insider_pct'] = float(m.group(1).replace(',', '.'))
            break
    
    return data


def find_rd_expenditure(text: str) -> Optional[float]:
    """
    Tìm chi phí R&D từ text.
    
    Returns:
        R&D expenditure (VND) hoặc None
    """
    patterns = [
        r"(?:R&D|R\s*&\s*D|nghiên\s*cứu\s*(?:và\s*)?phát\s*triển)[^\d]*?([\d,.]+)\s*(?:tỷ|billion|triệu|million)",
        r"chi\s*phí\s*(?:R&D|nghiên\s*cứu)[^\d]*?([\d,.]+)\s*(?:tỷ|billion|VND|đồng)",
    ]
    
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            s = m.group(1).replace(',', '').replace('.', '')
            if s:
                val = float(s)
                # Convert tỷ to VND
                if 'tỷ' in m.group(0).lower() or 'billion' in m.group(0).lower():
                    val *= 1e9
                elif 'triệu' in m.group(0).lower() or 'million' in m.group(0).lower():
                    val *= 1e6
                return val
    
    return None


def find_dividend_payment(text: str) -> Optional[float]:
    """
    Tìm chi trả cổ tức từ text.
    
    Returns:
        Dividend (VND) hoặc None
    """
    patterns = [
        r"(?:cổ\s*tức|dividend)[^\d]*?([\d,.]+)\s*(?:tỷ|billion|VND|đồng)",
        r"chi\s*trả\s*cổ\s*tức[^\d]*?([\d,.]+)\s*(?:tỷ|billion)",
        r"dividend\s*(?:payment|payout)[^\d]*?([\d,.]+)\s*(?:billion|VND)",
    ]
    
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            s = m.group(1).replace(',', '').replace('.', '')
            if s:
                val = float(s)
                if 'tỷ' in m.group(0).lower() or 'billion' in m.group(0).lower():
                    val *= 1e9
                return val
    
    return None


def parse_annual_report(pdf_path: str, year: int) -> Dict[int, float]:
    """
    Parse Annual Report PDF và extract các index.
    
    Args:
        pdf_path: Đường dẫn PDF
        year: Năm báo cáo
        
    Returns:
        Dict mapping index_id -> value:
            1: Managerial ownership (%)
            2: State ownership (%)
            3: Institutional ownership (%)
            4: Foreign ownership (%)
            18: R&D expenditure (VND)
            34: Dividend payment (VND)
            36: Number of employees
            38: Firm age (years)
    """
    print(f"  -> Parsing Annual Report: {pdf_path}")
    
    if not HAS_PYMUPDF:
        print("    [WARN] PyMuPDF not available")
        return {}
    
    if not Path(pdf_path).exists():
        print(f"    [WARN] File not found: {pdf_path}")
        return {}
    
    # Extract text
    text = extract_text_pymupdf(pdf_path)
    
    if not text:
        print("    [WARN] Could not extract text from PDF")
        return {}
    
    print(f"    Extracted {len(text):,} chars from PDF")
    
    data = {}
    
    # Number of employees (Index 36)
    employees = find_employees(text)
    if employees:
        data[36] = employees
        print(f"    [OK] Employees: {employees:,}")
    
    # Founding year -> Firm age (Index 38)
    founding_year = find_founding_year(text)
    if founding_year:
        firm_age = year - founding_year
        if firm_age >= 0:
            data[38] = firm_age
            print(f"    [OK] Firm age: {firm_age} years (founded {founding_year})")
    
    # Ownership structure (Index 1-4)
    ownership = find_ownership_structure(text)
    
    if 'insider_pct' in ownership:
        data[1] = ownership['insider_pct']
        print(f"    [OK] Managerial ownership: {ownership['insider_pct']}%")
    
    if 'state_pct' in ownership:
        data[2] = ownership['state_pct']
        print(f"    [OK] State ownership: {ownership['state_pct']}%")
    
    if 'institutional_pct' in ownership:
        data[3] = ownership['institutional_pct']
        print(f"    [OK] Institutional ownership: {ownership['institutional_pct']}%")
    
    if 'foreign_pct' in ownership:
        data[4] = ownership['foreign_pct']
        print(f"    [OK] Foreign ownership: {ownership['foreign_pct']}%")
    
    # R&D expenditure (Index 18)
    rd = find_rd_expenditure(text)
    if rd:
        data[18] = rd
        print(f"    [OK] R&D expenditure: {rd:,.0f} VND")
    
    # Dividend payment (Index 34)
    dividend = find_dividend_payment(text)
    if dividend:
        data[34] = dividend
        print(f"    [OK] Dividend: {dividend:,.0f} VND")
    
    return data


def parse_all_annual_reports(filings_dir: str, year: int) -> Dict[str, Dict[int, float]]:
    """
    Parse tất cả Annual Reports trong thư mục.
    
    Args:
        filings_dir: Thư mục chứa PDF
        year: Năm báo cáo
        
    Returns:
        Dict: company_code -> {index_id -> value}
    """
    filings_path = Path(filings_dir)
    
    if not filings_path.exists():
        print(f"  [WARN] Directory not found: {filings_dir}")
        return {}
    
    results = {}
    
    # Find all PDFs
    for company_dir in filings_path.iterdir():
        if not company_dir.is_dir():
            continue
        
        company_code = company_dir.name
        
        # Look for annual report PDF
        ar_patterns = [
            f"*{year}*annual*.pdf",
            f"*{year}*bctn*.pdf",  # Báo cáo thường niên
            f"*annual*{year}*.pdf",
            f"*{company_code}_{year}*.pdf",
        ]
        
        for pattern in ar_patterns:
            pdfs = list(company_dir.glob(pattern.lower())) + list(company_dir.glob(pattern.upper()))
            
            if pdfs:
                pdf_path = pdfs[0]
                print(f"\n[{company_code}] Found: {pdf_path.name}")
                
                data = parse_annual_report(str(pdf_path), year)
                if data:
                    results[company_code] = data
                break
    
    return results


# ========================
# Utility functions
# ========================

def scan_pdf_for_keywords(pdf_path: str, keywords: List[str]) -> Dict[str, List[str]]:
    """
    Debug function: tìm các dòng chứa keywords trong PDF.
    """
    if not HAS_PYMUPDF:
        return {}
    
    text = extract_text_pymupdf(pdf_path)
    lines = text.split('\n')
    
    results = {kw: [] for kw in keywords}
    
    for line in lines:
        for kw in keywords:
            if kw.lower() in line.lower():
                results[kw].append(line.strip()[:100])
    
    return results


if __name__ == '__main__':
    # Test
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        year = int(sys.argv[2]) if len(sys.argv) > 2 else 2024
        
        print(f"Parsing: {pdf_path}")
        data = parse_annual_report(pdf_path, year)
        print(f"\nResults: {data}")
    else:
        print("Usage: python annual_report.py <pdf_path> [year]")
        
        # Demo with existing PDFs
        demo_path = Path(__file__).parent.parent / 'data' / 'raw' / 'filings'
        if demo_path.exists():
            print(f"\nDemo: parsing {demo_path}")
            results = parse_all_annual_reports(str(demo_path), 2024)
            print(f"\nAll results: {results}")
