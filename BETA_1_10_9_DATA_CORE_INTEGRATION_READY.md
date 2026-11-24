# HDVIA Beta 1.10.9 — Data Core Integration Ready

## Chốt kiến trúc
- 8 kho dữ liệu là các nguồn dữ liệu chuyên biệt (system of record).
- Không tạo kho trung tâm thứ 9 để sao chép dữ liệu.
- `DataCoreBridge` là lớp điều phối/liên kết đọc dữ liệu.
- Quan hệ nhiều-nhiều: một kho phục vụ nhiều module; một module có thể dùng nhiều kho.

## Đã tích hợp
- Journey Intelligence → Data Core → 8 kho liên quan.
- AI Copilot nhận `data_context` từ Journey/Data Core.
- AI Agent nhận cùng context và báo cáo domain dữ liệu khả dụng.
- Destination/Admin/Knowledge/Experience/Weather-Risk/Market/Lineage được nối bằng stable IDs.
- Unknown destination không tự đoán liên kết.
- Lineage vẫn đi cùng record.
- Legacy warehouse routes/collections được giữ nguyên.

## Kiểm thử
- `66 passed` regression tests.
- `python -m compileall -q .` → PASS.
- Static route/contract checks → PASS.
- Runtime Flask live test: môi trường đóng gói hiện tại không có Flask package; `requirements.txt` vẫn pin Flask 3.1.0. Không ghi nhận giả là live Vercel đã chạy.

## Deploy
1. Upload ZIP lên GitHub.
2. Commit message: `HDVIA BETA 1.10.9 DATA CORE INTEGRATION READY`
3. Vercel build theo `vercel.json` + `requirements.txt`.
4. Sau deploy kiểm tra `/health`, `/__version`, Journey, Copilot và Agent.
