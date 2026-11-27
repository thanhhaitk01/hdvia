# HDVIA Beta 1.30.0 — Travel Intelligence Brain

## Mục tiêu
Nâng HDVIA từ hệ thống thu thập và trả lời thông tin điểm đến thành một **bộ não phân tích du lịch dành cho HDV**.

## Nguyên tắc
- Hành Trình AI vẫn là cửa vào chính; không tạo module UI độc lập mới.
- Não du lịch đứng giữa Deep World Research/Knowledge Fusion và lớp hiển thị.
- Mọi kết luận phải phân biệt dữ liệu đã có nguồn, dữ liệu tham khảo và khoảng trống cần kiểm tra.
- Không tự bịa dữ kiện để làm câu trả lời đầy đủ.

## 8 nhóm đối tượng lõi
FESTIVAL, RELIGIOUS_SITE, HERITAGE_SITE, NATURAL_SITE, FOOD, CRAFT_VILLAGE, PERSON, CITY_OR_DESTINATION; nếu chưa nhận diện được thì UNKNOWN.

## Với mỗi đối tượng
1. Nhận diện đối tượng.
2. Xác định kế hoạch nghiên cứu phù hợp với đối tượng.
3. Xác định giá trị thông tin đối với khách.
4. Liên hệ bối cảnh địa phương.
5. Đọc tín hiệu thời tiết/rủi ro.
6. Sinh hành động vận hành cho HDV.
7. Nêu khoảng trống tri thức cần kiểm tra.
8. Đóng gói thành brief để lớp hiển thị sử dụng.

## Ví dụ
### Đền/chùa
Ưu tiên lịch sử, nguồn gốc tín ngưỡng, nhân vật, kiến trúc, nghi lễ, quy tắc ứng xử, giờ tham quan, thời tiết và khả năng tiếp cận.

### Lễ hội
Ưu tiên nguồn gốc, thời gian, địa điểm, nghi lễ, hoạt động, cộng đồng, quy mô, giao thông, an toàn và thời tiết.

### Món ăn
Ưu tiên nguồn gốc, nguyên liệu, cách chế biến/thưởng thức, địa phương, câu chuyện văn hóa và lưu ý dị ứng/kiêng kỵ.

## Mục tiêu vận hành cho HDV
HDVIA không chỉ trả lời "đây là gì?" mà phải hỗ trợ câu hỏi thực tế:
- Khách cần biết gì?
- Nên kể câu chuyện nào?
- Cần chuẩn bị gì?
- Có rủi ro gì?
- Nếu điều kiện thay đổi thì xử lý thế nào?
- Thông tin nào còn cần xác minh?

## QA
`pytest -q tests` phải đạt toàn bộ test hiện có và test mới của Travel Intelligence Brain.
