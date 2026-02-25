import os
from dotenv import load_dotenv
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import json
import time

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

class GeminiFinancialProcessor:
    def __init__(self):
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Cấu hình niên độ tài chính (Mặc định là 12-31, HSG là 09-30)
        self.FISCAL_YEAR_END = {
            "HSG": "09-30"
        }

        # Prompt mẫu gửi cho Gemini
        self.prompt = """
                Bạn là chuyên gia tài chính. Đọc Báo cáo tài chính này và trích xuất các chỉ tiêu sau.
                Trả về DUY NHẤT định dạng JSON. Không giải thích thêm.
                Đơn vị: Đồng (VND), định dạng số nguyên (bỏ dấu phân cách hàng nghìn).
                Nếu không có, để giá trị là null.

                {
                    "6. Total sales revenue and Net sales revenue": (Doanh thu thuần),
                    "7. Total assets": (Tổng cộng tài sản),
                    "8. Selling expenses": (Chi phí bán hàng),
                    "9. General and administrative expenditure": (Chi phí quản lý doanh nghiệp),
                    "10. Value of intangible assets": (Tài sản cố định vô hình),
                    "11. Manufacturing overhead": (Chi phí sản xuất chung),
                    "12. Net operating income": (Lợi nhuận thuần từ hoạt động kinh doanh),
                    "13. Consumption of raw material": (Chi phí nguyên liệu, vật liệu),
                    "14. Merchandise purchase of the year": (Mua hàng hóa),
                    "15. Work-in-progess goods purchase": (Chi phí sản xuất kinh doanh dở dang),
                    "16. Outside manufacturing expenses": (Chi phí dịch vụ mua ngoài),
                    "17. Production cost": (Giá vốn hàng bán),
                    "18. R&D expenditure": (Chi phí nghiên cứu phát triển),
                    "21. Net Income": (Lợi nhuận sau thuế),
                    "22. Total shareholders' equity": (Vốn chủ sở hữu),
                    "24. Total liabilities": (Nợ phải trả),
                    "25. Net cash from operating activities": (Lưu chuyển tiền thuần từ HĐKD),
                    "26. Capital expenditure": (Tiền chi mua sắm, xây dựng TSCĐ),
                    "27. Cash flows from investing activities": (Lưu chuyển tiền từ HĐ ĐT),
                    "28. Cash and cash equivalent": (Tiền và các khoản tương đương tiền cuối kỳ),
                    "29. Long-term debt": (Vay và nợ thuê tài chính dài hạn),
                    "30. Current assets": (Tài sản ngắn hạn),
                    "31. Current liabiltiies": (Nợ ngắn hạn),
                    "33. Total inventory": (Hàng tồn kho),
                    "34. Divident payment": (Cổ tức đã trả cho chủ sở hữu),
                    "35. EPS": (Lãi cơ bản trên cổ phiếu),
                    "37. Net plant, property and equipment": (Tài sản cố định hữu hình)
                }
                """

    def extract_from_pdf(self, pdf_path):
        print(f"   🤖 Đang gửi {os.path.basename(pdf_path)} cho Gemini AI...")
        
        max_retries = 5
        retry_delay = 65 
        
        for attempt in range(max_retries):
            try:
                sample_file = genai.upload_file(path=pdf_path, display_name=os.path.basename(pdf_path))
                
                while sample_file.state.name == "PROCESSING":
                    time.sleep(2)
                    sample_file = genai.get_file(sample_file.name)
                    
                if sample_file.state.name == "FAILED":
                    genai.delete_file(sample_file.name)
                    return {}

                response = self.model.generate_content(
                    [sample_file, self.prompt],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                genai.delete_file(sample_file.name)
                
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:-3]
                    
                result_dict = json.loads(raw_text)
                print("   ✅ Phân tích PDF thành công!")
                return result_dict
                
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "quota" in error_msg:
                    print(f"   ⏳ Chạm ngưỡng API. Đang ngủ {retry_delay} giây rồi thử lại (Lần {attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                else:
                    print(f"   ❌ Lỗi: {e}")
                    return {}
                    
        return {}

    def get_market_data(self, symbol, year):
        data = {}
        try:
            ticker = f"{symbol}.VN"
            stock = yf.Ticker(ticker)
            
            month_day = self.FISCAL_YEAR_END.get(symbol.upper(), "12-31")
            target_date = pd.to_datetime(f"{year}-{month_day}")
            start_date = (target_date - pd.Timedelta(days=15)).strftime("%Y-%m-%d")
            end_date = (target_date + pd.Timedelta(days=15)).strftime("%Y-%m-%d")
            
            hist = stock.history(start=start_date, end=end_date)
            if not hist.empty:
                if hist.index.tz is not None:
                    hist.index = hist.index.tz_localize(None)
                idx = hist.index.get_indexer([target_date], method='nearest')[0]
                close_price = hist.iloc[idx]['Close']
                shares = stock.info.get('sharesOutstanding', 0)
                
                data["5. Total share outstanding"] = shares
                data["23. Market value of equity"] = close_price * (shares if shares else 0)
            else:
                data["5. Total share outstanding"] = None
                data["23. Market value of equity"] = None
        except:
             data["5. Total share outstanding"] = None
             data["23. Market value of equity"] = None
        return data