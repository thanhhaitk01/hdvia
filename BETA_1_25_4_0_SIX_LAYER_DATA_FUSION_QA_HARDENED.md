# HDVIA Beta 1.25.4.0 — 6 Layer Data Fusion QA Hardened

## Mục tiêu
Chốt bản kế thừa từ Beta 1.25.3.0 để đưa lên GitHub/Vercel với runtime version đồng bộ và QA contract rõ ràng, không thay đổi giao diện hay module.

## 6 lớp giữ nguyên
1. Source Registry
2. Data Acquisition
3. Entity Resolution
4. Visual Resolution
5. Knowledge Fusion & Governance
6. HDVIA Knowledge Warehouse

## Hardening của 1.25.4.0
- Đồng bộ version runtime ở `VERSION`, API adapter, app health/inject và verified image resolver.
- Kiểm tra release không còn version runtime 1.25.3.0 bị sót.
- Kiểm tra không đóng gói `.pyc`, `__pycache__`, `.pytest_cache`, `.DS_Store` và secrets phổ biến.
- Regression suite hiện có phải pass.
- API live smoke là network-dependent; không coi lỗi mạng ngoài runtime là lỗi logic.
- Không thay đổi UI/module layout.
- External/discovered data vẫn giữ trạng thái CANDIDATE cho tới khi qua governance.

## Release QA
```bash
PYTHONPATH=. python -m unittest discover -s tests -p "test_*.py"
PYTHONPATH=. python release_qa.py
```

## Kết quả mong đợi
- Unit/regression tests: PASS.
- Release QA contract: PASS.
- Không có artefact thừa.
- Không có secret thật trong source.
