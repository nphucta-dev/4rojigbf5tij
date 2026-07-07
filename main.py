"""
Phần 1: Phân tích Input/Output
Input:
Tham sốVị tríKiểu dữ liệuBắt buộcshipment_idPath parameterint (hoặc str nếu mã vận đơn dạng "SPX123")Có
Output thành công (200 OK):
json{
  "status": "success",
  "message": "Lấy thông tin vận đơn thành công",
  "data": {
    "id": 1,
    "shipment_code": "SPX0001",
    "status_delivery": "in_transit",
    "created_at": "2026-07-01T10:00:00"
  }
}
Output thất bại (404 Not Found):
json{
  "status": "error",
  "message": "Không tìm thấy vận đơn với ID: 999999"
}

Phần 2: So sánh & Lựa chọn giải pháp
Tiêu chí so sánhGiải pháp 1: .all() + lọc PythonGiải pháp 2: .filter().first()Số bản ghi kéo lên RAM ServerKéo toàn bộ 100.000 bản ghi lên RAM, dựng thành 100.000 object PythonChỉ 1 bản ghi (hoặc 0) được đưa lên RAMCâu lệnh SQL sinh raSELECT * FROM shipments; (không LIMIT, không WHERE)SELECT * FROM shipments WHERE id = %s LIMIT 1;Nơi xử lý điều kiện lọcTầng ứng dụng (Python for/if) — CPU Python phải duyệt tuần tựTầng Database (MySQL Query Optimizer + Index) — tối ưu bằng B-Tree index trên khóa chínhTốc độ khi dữ liệu phình toTuyến tính O(n): 100.000 bản ghi → chậm dần, tốn RAM tỉ lệ thuận số dòngGần như O(log n) nhờ index, gần như không đổi dù bảng có 1 triệu dòngRủi ro hệ thốngCó thể gây OOM (Out of Memory) hoặc treo server khi nhiều request cùng lúc đều .all()Không có rủi ro OOM vì payload trả về cực nhỏBăng thông Server ↔ MySQLTốn băng thông truyền toàn bộ dữ liệu qua network dù chỉ cần 1 dòngChỉ truyền đúng 1 dòng dữ liệu cần thiếtBối cảnh phù hợpChỉ nên dùng khi thực sự cần xử lý/duyệt toàn bộ tập dữ liệu (ví dụ: export báo cáo, tính tổng)Dùng khi chỉ cần tìm 1 bản ghi duy nhất theo điều kiện (tra cứu theo ID, theo mã)
Kết luận lựa chọn: Chọn Giải pháp 2 (.filter().first()), vì:

Đẩy việc lọc dữ liệu xuống tầng Database — nơi có index và query optimizer chuyên xử lý việc này nhanh hơn Python hàng chục đến hàng trăm lần.
Giảm tải RAM Server — server API chỉ là nơi xử lý logic nghiệp vụ, không phải nơi chứa dữ liệu thô toàn bảng.
Khả năng chịu tải (Scalability) — với .all(), mỗi request đồng thời đều kéo hết 100.000 bản ghi → nhân với số lượng request/giây sẽ làm sập RAM server rất nhanh. .first() giữ chi phí mỗi request ở mức cố định (constant), không phụ thuộc kích thước bảng.
"""



from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from models import Shipment

app = FastAPI()


@app.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    try:
        # GIẢI PHÁP TỐI ƯU: .filter() + .first()
        # -> Sinh SQL: SELECT * FROM shipments WHERE id = :id LIMIT 1
        # -> Chỉ 1 bản ghi được kéo lên RAM, không phải toàn bộ 100.000 dòng
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()

        # Bẫy dữ liệu: không tìm thấy -> chặn lỗi chủ động, trả 404 chuẩn RESTful
        if shipment is None:
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy vận đơn với ID: {shipment_id}"
            )

        return {
            "status": "success",
            "message": "Lấy thông tin vận đơn thành công",
            "data": {
                "id": shipment.id,
                "shipment_code": shipment.shipment_code,
                "status_delivery": shipment.status_delivery,
                "created_at": shipment.created_at
            }
        }

    except HTTPException:
        # Bắt và ném lại HTTPException TRƯỚC khi rơi vào except Exception bên dưới
        # (tránh bug quen thuộc: except Exception nuốt mất lỗi 404 rồi trả về 500)
        raise
    except SQLAlchemyError:
        # Lỗi kết nối/truy vấn DB -> không lộ stack trace thô ra ngoài
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi truy vấn dữ liệu")