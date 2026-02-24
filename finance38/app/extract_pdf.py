"""
PDF Extraction module cho finance38
- Parse BCTC PDF theo mapping
- Sử dụng pdfplumber (preferred) hoặc PyMuPDF + OCR
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    print("⚠ pdfplumber không được cài đặt. Sử dụng: pip install pdfplumber")

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pytesseract
    from PIL import Image
    import io
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Fallback nếu không có tqdm
    def tqdm(iterable, **kwargs):
        return iterable

from .utils import (
    parse_vn_number, 
    extract_numbers_from_line, 
    load_mapping, 
    get_pdf_indices,
    clean_company_code
)


class PDFExtractor:
    """Trích xuất dữ liệu tài chính từ PDF BCTC"""
    
    def __init__(self, mapping_path: Optional[Path] = None, tesseract_path: str = None):
        """
        Khởi tạo extractor với mapping config.
        
        Args:
            mapping_path: Đường dẫn file mapping (None = mặc định)
            tesseract_path: Đường dẫn Tesseract OCR (Windows)
        """
        self.mapping = load_mapping(mapping_path)
        self.pdf_indices = get_pdf_indices(self.mapping)
        
        # Config Tesseract
        if tesseract_path and HAS_OCR:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif HAS_OCR:
            # Default Windows path
            default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path
    
    def _check_has_text(self, pdf_path: Path) -> bool:
        """Kiểm tra PDF có text layer không."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check 5 trang đầu
                for i in range(min(5, len(pdf.pages))):
                    if pdf.pages[i].chars and len(pdf.pages[i].chars) > 50:
                        return True
        except Exception:
            pass
        return False
        return False
    
    def extract_from_pdf(self, pdf_path: str | Path) -> Dict[int, float]:
        """
        Trích xuất tất cả các chỉ số từ file PDF.
        
        Args:
            pdf_path: Đường dẫn file PDF
            
        Returns:
            Dict mapping index_id -> value
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"File không tồn tại: {pdf_path}")
        
        if not HAS_PDFPLUMBER:
            raise ImportError("Cần cài đặt pdfplumber: pip install pdfplumber")
        
        extracted = {}
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📄 Đang xử lý {len(pdf.pages)} trang từ {pdf_path.name}...")
            
            for page_num, page in enumerate(pdf.pages, 1):
                # Trích xuất text giữ layout
                text = page.extract_text(layout=True)
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for line in lines:
                    line_text = line.strip()
                    if not line_text:
                        continue
                    
                    # Tìm trong từng index config
                    for index_id, config in self.pdf_indices.items():
                        # Bỏ qua nếu đã tìm thấy (first_match rule)
                        rule = config.get('rule', 'first_match')
                        if rule == 'first_match' and index_id in extracted:
                            continue
                        
                        # Kiểm tra keywords
                        keywords = config.get('keywords', [])
                        matched = False
                        
                        for keyword in keywords:
                            if keyword.lower() in line_text.lower():
                                matched = True
                                break
                        
                        if not matched:
                            continue
                        
                        # Trích xuất số từ dòng
                        min_value = config.get('min_value', 1000)
                        numbers = extract_numbers_from_line(line_text, min_value=min_value)
                        
                        if not numbers:
                            continue
                        
                        # Áp dụng rule
                        if rule == 'max_value':
                            value = max(numbers, key=abs)
                            if index_id in extracted:
                                if abs(value) > abs(extracted[index_id]):
                                    extracted[index_id] = value
                            else:
                                extracted[index_id] = value
                        elif rule == 'last_match':
                            extracted[index_id] = numbers[-1]
                        else:  # first_match (default)
                            extracted[index_id] = numbers[0]
                        
                        # Xử lý số âm (CAPEX, dividend thường là âm trong BCTC)
                        if config.get('is_negative', False) and index_id in extracted:
                            extracted[index_id] = -abs(extracted[index_id])
                        
                        print(f"  ✓ [{index_id}] {config['name']}: {extracted[index_id]:,.0f}")
        
        return extracted
    
    def extract_with_tables(self, pdf_path: str | Path) -> Dict[int, float]:
        """
        Trích xuất sử dụng table extraction của pdfplumber.
        Hiệu quả hơn với BCTC có cấu trúc bảng rõ ràng.
        
        Args:
            pdf_path: Đường dẫn PDF
            
        Returns:
            Dict mapping index_id -> value
        """
        pdf_path = Path(pdf_path)
        extracted = {}
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                
                for table in tables:
                    if not table:
                        continue
                    
                    for row in table:
                        if not row or len(row) < 2:
                            continue
                        
                        # Cột đầu thường là tên chỉ tiêu
                        label = str(row[0]) if row[0] else ''
                        
                        for index_id, config in self.pdf_indices.items():
                            if index_id in extracted:
                                continue
                            
                            keywords = config.get('keywords', [])
                            for keyword in keywords:
                                if keyword.lower() in label.lower():
                                    # Tìm số trong các cột còn lại
                                    for cell in row[1:]:
                                        if cell:
                                            value = parse_vn_number(str(cell))
                                            min_val = config.get('min_value', 1000)
                                            if value and abs(value) >= min_val:
                                                extracted[index_id] = value
                                                break
                                    break
        
        return extracted
    
    def extract_with_ocr(self, pdf_path: str | Path, dpi: int = 200) -> Dict[int, float]:
        """
        Trích xuất sử dụng OCR (cho PDF scan).
        
        Args:
            pdf_path: Đường dẫn PDF
            dpi: Độ phân giải render (cao hơn = chính xác hơn nhưng chậm)
            
        Returns:
            Dict mapping index_id -> value
        """
        if not HAS_PYMUPDF:
            raise ImportError("Cần cài PyMuPDF: pip install PyMuPDF")
        if not HAS_OCR:
            raise ImportError("Cần cài pytesseract và Pillow: pip install pytesseract Pillow")
        
        pdf_path = Path(pdf_path)
        extracted = {}
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Progress bar cho OCR từng trang
        page_iterator = tqdm(
            range(total_pages),
            desc=f"  🔍 OCR {pdf_path.name[:15]}",
            unit="page",
            ncols=80,
            leave=False
        ) if HAS_TQDM else range(total_pages)
        
        for page_num in page_iterator:
            page = doc[page_num]
            
            # Render page thành image
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # OCR
            text = pytesseract.image_to_string(img, lang='vie')
            
            if not text:
                continue
            
            # Process text giống như pdfplumber
            for line in text.split('\n'):
                line_text = line.strip()
                if not line_text:
                    continue
                
                for index_id, config in self.pdf_indices.items():
                    rule = config.get('rule', 'first_match')
                    if rule == 'first_match' and index_id in extracted:
                        continue
                    
                    keywords = config.get('keywords', [])
                    matched = False
                    for keyword in keywords:
                        if keyword.lower() in line_text.lower():
                            matched = True
                            break
                    
                    if not matched:
                        continue
                    
                    min_value = config.get('min_value', 1000)
                    numbers = extract_numbers_from_line(line_text, min_value=min_value)
                    
                    if not numbers:
                        continue
                    
                    if rule == 'max_value':
                        value = max(numbers, key=abs)
                        if index_id in extracted:
                            if abs(value) > abs(extracted[index_id]):
                                extracted[index_id] = value
                        else:
                            extracted[index_id] = value
                    else:
                        extracted[index_id] = numbers[0]
                    
                    if config.get('is_negative', False) and index_id in extracted:
                        extracted[index_id] = -abs(extracted[index_id])
        
        doc.close()
        
        if extracted:
            print(f"  ✓ OCR tìm được {len(extracted)} chỉ số")
        
        return extracted
    
    def process_file(self, pdf_path: str | Path) -> Dict[str, Any]:
        """
        Xử lý một file PDF và trả về kết quả đầy đủ.
        
        Args:
            pdf_path: Đường dẫn file PDF
            
        Returns:
            Dict với keys: company_code, year, data (dict index_id -> value)
        """
        pdf_path = Path(pdf_path)
        
        # Parse tên file
        company_code, year = clean_company_code(pdf_path.name)
        
        # Kiểm tra PDF có text layer không
        has_text = self._check_has_text(pdf_path)
        
        if has_text:
            # PDF có text -> dùng pdfplumber
            data = self.extract_from_pdf(pdf_path)
            
            # Thử table extraction nếu có ít dữ liệu
            if len(data) < 10:
                print("  → Thử table extraction...")
                table_data = self.extract_with_tables(pdf_path)
                for idx, val in table_data.items():
                    if idx not in data:
                        data[idx] = val
        else:
            # PDF scan -> dùng OCR
            print("  ⚠ PDF scan detected, sử dụng OCR...")
            if HAS_OCR and HAS_PYMUPDF:
                data = self.extract_with_ocr(pdf_path)
            else:
                print("  ✗ Cần cài: pip install PyMuPDF pytesseract Pillow")
                print("  ✗ Và cài Tesseract OCR: https://github.com/tesseract-ocr/tesseract")
                data = {}
        
        return {
            'company_code': company_code,
            'year': year,
            'data': data,
            'extracted_count': len(data),
            'pdf_filename': pdf_path.name
        }


def process_filings_folder(
    folder_path: Optional[Path] = None,
    recursive: bool = True
) -> List[Dict[str, Any]]:
    """
    Xử lý tất cả PDF trong folder filings.
    
    Cấu trúc folder:
        data/raw/filings/
        ├── HPG/
        │   ├── HPG_2020.pdf
        │   ├── HPG_2021.pdf
        ├── VNM/
        │   └── VNM_2020.pdf
    
    Args:
        folder_path: Đường dẫn folder (None = data/raw/filings)
        recursive: Tìm trong subfolder không
        
    Returns:
        List các kết quả extract
    """
    if folder_path is None:
        root = Path(__file__).parent.parent
        folder_path = root / 'data' / 'raw' / 'filings'
    
    folder_path = Path(folder_path)
    
    if not folder_path.exists():
        print(f"⚠ Folder không tồn tại: {folder_path}")
        return []
    
    # Tìm tất cả file PDF
    if recursive:
        pdf_files = list(folder_path.rglob('*.pdf'))
    else:
        pdf_files = list(folder_path.glob('*.pdf'))
    
    if not pdf_files:
        print(f"⚠ Không tìm thấy file PDF trong {folder_path}")
        return []
    
    print(f"📁 Tìm thấy {len(pdf_files)} file PDF")
    
    extractor = PDFExtractor()
    results = []
    
    # Progress bar cho danh sách file
    pdf_iterator = tqdm(
        sorted(pdf_files), 
        desc="📊 Xử lý PDF", 
        unit="file",
        ncols=80
    ) if HAS_TQDM else sorted(pdf_files)
    
    for pdf_file in pdf_iterator:
        try:
            if HAS_TQDM:
                pdf_iterator.set_postfix_str(pdf_file.name[:20])
            else:
                print(f"\n{'='*60}")
            
            result = extractor.process_file(pdf_file)
            results.append(result)
            
            if not HAS_TQDM:
                print(f"  → Trích xuất được {result['extracted_count']}/38 chỉ số")
        except Exception as e:
            if not HAS_TQDM:
                print(f"  ✗ Lỗi: {e}")
            results.append({
                'pdf_filename': pdf_file.name,
                'error': str(e)
            })
    
    # Summary
    success = sum(1 for r in results if 'error' not in r)
    total_extracted = sum(r.get('extracted_count', 0) for r in results)
    print(f"\n✅ Hoàn thành: {success}/{len(results)} files, {total_extracted} chỉ số")
    
    return results


# Convenience function
def extract_pdf(pdf_path: str | Path) -> Dict[int, float]:
    """
    Quick extract từ một file PDF.
    
    Args:
        pdf_path: Đường dẫn file
        
    Returns:
        Dict index_id -> value
    """
    extractor = PDFExtractor()
    return extractor.extract_from_pdf(pdf_path)
