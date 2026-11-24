# HDVIA Data Acquisition & Controlled Learning

## Mục tiêu
Cho phép HDVIA thu thập dữ liệu từ các nguồn web/API được cấu hình và đưa dữ liệu mới vào pipeline kiểm duyệt mà không tự động xuất bản.

## Nguồn
- `web`: URL HTTP/HTTPS được chỉ định.
- `official_gov`: nguồn chính thức, ưu tiên `.gov.vn`.
- `google_cse`: Google Custom Search JSON API khi có `GOOGLE_CSE_API_KEY` + `GOOGLE_CSE_CX`. HDVIA không scrape HTML Google.

## Luồng
`SOURCE → FETCH → EXTRACT → CLASSIFY → LINEAGE → CANDIDATE → VALIDATED → REVIEWED → PUBLISHED`

External content luôn bắt đầu ở `CANDIDATE`.

## CLI
```bash
python scripts_data_acquisition.py --url https://example.gov.vn/article --kind knowledge
```

## Nguyên tắc
- Không ghi đè dữ liệu đã xuất bản.
- Không tự động publish dữ liệu external.
- Mọi candidate phải có nguồn và lineage.
- Có giới hạn kích thước/timeout.
- Không scrape Google HTML; dùng API chính thức nếu được cấu hình.
