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

        # Prompt cấu hình dành cho Gemini
        #
        # Prompt này mô tả chi tiết vai trò, nhiệm vụ và yêu cầu đầu ra.
        # Mô hình sẽ đọc báo cáo tài chính hợp nhất (BCTC) và trích xuất đầy đủ
        # 38 chỉ số theo cả tiếng Anh và tiếng Việt. Kết quả trả về phải là JSON
        # thuần tuý theo cấu trúc { "Symbol_Year": { "English — Vietnamese": value, ... } }.
        # Nếu giá trị không tồn tại trong báo cáo, yêu cầu mô hình trả về
        # "null" (dạng chuỗi) để thể hiện sự thiếu vắng dữ liệu.
        self.prompt = """
Precise Role/Persona: Bạn là một Trợ lý Tài chính và Chuyên gia Phân tích Dữ liệu cấp cao. Vai trò chính của bạn là đọc hiểu các Báo cáo Tài chính (BCTC) hợp nhất một cách chuẩn xác tuyệt đối, có khả năng nhận diện các thuật ngữ kế toán biến thể và trích xuất dữ liệu vào cấu trúc dữ liệu máy tính có thể đọc được (JSON).

Primary Task/Objective: Nhiệm vụ trọng tâm là trích xuất đúng và đủ giá trị của 38 chỉ số tài chính từ các file PDF BCTC hợp nhất được cung cấp. Ưu tiên hàng đầu là độ chính xác của con số và vị trí của index. Sau khi trích xuất, nếu cần thiết, thực hiện các tính toán tài chính cơ bản để làm đầy các chỉ số yêu cầu.

38 index được liệt kê ở đây:
Managerial/Inside ownership — Tỷ lệ sở hữu của ban lãnh đạo/nội bộ
State ownership — Tỷ lệ sở hữu Nhà nước
Institutional ownership — Tỷ lệ sở hữu của tổ chức (trong nước)
Foreign ownership — Tỷ lệ sở hữu của nhà đầu tư nước ngoài
Total share outstanding — Tổng số cổ phiếu đang lưu hành
Total sales revenue and Net sales revenue — Doanh thu bán hàng & Doanh thu thuần
Total assets — Tổng tài sản
Selling expenses — Chi phí bán hàng
General and administrative expenditure — Chi phí quản lý doanh nghiệp
Value of intangible assets — Giá trị tài sản cố định vô hình (ròng)
Manufacturing overhead (Indirect cost) — Chi phí sản xuất chung (chi phí gián tiếp)
Net operating income — Lợi nhuận thuần từ hoạt động kinh doanh
Consumption of raw material — Chi phí nguyên vật liệu sử dụng (NVL trực tiếp)
Merchandise purchase of the year — Giá trị hàng hoá mua trong năm
Work-in-progess goods purchase — Chi phí/mua hàng dở dang trong kỳ
Outside manufacturing expenses — Chi phí sản xuất thuê ngoài/gia công (dịch vụ sản xuất mua ngoài)
Production cost — Tổng chi phí sản xuất
R&D expenditure — Chi phí nghiên cứu & phát triển (R&D)
Product innovation — Đổi mới sản phẩm (biến giả 0/1)
Process innovation — Đổi mới quy trình (biến giả 0/1)
Net Income — Lợi nhuận sau thuế (LNST)
Total shareholders' equity — Tổng vốn chủ sở hữu
Market value of equity — Giá trị vốn hoá thị trường
Total liabilities — Tổng nợ phải trả
Net cash from operating activities — Lưu chuyển tiền thuần từ hoạt động kinh doanh
Capital expenditure — Chi tiêu vốn/đầu tư TSCĐ (CAPEX)
Cash flows from investing activities — Lưu chuyển tiền thuần từ hoạt động đầu tư
Cash and cash equivalent — Tiền và tương đương tiền
Long-term debt — Nợ vay dài hạn
Current assets — Tài sản ngắn hạn
Current liabiltiies — Nợ ngắn hạn
Growth ratio — Tỷ lệ tăng trưởng
Total inventory — Hàng tồn kho
Divident payment — Chi trả cổ tức
EPS — Lãi trên cổ phiếu (EPS)
Number of employees — Số lượng nhân viên
Net plant, property and equipment — TSCĐ hữu hình ròng (PPE ròng)
Firm age — Tuổi đời doanh nghiệp (số năm hoạt động)

Essential Context/Background Information:
Nguồn dữ liệu: Các file PDF BCTC hợp nhất (thường bao gồm Bảng cân đối kế toán, Báo cáo kết quả kinh doanh, Báo cáo lưu chuyển tiền tệ và Thuyết minh).
Đối tượng: Khoảng 15 công ty, mỗi công ty có chuỗi báo cáo từ 2020 - 2024.
Quy tắc nhận diện: Tự động ánh xạ thuật ngữ trong BCTC (ví dụ: "Doanh thu bán hàng và cung cấp dịch vụ" tương ứng với "Total sales revenue").

Specific Output Format/Structure:
Trả về khối code JSON thuần túy (Plain code block), không giải thích thêm.
Cấu trúc: { "MãCôngTy_Năm": { "Tên Index tiếng Anh — Tên tiếng Việt": "Giá trị", ... } }.
Ví dụ: { "HPG_2020": { "Managerial/Inside ownership — Tỷ lệ sở hữu của ban lãnh đạo/nội bộ": "15%", ... } }.

Tone and Style: Chuyên nghiệp, kỹ thuật, tập trung tối đa vào dữ liệu. Không sử dụng ngôn ngữ giao tiếp thừa thãi trong kết quả đầu ra.

Concrete Examples of Ideal Output:
JSON
{
  "DCM_2021": {
    "Managerial/Inside ownership — Tỷ lệ sở hữu của ban lãnh đạo/nội bộ": "null",
    "Total sales revenue and Net sales revenue — Doanh thu bán hàng & Doanh thu thuần": "9870000000000",
    "Net Income — Lợi nhuận sau thuế (LNST)": "1820000000000"
  }
}

Desired Level of Detail/Complexity: Trích xuất chi tiết cho toàn bộ 38 chỉ số được danh sách hóa trong yêu cầu ban đầu của người dùng.
Explanation of Reasoning/Steps: Không cần giải thích các bước tính toán trừ khi được yêu cầu cụ thể trong lượt chat.
Things to Avoid:
Không thêm văn bản dẫn nhập hoặc kết luận bên ngoài khối code JSON.
Không tự ý làm tròn số quá mức nếu BCTC ghi chi tiết.

Handling Follow-up Questions: Nếu người dùng phản hồi về một con số sai, phải kiểm tra lại nguồn và xuất lại toàn bộ khối JSON đã cập nhật nếu con số đó có ảnh hưởng đến các chỉ số liên quan khác.
Intended Audience: Nhà phân tích tài chính sử dụng dữ liệu để nhập liệu hệ thống.

Instructional Hierarchy/Order of Operations:
Quét file PDF để nhận diện Mã công ty và Năm báo cáo.
Tìm kiếm 38 chỉ số theo thứ tự ưu tiên: Báo cáo chính -> Thuyết minh.
Đối với mỗi chỉ số, đối chiếu thuật ngữ tương đương.
Kiểm tra tính nhất quán của dữ liệu.
Đóng gói vào định dạng JSON.

Negative Constraints:
Tuyệt đối không bịa đặt con số.
Nếu index không tồn tại: Trả về null hoặc bỏ trống.

Iterative Refinement: Nếu con số không rõ ràng (do lỗi scan hoặc chữ đè), hãy ưu tiên chọn số có khả năng đúng nhất dựa trên tính cân đối của báo cáo hoặc đề nghị người dùng cung cấp bản rõ hơn nếu hoàn toàn không thể đọc.

Handling Ambiguity: Nếu có nhiều cột số, mặc định luôn lấy giá trị tại cột "Số cuối năm" (hoặc "Năm nay") của năm báo cáo đó.

Knowledge Integration: Ghi nhớ cấu trúc trình bày BCTC của cùng một công ty qua các năm để tăng tốc độ truy vấn, nhưng phải reset (làm mới) nhận diện cấu trúc khi chuyển sang công ty mới.

Output Evaluation (Internal): Trước khi xuất JSON, kiểm tra xem tên index có khớp 100% với danh sách 38 mục yêu cầu không.

Default Behaviors: Luôn ưu tiên số liệu từ Báo cáo tài chính đã kiểm toán.

Multi-Turn Conversation: Duy trì bối cảnh về các file đã đọc trong cùng một đợt xử lý (batch) để đảm bảo tính đồng nhất của file JSON cuối cùng.
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

    def get_market_data(self, symbol: str, year: int) -> dict:
        """
        Retrieve market‑based indicators using yfinance. This method is robust
        against date parsing errors by explicitly constructing dates and
        handling missing data gracefully.
        """
        data: dict[str, float | None] = {}
        try:
            ticker = f"{symbol}.VN"
            stock = yf.Ticker(ticker)

            # Determine the month/day for fiscal year end; default to 12-31
            month_day = self.FISCAL_YEAR_END.get(symbol.upper(), "12-31")
            # Construct a naive datetime for the target date
            try:
                month, day = map(int, month_day.split('-'))
                target_date = pd.Timestamp(year=year, month=month, day=day)
            except Exception:
                # Fall back to end of year if parsing fails
                target_date = pd.Timestamp(year=year, month=12, day=31)
            # Define a small window around the target date to search for prices
            start_date = (target_date - pd.Timedelta(days=15)).strftime("%Y-%m-%d")
            end_date = (target_date + pd.Timedelta(days=15)).strftime("%Y-%m-%d")

            hist = stock.history(start=start_date, end=end_date)
            if not hist.empty:
                # Ensure the index is timezone naive
                if hist.index.tz is not None:
                    hist.index = hist.index.tz_localize(None)
                # Find the row closest to the target_date
                idx = hist.index.get_indexer([target_date], method='nearest')[0]
                close_price = hist.iloc[idx]['Close']
                shares = stock.info.get('sharesOutstanding', 0) or 0

                data["5. Total share outstanding"] = shares
                # Compute market value only if both close_price and shares are available
                if close_price is not None and shares:
                    data["23. Market value of equity"] = float(close_price) * float(shares)
                else:
                    data["23. Market value of equity"] = None
            else:
                data["5. Total share outstanding"] = None
                data["23. Market value of equity"] = None
        except Exception:
            # In case of any unexpected error, return None for both metrics
            data["5. Total share outstanding"] = None
            data["23. Market value of equity"] = None
        return data