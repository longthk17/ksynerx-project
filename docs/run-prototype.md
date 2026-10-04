# Hướng dẫn chạy prototype

[← Quay lại trang chính](../README.md)

Các lệnh dưới đây dùng PowerShell, chạy tại thư mục gốc `ksynerx-project`. Cần cài Git, Docker Desktop và bật Docker Desktop trước khi bắt đầu. Docker sẽ cài Python và dependencies trong image.

## Bước 1. Lấy source code

Lần đầu:

```powershell
git clone https://github.com/longthk17/ksynerx-project.git
cd ksynerx-project
```

Nếu đã có repository, vào thư mục dự án rồi cập nhật nhánh hiện tại:

```powershell
git status
git pull --ff-only
```

Nếu có thay đổi local, commit hoặc stash các thay đổi cần giữ trước khi pull.

## Bước 2. Tạo cấu hình môi trường

Chỉ chạy hai lệnh copy khi chưa có file `.env` tương ứng:

```powershell
Copy-Item backend/inventory-service/.env.example backend/inventory-service/.env
Copy-Item backend/cdm-service/.env.example backend/cdm-service/.env
```

Đặt `DB_PASSWORD=0000` trong hai file `.env` để khớp với `POSTGRES_PASSWORD: "0000"` trong Compose hiện tại. Nếu dùng mật khẩu khác, cập nhật đồng thời `.env` và `POSTGRES_PASSWORD` của database tương ứng.

Compose đã cấu hình host nội bộ cho ứng dụng. Database thực tế khi chạy Compose là `inventory` và `cdm`. Các cổng host `5432`, `5433`, `6379`, `8000`, `8001` cần còn trống.

Nếu database volume đã được khởi tạo, dùng mật khẩu hiện có của database; đổi `POSTGRES_PASSWORD` trong Compose không đổi mật khẩu trong volume cũ.

## Bước 3. Build và khởi chạy toàn bộ prototype

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Compose chạy hai container PostgreSQL (`inventory-db`, `cdm-db`), Redis, hai API, Celery Worker và Beat. Không cần cài PostgreSQL hoặc Redis riêng trên máy host.

Inventory/CDM tự chạy `migrate --noinput` trước khi khởi động API. Healthcheck và `depends_on` giúp các service chờ dependency sẵn sàng; Worker và Beat chạy sau khi CDM API sẵn sàng.

## Bước 4. Kiểm tra trạng thái và log

```powershell
docker compose ps
docker compose logs --tail=50 inventory-service cdm-service cdm-worker cdm-beat
```

- Inventory API: `http://localhost:8000/api/v1/product`.
- CDM upload API: `http://localhost:8001/api/v1/upload-excel`.
- Celery Worker xử lý tác vụ; Celery Beat gửi tác vụ polling mỗi phút.

## Cập nhật code và dừng ứng dụng

Sau khi cập nhật source:

```powershell
git pull --ff-only
docker compose stop inventory-service cdm-service cdm-worker cdm-beat
docker compose up -d --build
```

Nếu bản cập nhật bổ sung biến môi trường, cập nhật `.env` theo `.env.example` trước khi chạy lại. API tự chạy migration mới khi khởi động.

Dừng toàn bộ prototype, giữ dữ liệu trong volume:

```powershell
docker compose down
```

Hướng dẫn thao tác API và chạy thử: [Chạy thử prototype](test-prototype.md).
