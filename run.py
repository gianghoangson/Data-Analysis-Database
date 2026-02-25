import os
import time
import pandas as pd
import numpy as np
from typing import Any

# Nhập các module đã tự viết
from gemini_pdf import GeminiFinancialProcessor
from compute import apply_calculations

BCTC_PATH = "./BCTC"
RESULT_FOLDER = "./finance38/data/result"

# TỪ ĐIỂN CẤU HÌNH GIAO DIỆN (Định hình 6 cột cho file CSV)
METADATA_CONFIG = {
    "1. Managerial ownership": {"name_vn": "Sở hữu của ban điều hành", "unit": "%", "source": "manual"},
    "2. State ownership": {"name_vn": "Sở hữu nhà nước", "unit": "%", "source": "manual"},
    "3. Institutional ownership": {"name_vn": "Sở hữu tổ chức", "unit": "%", "source": "manual"},
    "4. Foreign ownership": {"name_vn": "Sở hữu nước ngoài", "unit": "%", "source": "manual"},
    "5. Total share outstanding": {"name_vn": "Tổng số cổ phiếu lưu hành", "unit": "shares", "source": "yahoo"},
    "6. Total sales revenue and Net sales revenue": {"name_vn": "Doanh thu thuần", "unit": "VND", "source": "pdf"},
    "7. Total assets": {"name_vn": "Tổng tài sản", "unit": "VND", "source": "pdf"},
    "8. Selling expenses": {"name_vn": "Chi phí bán hàng", "unit": "VND", "source": "pdf"},
    "9. General and administrative expenditure": {"name_vn": "Chi phí quản lý doanh nghiệp", "unit": "VND", "source": "pdf"},
    "10. Value of intangible assets": {"name_vn": "Tài sản cố định vô hình", "unit": "VND", "source": "pdf"},
    "11. Manufacturing overhead": {"name_vn": "Chi phí sản xuất chung", "unit": "VND", "source": "pdf"},
    "12. Net operating income": {"name_vn": "Lợi nhuận thuần từ hoạt động kinh doanh", "unit": "VND", "source": "pdf"},
    "13. Consumption of raw material": {"name_vn": "Chi phí nguyên vật liệu", "unit": "VND", "source": "pdf"},
    "14. Merchandise purchase of the year": {"name_vn": "Mua hàng hóa", "unit": "VND", "source": "pdf"},
    "15. Work-in-progess goods purchase": {"name_vn": "Chi phí sản xuất kinh doanh dở dang", "unit": "VND", "source": "pdf"},
    "16. Outside manufacturing expenses": {"name_vn": "Chi phí dịch vụ mua ngoài", "unit": "VND", "source": "pdf"},
    "17. Production cost": {"name_vn": "Tổng chi phí sản xuất", "unit": "VND", "source": "pdf"},
    "18. R&D expenditure": {"name_vn": "Chi phí nghiên cứu phát triển", "unit": "VND", "source": "pdf"},
    "19. Product innovation": {"name_vn": "Đổi mới sản phẩm", "unit": "binary", "source": "manual"},
    "20. Process innovation": {"name_vn": "Đổi mới quy trình", "unit": "binary", "source": "manual"},
    "21. Net Income": {"name_vn": "Lợi nhuận sau thuế", "unit": "VND", "source": "pdf"},
    "22. Total shareholders' equity": {"name_vn": "Vốn chủ sở hữu", "unit": "VND", "source": "pdf"},
    "23. Market value of equity": {"name_vn": "Vốn hóa thị trường", "unit": "VND", "source": "yahoo"},
    "24. Total liabilities": {"name_vn": "Nợ phải trả", "unit": "VND", "source": "pdf"},
    "25. Net cash from operating activities": {"name_vn": "Lưu chuyển tiền thuần từ HĐKD", "unit": "VND", "source": "pdf"},
    "26. Capital expenditure": {"name_vn": "Chi mua sắm TSCĐ", "unit": "VND", "source": "pdf"},
    "27. Cash flows from investing activities": {"name_vn": "Lưu chuyển tiền từ HĐĐT", "unit": "VND", "source": "pdf"},
    "28. Cash and cash equivalent": {"name_vn": "Tiền và tương đương tiền", "unit": "VND", "source": "pdf"},
    "29. Long-term debt": {"name_vn": "Vay và nợ thuê tài chính dài hạn", "unit": "VND", "source": "pdf"},
    "30. Current assets": {"name_vn": "Tài sản ngắn hạn", "unit": "VND", "source": "pdf"},
    "31. Current liabiltiies": {"name_vn": "Nợ ngắn hạn", "unit": "VND", "source": "pdf"},
    "32. Growth ratio": {"name_vn": "Tỷ lệ tăng trưởng", "unit": "%", "source": "computed"},
    "33. Total inventory": {"name_vn": "Hàng tồn kho", "unit": "VND", "source": "pdf"},
    "34. Divident payment": {"name_vn": "Cổ tức đã trả", "unit": "VND", "source": "pdf"},
    "35. EPS": {"name_vn": "Lãi cơ bản trên cổ phiếu", "unit": "VND", "source": "pdf"},
    "36. Number of employees": {"name_vn": "Số lượng nhân viên", "unit": "người", "source": "manual"},
    "37. Net plant, property and equipment": {"name_vn": "Tài sản cố định hữu hình", "unit": "VND", "source": "pdf"},
    "38. Firm age": {"name_vn": "Tuổi công ty", "unit": "years", "source": "computed"}
}

ALL_FIELDS = list(METADATA_CONFIG.keys())

def get_pdf_files(root_dir):
    pdf_list = []
    if os.path.exists(root_dir):
        for company_code in os.listdir(root_dir):
            comp_path = os.path.join(root_dir, company_code)
            if os.path.isdir(comp_path):
                for file in os.listdir(comp_path):
                    if file.lower().endswith(".pdf"):
                        try:
                            year = int(file.replace(".pdf", "").split("_")[-1])
                            pdf_list.append({"Symbol": company_code, "Year": year, "FilePath": os.path.join(comp_path, file)})
                        except:
                            pass
    return pdf_list

def run_pipeline():
    if not os.path.exists(RESULT_FOLDER):
        os.makedirs(RESULT_FOLDER)

    processor = GeminiFinancialProcessor()
    pdf_files = get_pdf_files(BCTC_PATH)
    
    if not pdf_files:
        print("❌ Không tìm thấy PDF trong thư mục BCTC")
        return

    print(f"🚀 BẮT ĐẦU XỬ LÝ {len(pdf_files)} FILE BÁO CÁO...")

    # Process each file one by one and write results immediately
    processed_rows: list[dict] = []

    for idx, item in enumerate(pdf_files):
        symbol = item['Symbol']
        year = item['Year']
        pdf_path = item['FilePath']
        output_csv = os.path.join(RESULT_FOLDER, f"{symbol}_{year}_result.csv")

        print(f"\n[{idx+1}/{len(pdf_files)}] Đang xử lý: {symbol} - {year}")

        # Initialise row with all indicators set to None
        row_data: dict[str, Any] = {"Symbol": symbol, "Year": year}
        for field in ALL_FIELDS:
            row_data[field] = None

        need_ai = True

        # If CSV exists, read existing values and avoid API call
        if os.path.exists(output_csv):
            print(f"   📂 Đã có file cũ, đang đọc dữ liệu nhập tay...")
            try:
                df_old = pd.read_csv(output_csv)
                old_dict: dict[str, Any] = {}
                if 'index_id' in df_old.columns and 'value' in df_old.columns:
                    for _, r in df_old.iterrows():
                        key = f"{int(r['index_id'])}. {r['index_name']}"
                        old_dict[key] = r['value']
                elif 'Indicator' in df_old.columns and 'Value' in df_old.columns:
                    old_dict = df_old.set_index('Indicator')['Value'].to_dict()
                if pd.notna(old_dict.get("7. Total assets")):
                    need_ai = False
                    print("   ⏭️ File này đã chạy AI trước đó, sẽ bỏ qua gọi API.")
                for key in ALL_FIELDS:
                    val = old_dict.get(key)
                    if pd.notna(val) and str(val).strip() != "":
                        row_data[key] = val
            except Exception as e:
                print(f"   ⚠️ Lỗi đọc file cũ: {e}")

        if need_ai:
            pdf_data = processor.extract_from_pdf(pdf_path)
            market_data = processor.get_market_data(symbol, year)

            # Build mapping of English names to field keys (with parentheses stripped)
            english_to_field: dict[str, str] = {}
            for field_key in ALL_FIELDS:
                parts = field_key.split('. ', 1)
                if len(parts) == 2:
                    english_name = parts[1].strip()
                    english_to_field[english_name] = field_key
                    if '(' in english_name:
                        english_clean = english_name.split('(', 1)[0].strip()
                        english_to_field.setdefault(english_clean, field_key)

            # Parse the PDF JSON and fill row_data
            if isinstance(pdf_data, dict):
                for _, indicators in pdf_data.items():
                    if isinstance(indicators, dict):
                        for full_name, value in indicators.items():
                            if not isinstance(full_name, str):
                                continue
                            if ' — ' in full_name:
                                english_name = full_name.split(' — ', 1)[0].strip()
                            elif ' - ' in full_name:
                                english_name = full_name.split(' - ', 1)[0].strip()
                            else:
                                english_name = full_name.strip()
                            english_clean = english_name.split('(', 1)[0].strip()
                            field_key = english_to_field.get(english_name) or english_to_field.get(english_clean)
                            if field_key:
                                if value is not None:
                                    row_data[field_key] = value

            # Merge market data
            for k, v in market_data.items():
                if k in ALL_FIELDS and v is not None:
                    row_data[k] = v

            time.sleep(5)

        # Append row and compute derived metrics
        processed_rows.append(row_data.copy())
        df_all = pd.DataFrame(processed_rows)
        df_all = apply_calculations(df_all)
        df_row = df_all.iloc[-1]

        # Write out CSV for this file immediately
        formatted_rows: list[dict[str, Any]] = []
        for field in ALL_FIELDS:
            parts = field.split('. ', 1)
            index_id = int(parts[0])
            index_name = parts[1]
            meta = METADATA_CONFIG[field]
            val = df_row.get(field)
            formatted_rows.append({
                "index_id": index_id,
                "index_name": index_name,
                "name_vn": meta["name_vn"],
                "value": val,
                "unit": meta["unit"],
                "source": meta["source"]
            })
        df_final = pd.DataFrame(formatted_rows)
        df_final = df_final.sort_values(by="index_id")
        df_final.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"   ✅ Đã xuất: {symbol}_{year}_result.csv")

    print("\n🎉🎉🎉 HOÀN TẤT TOÀN BỘ QUY TRÌNH!")

if __name__ == "__main__":
    run_pipeline()