"""
Main entry point cho finance38
Chạy pipeline: OCR -> External (Yahoo) -> Compute -> Export
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .db import Database, get_db, init_database
from .external import get_all_external_data
from .compute import compute_all_derived, validate_data, get_completeness_report
from .utils import load_mapping, get_founding_year


def export_individual_csvs(db: Database, output_dir: Path):
    """
    Export CSV riêng cho từng company-year với đầy đủ 38 index từ DB.
    Merge data từ tất cả sources: pdf, yahoo, computed, manual.
    """
    mapping = load_mapping()
    
    # Lấy danh sách company-year
    with db.get_connection() as conn:
        company_years = conn.execute("""
            SELECT DISTINCT company_code, year FROM finance_data ORDER BY company_code, year
        """).fetchall()
    
    for row in company_years:
        company = row['company_code']
        year = row['year']
        
        # Lấy data từ DB cho company-year này
        df_data = db.get_company_data(company, year)
        data_dict = {}
        if not df_data.empty:
            data_dict = dict(zip(df_data['index_id'], df_data['value']))
        
        # Tạo DataFrame với đủ 38 index
        rows = []
        for idx in sorted(mapping.keys()):
            config = mapping[idx]
            value = data_dict.get(idx, None)
            
            rows.append({
                'index_id': idx,
                'index_name': config.get('name', ''),
                'name_vn': config.get('name_vn', ''),
                'value': value,
                'unit': config.get('unit', ''),
                'source': config.get('source', '')
            })
        
        df = pd.DataFrame(rows)
        
        # Export
        csv_name = f"{company}_{year}_result.csv"
        csv_path = output_dir / csv_name
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    print(f"  ✓ Exported {len(company_years)} individual CSV files")


def run_pipeline(
    filings_path: Optional[Path] = None,
    skip_ocr: bool = False,
    skip_yahoo: bool = False,
    skip_compute: bool = False,
    export_csv: bool = True,
    parallel: bool = False,
    workers: Optional[int] = None
):
    """
    Chạy toàn bộ pipeline xử lý dữ liệu.
    
    Steps:
        1. Init database schema
        2. OCR Extract data từ PDF (run_ocr)
        3. Lấy external data (Yahoo Finance) 
        4. Compute derived indicators
        5. Export CSV
    """
    print("="*70)
    print("🚀 FINANCE38 PIPELINE")
    print("="*70)
    
    # 1. Init database
    print("\n[1/5] Khởi tạo database...")
    db = init_database()
    
    # Set paths
    root = Path(__file__).parent.parent
    if filings_path is None:
        filings_path = root / 'data' / 'raw' / 'filings'
    output_dir = root / 'data' / 'processed'
    
    # 2. OCR Extract từ PDF
    if not skip_ocr:
        print(f"\n[2/5] OCR Extract từ PDF...")
        
        if not filings_path.exists():
            print(f"⚠ Folder không tồn tại: {filings_path}")
        else:
            try:
                # Import run_ocr từ root
                from run_ocr import process_folder
                
                results, errors = process_folder(
                    filings_path,
                    output_dir=output_dir,
                    save_db=True,
                    parallel=parallel,
                    workers=workers
                )
                
                if errors:
                    print(f"  ⚠ {len(errors)} file lỗi")
                    
            except ImportError as e:
                print(f"  ⚠ Không import được run_ocr: {e}")
                print(f"  → Chạy riêng: python run_ocr.py -p")
    else:
        print("\n[2/5] Bỏ qua OCR (--skip-ocr)")
    
    # 3. External data (Yahoo Finance)
    if not skip_yahoo:
        print("\n[3/5] Lấy dữ liệu từ Yahoo Finance...")
        
        # Lấy danh sách company/year đã extract
        with db.get_connection() as conn:
            company_years = conn.execute("""
                SELECT DISTINCT company_code, year FROM finance_data
            """).fetchall()
        
        if not company_years:
            print("  ⚠ Chưa có dữ liệu PDF, skip Yahoo")
        else:
            mapping = load_mapping()
            count = 0
            
            for row in company_years:
                company = row['company_code']
                year = row['year']
                founding_year = get_founding_year(company)
                
                # Lấy external data (shares, market cap, firm age)
                ext_data = get_all_external_data(company, year, founding_year)
                
                for index_id, value in ext_data.items():
                    config = mapping.get(index_id, {})
                    db.upsert_value(
                        company_code=company,
                        year=year,
                        index_id=index_id,
                        index_name=config.get('name', f'Index {index_id}'),
                        value=value,
                        unit=config.get('unit', 'VND'),
                        source='yahoo'
                    )
                    count += 1
            
            print(f"  ✓ Đã lưu {count} records từ Yahoo")
    else:
        print("\n[3/5] Bỏ qua Yahoo Finance (--skip-yahoo)")
    
    # 4. Compute derived indicators
    if not skip_compute:
        print("\n[4/5] Tính toán derived indicators...")
        computed = compute_all_derived(db)
        print(f"  ✓ Đã tính {computed} giá trị")
    else:
        print("\n[4/5] Bỏ qua compute (--skip-compute)")
    
    # 5. Export
    print("\n[5/5] Export kết quả...")
    
    if export_csv:
        # Panel long
        db.export_panel_csv(format='long')
        # Panel wide  
        db.export_panel_csv(
            output_path=output_dir / 'panel_wide.csv',
            format='wide'
        )
        # Individual CSV files (đầy đủ 38 index từ tất cả sources)
        export_individual_csvs(db, output_dir)
        print(f"  📁 Output: {output_dir}")
    
    # Statistics
    stats = db.get_statistics()
    
    print("\n" + "="*70)
    print("📊 KẾT QUẢ")
    print("="*70)
    print(f"  • Số công ty:    {stats['n_companies']}")
    if stats['year_range'][0]:
        print(f"  • Khoảng năm:    {stats['year_range'][0]} - {stats['year_range'][1]}")
    print(f"  • Tổng records:  {stats['n_records']}")
    
    # Top indices filled
    completeness = get_completeness_report(db)
    if not completeness.empty:
        print("\n  Completeness (top 10):")
        top_filled = completeness.nlargest(10, 'fill_rate')
        for _, row in top_filled.iterrows():
            print(f"    [{int(row['index_id']):2d}] {row['index_name'][:35]:<35} {row['fill_rate']:>5.1f}%")
    
    print("\n" + "="*70)
    print("✅ HOÀN THÀNH!")
    print("="*70)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Finance38 - Extract 38 financial indicators from Vietnamese BCTC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python -m app.main                    # Chạy full pipeline
  python -m app.main -p                 # Chạy song song (nhanh hơn)
  python -m app.main --skip-ocr         # Chỉ chạy Yahoo + Compute
  python -m app.main --skip-yahoo       # Không lấy Yahoo Finance
  python -m app.main --stats            # Xem thống kê hiện tại
        """
    )
    
    parser.add_argument(
        '-f', '--filings',
        type=Path,
        help='Folder chứa PDF (mặc định: data/raw/filings)'
    )
    
    parser.add_argument(
        '-p', '--parallel',
        action='store_true',
        help='OCR song song (nhanh hơn)'
    )
    
    parser.add_argument(
        '-w', '--workers',
        type=int,
        help='Số worker cho parallel'
    )
    
    parser.add_argument(
        '--skip-ocr',
        action='store_true',
        help='Bỏ qua OCR extract PDF'
    )
    
    parser.add_argument(
        '--skip-yahoo',
        action='store_true',
        help='Bỏ qua Yahoo Finance'
    )
    
    parser.add_argument(
        '--skip-compute',
        action='store_true',
        help='Bỏ qua compute derived'
    )
    
    parser.add_argument(
        '--no-export',
        action='store_true',
        help='Không xuất CSV'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Xem thống kê database'
    )
    
    args = parser.parse_args()
    
    if args.stats:
        db = get_db()
        stats = db.get_statistics()
        print(f"Số công ty: {stats['n_companies']}")
        print(f"Khoảng năm: {stats['year_range']}")
        print(f"Tổng records: {stats['n_records']}")
        
        completeness = get_completeness_report(db)
        if not completeness.empty:
            print("\nCompleteness:")
            print(completeness.to_string())
        return
    
    run_pipeline(
        filings_path=args.filings,
        skip_ocr=args.skip_ocr,
        skip_yahoo=args.skip_yahoo,
        skip_compute=args.skip_compute,
        export_csv=not args.no_export,
        parallel=args.parallel,
        workers=args.workers
    )


if __name__ == '__main__':
    main()
