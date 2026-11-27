# HDVIA Beta 1.25.4.1 — Six Layer Data Fusion QA + Real-World Hardened

## Mục tiêu
Bổ sung QA và contract logic cho toàn bộ chuỗi 6 lớp mà không thay đổi UI hoặc module layout.

## 6 lớp
1. Source Registry — chính sách nguồn, license, attribution và trust.
2. Data Acquisition — ingest có giới hạn, chống SSRF và giữ nguồn ở trạng thái candidate.
3. Entity Resolution — chuẩn hóa tên, alias đa ngôn ngữ, fail-closed khi không đủ bằng chứng.
4. Visual Resolution — resolver ảnh đã có, chỉ VERIFIED khi đạt ngưỡng bằng chứng.
5. Knowledge Governance — DISCOVERED/CANDIDATE/REVIEWED/VERIFIED/PUBLISHED; external discovery không tự publish.
6. Knowledge Warehouse — record giữ provenance, freshness và layer trace.

## Freshness
Record có `retrieved_at`, `updated_at`, `expires_at` và trạng thái `FRESH/AGING/STALE/UNKNOWN`.

## QA
- 25 pytest tests + 8 subtests: PASS.
- Release contract: PASS.
- Runtime version synchronization: PASS.
- Bundled-secret scan: PASS.
- Forbidden build-artifact scan: PASS.
- Python compile check: PASS.

## Release hygiene
Đã loại `.pyc`, `.pyo`, `.DS_Store`, `__pycache__` và `.pytest_cache` khỏi release bundle.

## UI
Không thay đổi giao diện hoặc bố cục module.
