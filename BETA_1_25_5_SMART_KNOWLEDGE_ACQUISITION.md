# HDVIA Beta 1.25.5 — Smart Knowledge Acquisition

Bản này giữ nguyên UI/module hiện tại và nâng cấp lớp dữ liệu:

- Smart Knowledge Acquisition: lấy dữ liệu tham khảo theo địa điểm từ Wikidata, Wikipedia tiếng Việt/Anh, OpenStreetMap và bộ xác minh ảnh hiện có.
- Knowledge Gap: chỉ gọi enrichment khi thẻ điểm đến còn thiếu chiều sâu.
- Source-aware profile: lưu nguồn, độ tin cậy, thời điểm thu thập và trạng thái REFERENCE/CANDIDATE.
- Không tự suy diễn lịch sử/văn hóa/ẩm thực khi nguồn không cung cấp.
- Không tự dùng ảnh ngẫu nhiên: ảnh live vẫn đi qua VerifiedImageResolver và ngưỡng xác minh.
- Endpoint: `/api/v1/knowledge/enrich?q=...` cho kiểm tra/thu thập theo một điểm.
- Journey AI tự dùng enrichment có giới hạn cho các điểm còn thiếu dữ liệu, nhưng không thay thế dữ liệu curated đã có.

## Nguyên tắc phát hành
External data is evidence, not truth. Candidate/reference data is never silently promoted to verified knowledge.
