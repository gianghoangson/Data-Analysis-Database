"""
Script chạy OCR từng file PDF và xuất CSV ngay
Mỗi file PDF -> 1 file CSV kết quả + lưu vào SQLite DB
Hỗ trợ chạy song song (parallel processing)
"""
import sys
import os
from pathlib import Path
import pandas as pd
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from tqdm import tqdm

# Add finance38 to path
sys.path.insert(0, str(Path(__file__).parent))

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import yaml

from app.db import Database

# Config Tesseract
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Load mapping
MAPPING_PATH = Path(__file__).parent / "mapping" / "mapping_index.yaml"
with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
    MAPPING = yaml.safe_load(f)

# Lọc PDF indices
PDF_INDICES = {k: v for k, v in MAPPING.items() if v.get('source') == 'pdf'}


def parse_vn_number(text):
    """Parse số VN: 109.842.249.570.282 -> float"""
    if not text:
        return None
    text = str(text).strip()
    
    is_negative = text.startswith('(') and text.endswith(')')
    if is_negative:
        text = text[1:-1]
    if text.startswith('-'):
        is_negative = True
        text = text[1:]
    
    clean = re.sub(r'[^\d]', '', text)
    if not clean:
        return None
    
    try:
        val = float(clean)
        return -val if is_negative else val
    except:
        return None


def extract_numbers(line, min_value=1000):
    """Extract tất cả số từ dòng text"""
    pattern = r'\(?\d{1,3}(?:[.,]\d{3})+\)?'
    matches = re.findall(pattern, line)
    
    numbers = []
    for m in matches:
        val = parse_vn_number(m)
        if val and abs(val) >= min_value:
            numbers.append(val)
    return numbers


def ocr_pdf(pdf_path, dpi=150, quiet=False):
    """OCR toàn bộ PDF và extract 38 index"""
    pdf_path = Path(pdf_path)
    
    extracted = {}
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    if not quiet:
        print(f"\n[OCR] {pdf_path.name} ({total_pages} trang)")
    
    for page_num in range(total_pages):
        # Progress
        if (page_num + 1) % 10 == 0 and not quiet:
            print(f"  ... trang {page_num + 1}/{total_pages}")
        
        page = doc[page_num]
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes('png')))
        
        try:
            text = pytesseract.image_to_string(img, lang='vie')
        except Exception as e:
            continue
        
        if not text:
            continue
        
        lines = text.split('\n')
        
        # DEBUG: Find BALANCE SHEET pages (Bảng CDKT)
        text_upper = text.upper()
        if "CONG TAI SAN" in text_upper or "TONG CONG" in text_upper:
            safe_text = text.encode('ascii', 'replace').decode()
            print(f"[DEBUG] P{page_num} may have Total Assets:\n{safe_text[:800]}")
        
        # Indices cần search cả trang (totals nằm xa keyword do format bảng OCR)
        # Chỉ dùng cho các TỔNG lớn nhất
        SEARCH_PAGE_INDICES = {6, 7}  # Revenue, Total Assets
        
        for i, line in enumerate(lines):
            line_text = line.strip()
            if not line_text:
                continue
            
            for index_id, config in PDF_INDICES.items():
                rule = config.get('rule', 'first_match')
                if rule == 'first_match' and index_id in extracted:
                    continue
                
                keywords = config.get('keywords', [])
                matched = False
                for kw in keywords:
                    if kw.lower() in line_text.lower():
                        matched = True
                        break
                
                if not matched:
                    continue
                
                # Debug for Index 7
                if index_id == 7:
                    print(f"[DEBUG] Index 7 matched at line {i}: {line_text[:60]}")
                
                min_val = config.get('min_value', 1000)
                
                # Tìm số trong dòng hiện tại + 5 dòng tiếp theo
                search_text = line_text
                for j in range(1, 6):
                    if i + j < len(lines):
                        search_text += ' ' + lines[i + j].strip()
                
                numbers = extract_numbers(search_text, min_value=min_val)
                
                # Nếu không tìm thấy và là index quan trọng, search cả trang
                if not numbers and index_id in SEARCH_PAGE_INDICES:
                    numbers = extract_numbers(text, min_value=min_val)
                    if index_id == 7:
                        print(f"[DEBUG] Index 7 page search found {len(numbers) if numbers else 0} numbers")
                        if numbers:
                            print(f"[DEBUG] Index 7 numbers sample: {numbers[:5]}")
                
                if not numbers:
                    if index_id == 7:
                        print(f"[DEBUG] Index 7 NO numbers found, min_val={min_val}")
                    continue
                
                # Với indices quan trọng (totals), lấy giá trị lớn nhất
                if index_id in SEARCH_PAGE_INDICES:
                    val = max(numbers, key=abs)
                elif rule == 'max_value':
                    val = max(numbers, key=abs)
                    if index_id in extracted:
                        if abs(val) > abs(extracted[index_id]):
                            extracted[index_id] = val
                        continue
                    else:
                        pass  # sẽ assign bên dưới
                else:
                    val = numbers[0]
                
                extracted[index_id] = val
                
                # Debug for Index 7
                if index_id == 7:
                    print(f"[DEBUG] Index 7 EXTRACTED: {val}")
                
                if config.get('is_negative', False) and index_id in extracted:
                    extracted[index_id] = -abs(extracted[index_id])
    
    doc.close()
    return extracted


def export_single_result(pdf_path, output_dir=None, save_db=True, quiet=False):
    """
    Extract và xuất CSV cho 1 file PDF, đồng thời lưu vào DB.
    
    Args:
        pdf_path: Đường dẫn file PDF
        output_dir: Thư mục output CSV
        save_db: True = lưu vào SQLite DB
        quiet: True = không in output (dùng cho parallel)
    
    Returns:
        Dict chứa kết quả: company, year, extracted_count, csv_path
    """
    pdf_path = Path(pdf_path)
    
    if output_dir is None:
        output_dir = Path(__file__).parent / "data" / "processed"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse filename
    name = pdf_path.stem  # HPG_2024
    parts = name.split('_')
    company = parts[0] if parts else name
    year = int(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 0
    
    # OCR extract
    data = ocr_pdf(pdf_path, quiet=quiet)
    
    # Tạo DataFrame với đủ 38 index
    rows = []
    db_records = []
    
    for idx in sorted(MAPPING.keys()):
        config = MAPPING[idx]
        value = data.get(idx, None)
        
        rows.append({
            'index_id': idx,
            'index_name': config.get('name', ''),
            'name_vn': config.get('name_vn', ''),
            'value': value,
            'unit': config.get('unit', ''),
            'source': config.get('source', '')
        })
        
        # Chuẩn bị record cho DB (chỉ lưu nếu có value)
        if value is not None:
            db_records.append({
                'company_code': company,
                'year': year,
                'index_id': idx,
                'index_name': config.get('name', ''),
                'value': value,
                'unit': config.get('unit', 'VND'),
                'source': 'pdf'
            })
    
    df = pd.DataFrame(rows)
    
    # Xuất CSV
    csv_name = f"{company}_{year}_result.csv"
    csv_path = output_dir / csv_name
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    # Lưu vào DB
    if save_db and db_records:
        try:
            db = Database()
            db.init_schema()  # Auto-create nếu chưa có
            db.add_company(company)
            db.upsert_batch(db_records)
            db.log_processing(
                company_code=company,
                year=year,
                pdf_filename=pdf_path.name,
                status='success',
                extracted_count=len(db_records)
            )
        except Exception as e:
            if not quiet:
                print(f"  [WARN] DB Error: {e}")
    
    # Stats
    filled = df['value'].notna().sum()
    
    if not quiet:
        print(f"  [OK] Extracted: {filled}/38 indices")
        print(f"  [OK] Saved: {csv_path.name}")
        if save_db:
            print(f"  [OK] DB: {len(db_records)} records saved")
        
        # Hiển thị các giá trị đã extract
        if data:
            print(f"  Indices found:")
            for idx, val in sorted(data.items()):
                idx_name = MAPPING[idx].get('name', '')[:40]
                if abs(val) >= 1e12:
                    fmt = f"{val/1e12:.2f} nghin ty"
                elif abs(val) >= 1e9:
                    fmt = f"{val/1e9:.2f} ty"
                else:
                    fmt = f"{val:,.0f}"
                print(f"    [{idx:2d}] {idx_name:<40} = {fmt}")
    
    return {
        'company': company,
        'year': year,
        'pdf_name': pdf_path.name,
        'extracted_count': filled,
        'csv_path': str(csv_path),
        'db_records': len(db_records) if save_db else 0
    }


def _process_single(args):
    """Wrapper function cho parallel processing"""
    pdf_file, output_dir, save_db = args
    try:
        result = export_single_result(pdf_file, output_dir, save_db=save_db, quiet=True)
        return {'status': 'success', **result}
    except Exception as e:
        return {
            'status': 'error',
            'pdf_name': pdf_file.name,
            'error': str(e)
        }


def process_folder(folder_path, output_dir=None, save_db=True, parallel=False, workers=None):
    """
    Xử lý tất cả PDF trong folder.
    
    Args:
        folder_path: Thư mục chứa PDF
        output_dir: Thư mục output
        save_db: True = lưu vào SQLite DB
        parallel: True = chạy song song
        workers: Số worker (mặc định = CPU cores - 1)
    """
    folder = Path(folder_path)
    pdf_files = list(folder.rglob('*.pdf'))
    
    print(f"📁 Tìm thấy {len(pdf_files)} file PDF")
    if save_db:
        print(f"💾 Sẽ lưu vào SQLite DB")
    
    if parallel:
        if workers is None:
            workers = max(1, multiprocessing.cpu_count() - 1)
        print(f"🚀 Chạy SONG SONG với {workers} workers")
    else:
        print(f"🔄 Chạy TUẦN TỰ")
    
    print("="*60)
    
    # Init DB schema trước nếu cần
    if save_db:
        db = Database()
        db.init_schema()
    
    results = []
    errors = []
    
    if parallel:
        # Parallel processing with tqdm
        args_list = [(pdf, output_dir, save_db) for pdf in sorted(pdf_files)]
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_process_single, args): args[0].name 
                      for args in args_list}
            
            pbar = tqdm(as_completed(futures), total=len(futures), 
                       desc="OCR Processing", unit="file", ncols=80)
            
            for future in pbar:
                pdf_name = futures[future]
                result = future.result()
                
                if result['status'] == 'success':
                    results.append(result)
                    pbar.set_postfix_str(f"OK {pdf_name}: {result['extracted_count']}/38")
                else:
                    errors.append(result)
                    pbar.set_postfix_str(f"ERR {pdf_name}")
            
            pbar.close()
    else:
        # Sequential processing
        for i, pdf_file in enumerate(sorted(pdf_files), 1):
            try:
                result = export_single_result(pdf_file, output_dir, save_db=save_db, quiet=False)
                results.append(result)
                print()
            except Exception as e:
                errors.append({'pdf_name': pdf_file.name, 'error': str(e)})
                print(f"  [ERR] Loi: {e}")
    
    print("="*60)
    print(f"✅ Hoàn thành: {len(results)}/{len(pdf_files)} files")
    if errors:
        print(f"❌ Lỗi: {len(errors)} files")
    
    # Tổng kết DB
    if save_db and results:
        total_records = sum(r.get('db_records', 0) for r in results)
        print(f"💾 Tổng: {total_records} records đã lưu vào DB")
    
    return results, errors


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='OCR extract PDF -> CSV + SQLite DB')
    parser.add_argument('path', nargs='?', default='./data/raw/filings',
                       help='PDF file hoặc folder')
    parser.add_argument('-o', '--output', default='./data/processed',
                       help='Output folder cho CSV')
    parser.add_argument('--no-db', action='store_true',
                       help='Không lưu vào SQLite DB')
    parser.add_argument('-p', '--parallel', action='store_true',
                       help='Chạy song song (parallel)')
    parser.add_argument('-w', '--workers', type=int, default=None,
                       help='Số worker cho parallel (mặc định: CPU-1)')
    args = parser.parse_args()
    
    path = Path(args.path)
    output = Path(args.output)
    save_db = not args.no_db
    
    if path.is_file():
        export_single_result(path, output, save_db=save_db)
    elif path.is_dir():
        process_folder(path, output, save_db=save_db, 
                      parallel=args.parallel, workers=args.workers)
    else:
        print(f"❌ Không tìm thấy: {path}")
