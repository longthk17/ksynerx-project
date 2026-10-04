# KSynerX — Prototype

Prototype gồm một Inventory Service giả lập nguồn sản phẩm và một Change Data Management Service (CDMS) thu thập dữ liệu qua polling hoặc Excel. CDMS lưu phiên bản nội dung mới và tránh insert trùng khi nhận lại cùng dữ liệu.

## Tài liệu hướng dẫn

- [Chạy source](docs/run-prototype.md): clone/pull code, cấu hình `.env`, khởi chạy và dừng Docker Compose.
- [Chạy thử API](docs/test-prototype.md): tạo/lấy sản phẩm, upload Excel và kiểm tra polling thủ công hoặc theo lịch.
- [File Excel mẫu](products_sample_10.xlsx): dữ liệu dùng để thử API upload Excel.

## Tech stack

| Thành phần | Công nghệ | Vai trò |
| --- | --- | --- |
| Backend | Python 3.11, Django, Django REST Framework | Xây dựng Inventory/CDM Service và REST API |
| Database | PostgreSQL 16, Django ORM, Psycopg | Lưu sản phẩm, phiên bản dữ liệu và ràng buộc chống trùng |
| Tác vụ nền | Celery Worker, Celery Beat | Xử lý Excel, polling định kỳ và retry |
| Cache và hàng đợi | Redis 7 | Cache, broker và result backend cho Celery |
| Xử lý dữ liệu | OpenPyXL, Requests, Arrow | Đọc Excel, gọi Inventory API và xử lý thời gian |
| Container | Docker, Docker Compose | Đóng gói và chạy các service |
| Frontend (chưa hoàn thành) | React 19, Vite 7 | Bản nháp giao diện thao tác prototype |

## 1. Inventory Service

Giả lập hệ thống quản lý sản phẩm, sử dụng database **`inventory`** trong container `inventory-db`. Schema theo model [Product](backend/inventory-service/my_app/models/product.py) và [BaseModel](backend/inventory-service/my_app/models/models.py):

```dbml
Table my_app_product {
  id bigint [pk, increment]

  sku varchar(100) [not null, unique]
  partner_sku varchar(100)
  product_name varchar(255) [not null]

  unit_code varchar(50) [not null]
  unit_name varchar(100) [not null]

  serial_type integer [not null]
  is_expiry_date boolean [not null, note: 'Django default=False']

  categories jsonb [not null, note: 'Mảng danh mục; Django default=list (mảng rỗng)']
  product_units jsonb [not null, note: 'Mảng đơn vị tính và quy đổi; Django default=list (mảng rỗng)']

  created_at timestamptz [not null, note: 'Django auto_now_add=True']
  updated_at timestamptz [not null, note: 'Django auto_now=True']

  indexes {
    (updated_at, id) [name: 'product_update_at_id_idx']
  }
}
```

### API

Các endpoint hiện dùng prefix `/api/v1` và không có dấu `/` ở cuối URL.

| Method | Endpoint | Chức năng |
| --- | --- | --- |
| POST | `/api/v1/product` | Tạo danh sách sản phẩm bằng payload mảng |
| GET | `/api/v1/product` | Lấy danh sách với filter và pagination |
| GET | `/api/v1/product-query-all` | Truy vấn sản phẩm theo thời gian cập nhật để CDMS polling |

Bộ lọc gồm `Keyword`, `SKUs`, `PartnerSKUs`; phân trang dùng `PageIndex` bắt đầu từ 0 và `PageSize`. API polling nhận `updatedFrom`, `updatedTo`, lấy dữ liệu trong khoảng `[updatedFrom, updatedTo)`.

## 2. Change Data Management Service

CDMS sử dụng database **`cdm`** trong container `cdm-db`, tiếp nhận dữ liệu từ Inventory hoặc Excel. Schema theo model [ChangeData](backend/cdm-service/my_app/models/change_data.py) và [BaseModel](backend/cdm-service/my_app/models/models.py):

```dbml
Table my_app_changedata {
  id bigint [pk, increment]

  sku varchar(100) [not null]
  partner_sku varchar(100)
  product_name varchar(255) [not null]

  unit_code varchar(50) [not null]
  unit_name varchar(100) [not null]

  serial_type integer [not null]
  is_expiry_date boolean [not null, note: 'Django default=False']

  categories jsonb [not null, note: 'Django default=list (mảng rỗng)']
  product_units jsonb [not null, note: 'Django default=list (mảng rỗng)']

  hash_value varchar(255) [not null, unique]

  created_at timestamptz [not null, note: 'Django auto_now_add=True']
  updated_at timestamptz [not null, note: 'Django auto_now=True']
}
```

Trong CDM, chỉ `hash_value` có ràng buộc unique ngoài khóa chính; SKU có thể lặp lại ở các phiên bản nội dung khác nhau. Cột hash dài tối đa 255 ký tự theo model, còn giá trị SHA-256 sinh ra dài 64 ký tự. Model hiện không có `received_via`.

Hai schema dùng tên bảng mặc định của Django. Default và timestamp trong ghi chú được xử lý bởi Django, không phải database default `now()` hoặc trigger. `serial_type` là NOT NULL dù model đặt `blank=True, default=None`; khi lưu phải cung cấp giá trị integer hợp lệ. Tên database được cấu hình qua `DB_NAME`; Compose đặt lần lượt là `inventory` và `cdm`.

### API và tác vụ nền

| Method | Endpoint | Chức năng |
| --- | --- | --- |
| POST | `/api/v1/upload-excel` | Upload Excel, xếp hàng xử lý và insert dữ liệu vào CDM |
| GET | `/api/v1/product-polling-check` | Chạy kiểm tra polling thủ công, lấy dữ liệu Inventory và insert vào CDM |

Upload nhận file `.xlsx` qua multipart field `file`; workbook gồm ba sheet `products`, `categories`, `product_units`, liên kết bằng SKU. API trả HTTP 202 và taskId khi xếp hàng; Celery Worker đọc file, validate và lưu dữ liệu.

Polling theo lịch được thực hiện riêng bằng **Celery Beat → Celery Worker**, không phải do GET endpoint tạo lịch. Beat hiện chạy mỗi phút. Endpoint polling thủ công còn cần hoàn thiện khoảng thời gian truy vấn và xử lý lỗi.

## 3. Lưu dữ liệu mới và chống trùng

- Chuẩn hóa nội dung sản phẩm, sắp xếp danh mục và đơn vị quy đổi rồi tính hash SHA-256.
- Dùng `get_or_create` theo `hash_value` có ràng buộc unique trong database.
- Hash đã tồn tại thì bỏ qua; hash mới thì lưu phiên bản mới, tránh insert trùng khi gửi lại hoặc retry.

## 4. Xử lý lỗi và retry

- Retry tối đa **3 lần**, chờ **60 giây** trước mỗi lần thử lại.
- Polling: đặt timeout, retry khi timeout hoặc lỗi kết nối HTTP/database.
- Excel: retry khi gặp lỗi kết nối database.
- Không tự retry lỗi validation.
- Lưu batch trong transaction, ghi log lỗi và dùng hash chống trùng khi retry.

## 5. Containerized environment

Có Dockerfile cho từng service và [docker-compose.yml](docker-compose.yml) để chạy:

- Inventory Service.
- CDM Service.
- Celery Worker.
- Celery Beat.
- Hai container PostgreSQL 16: `inventory-db` và `cdm-db`.
- Redis 7: `redis`, dùng cho cache và Celery.

Toàn bộ backend, PostgreSQL và Redis chạy trong Compose. Các service kết nối nội bộ qua `inventory-db:5432`, `cdm-db:5432` và `redis:6379`; không cần cài PostgreSQL hoặc Redis riêng trên máy host.

PostgreSQL được publish ra máy host ở cổng `5432` (Inventory), `5433` (CDM); Redis ở cổng `6379`. Database và Redis dùng volume lưu dữ liệu; CDM API và worker dùng chung volume file upload.

Inventory/CDM tự chạy migration trước khi khởi động API. Compose dùng healthcheck để chờ database, Redis và API sẵn sàng trước khi chạy các service phụ thuộc. Khởi chạy toàn bộ bằng `docker compose up -d --build` sau khi tạo `.env` theo [hướng dẫn](docs/run-prototype.md).

## 6. Tính năng đã hoàn thành và chưa hoàn thành

### Đã hoàn thành trong phạm vi prototype

- Inventory API: tạo danh sách sản phẩm, lấy danh sách có bộ lọc và phân trang, truy vấn theo thời gian cập nhật.
- Upload Excel: nhận và lưu file, xếp hàng Celery task, đọc/validate dữ liệu và import vào CDM ở nền.
- Polling theo lịch: Celery Beat gửi task mỗi phút, Worker lấy dữ liệu Inventory được cập nhật trong một giờ gần nhất, tính đến thời điểm chạy, và lưu vào CDM.
- Chống trùng theo nội dung bằng SHA-256, `get_or_create` và unique constraint.
- Retry các lỗi kết nối được cấu hình tối đa 3 lần, chờ 60 giây; lưu batch trong transaction và ghi log lỗi.
- Đóng gói backend, PostgreSQL, Redis, Worker và Beat bằng Docker Compose; API tự chạy migration khi khởi động.
- Có dữ liệu mẫu, hướng dẫn chạy source và hướng dẫn chạy thử API.

### Chưa hoàn thành

- API polling thủ công còn cần hoàn thiện khoảng thời gian truy vấn và xử lý lỗi.
- Chưa kiểm thử với tải tăng đột biến (spike) và xử lý dữ liệu đồng thời; chưa xác nhận bảo đảm exactly-once dưới tải concurrent.
- Chưa triển khai máy chủ chạy CDC (Change Data Capture); polling hiện tại là gọi API theo thời gian cập nhật.
- Chưa hoàn thành frontend; prototype hiện được thao tác qua API.
- Chưa triển khai webhook và trường ghi nhận nguồn `received_via` trong model.

## 7. Source code và nguồn thực hiện

Source code: [GitHub — ksynerx-project](https://github.com/longthk17/ksynerx-project).

| Phần thực hiện | Tự viết / AI hỗ trợ |
| --- | --- |
| Backend Inventory/CDM | Ứng viên tự viết: API, model, xử lý Excel, polling, chống trùng và Celery task |
| Dữ liệu mockup / dữ liệu mẫu | Có AI hỗ trợ tạo dữ liệu phục vụ chạy thử |
| Frontend | Có AI hỗ trợ xây dựng bản nháp; chưa hoàn thành |
| Docker Compose | Có AI hỗ trợ viết và chỉnh cấu hình chạy các service |
| README và tài liệu hướng dẫn | Có AI hỗ trợ soạn và chỉnh sửa nội dung |
