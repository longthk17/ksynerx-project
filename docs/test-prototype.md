# Hướng dẫn chạy thử prototype

[← Quay lại trang chính](../README.md)

Khởi chạy source theo [hướng dẫn](run-prototype.md) trước khi thực hiện các lệnh dưới đây tại thư mục gốc dự án bằng PowerShell.

## Kiểm tra nhanh

Gọi API lấy danh sách sản phẩm:

```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/product?PageIndex=0&PageSize=10'
```

### Lấy danh sách sản phẩm bằng curl

API **GET** `/api/v1/product` hỗ trợ phân trang và lọc. Lệnh dùng Bash/Git Bash hoặc import vào Postman:

```bash
curl --location 'http://127.0.0.1:8000/api/v1/product?PageSize=10&PageIndex=0&Keyword=&PartnerSKUs=&SKUs='
```

- `PageSize`: số sản phẩm mỗi trang, từ 1 đến 100, mặc định 10.
- `PageIndex`: chỉ số trang bắt đầu từ 0; bỏ tham số thì mặc định 0, gửi giá trị rỗng sẽ lỗi validation.
- `Keyword`: tìm theo SKU hoặc tên sản phẩm.
- `PartnerSKUs`, `SKUs`: lọc danh sách mã, phân cách bằng dấu phẩy; để trống thì không lọc.

Response gồm `results` và thông tin phân trang: `pageIndex`, `pageSize`, `totalCount`, `totalPages`, `hasNextPage`, `hasPreviousPage`.

Tạo dữ liệu mẫu từ file JSON một lần trên database mới (PowerShell):

```powershell
curl.exe -X POST "http://localhost:8000/api/v1/product" -H "Content-Type: application/json" --data-binary "@backend/inventory-service/product_data_example.json"
```

### Tạo 3 sản phẩm bằng curl

API **POST** `/api/v1/product` nhận payload mảng sản phẩm và lưu vào database `inventory`. Mẫu dưới đây dùng Bash/Git Bash hoặc import vào Postman. Chạy trên database chưa có các SKU này để tránh lỗi trùng SKU.

```bash
curl --location 'http://127.0.0.1:8000/api/v1/product' \
--header 'Content-Type: application/json' \
--data '[
    {
        "sku": "DEMO_PHONE_101",
        "partnerSKU": "PARTNER_PHONE_101",
        "productName": "Điện thoại Nova X1",
        "unitCode": "CAI",
        "unitName": "Cái",
        "serialType": 1,
        "isExpiryDate": false,
        "categories": [
            {
                "categoryCode": "PHONE",
                "categoryName": "Điện thoại"
            }
        ],
        "productUnits": [
            {
                "unitCode": "CAI",
                "unitName": "Cái",
                "baseUnitQty": 1,
                "costPrice": 4200000,
                "sellingPrice": 5100000,
                "isBaseUnit": true
            },
            {
                "unitCode": "HOP",
                "unitName": "Hộp",
                "baseUnitQty": 5,
                "costPrice": 21000000,
                "sellingPrice": 25500000,
                "isBaseUnit": false
            }
        ]
    },
    {
        "sku": "DEMO_LAPTOP_102",
        "partnerSKU": "PARTNER_LAPTOP_102",
        "productName": "Laptop Orion 14",
        "unitCode": "CAI",
        "unitName": "Cái",
        "serialType": 1,
        "isExpiryDate": false,
        "categories": [
            {
                "categoryCode": "COMPUTER",
                "categoryName": "Máy tính"
            }
        ],
        "productUnits": [
            {
                "unitCode": "CAI",
                "unitName": "Cái",
                "baseUnitQty": 1,
                "costPrice": 12500000,
                "sellingPrice": 14900000,
                "isBaseUnit": true
            }
        ]
    },
    {
        "sku": "DEMO_MOUSE_103",
        "partnerSKU": "PARTNER_MOUSE_103",
        "productName": "Chuột không dây Aero",
        "unitCode": "CAI",
        "unitName": "Cái",
        "serialType": 1,
        "isExpiryDate": false,
        "categories": [
            {
                "categoryCode": "ACCESSORY",
                "categoryName": "Phụ kiện"
            }
        ],
        "productUnits": [
            {
                "unitCode": "CAI",
                "unitName": "Cái",
                "baseUnitQty": 1,
                "costPrice": 180000,
                "sellingPrice": 290000,
                "isBaseUnit": true
            },
            {
                "unitCode": "HOP",
                "unitName": "Hộp",
                "baseUnitQty": 10,
                "costPrice": 1800000,
                "sellingPrice": 2900000,
                "isBaseUnit": false
            }
        ]
    }
]'
```

Mẫu curl và file JSON ở trên có các SKU trùng nhau; chọn một cách tạo dữ liệu cho lần chạy thử.

## Upload Excel vào CDM

API: **POST** `http://localhost:8001/api/v1/upload-excel`. Gửi multipart/form-data với field `file`, sử dụng file mẫu [products_sample_10.xlsx](../products_sample_10.xlsx):

```powershell
curl.exe -X POST "http://localhost:8001/api/v1/upload-excel" -F "file=@products_sample_10.xlsx"
```

Nếu file nằm trong thư mục Downloads trên Windows, dùng đường dẫn sau với Bash/Git Bash hoặc import vào Postman:

```bash
curl --location 'http://127.0.0.1:8001/api/v1/upload-excel' \
--form 'file=@"C:/Users/kimlo/Downloads/products_sample_10.xlsx"'
```

Thay đường dẫn theo vị trí file trên máy. `--form` tự tạo header `Content-Type: multipart/form-data` và boundary; không cần đặt header này thủ công.

Luồng xử lý:

1. API nhận file `.xlsx`, lưu vào `media/excel_uploads/` trên volume dùng chung giữa CDM API và Worker.
2. Gọi `process_excel_file.delay(file_name)` để đưa Celery task vào hàng đợi Redis.
3. API trả HTTP **202** cùng `taskId` và `fileName`; việc import tiếp tục chạy nền.
4. Celery Worker đọc file bằng OpenPyXL, ghép ba sheet `products`, `categories`, `product_units` theo SKU và validate dữ liệu.
5. Task tính hash chống trùng và lưu dữ liệu vào database `cdm` trong container `cdm-db` bằng transaction. Nội dung đã có thì bỏ qua.

HTTP 202 xác nhận task đã được xếp hàng; xem log Worker để kiểm tra kết quả import. Code tiếp nhận file nằm ở [ExcelUploadView](../backend/cdm-service/my_app/views/views.py), task xử lý ở [process_excel_file](../backend/cdm-service/my_app/tasks.py).

## Polling từ Inventory vào CDM

Lịch được cấu hình tại **`CELERY_BEAT_SCHEDULE`** trong [backend/cdm-service/my_project/settings.py](../backend/cdm-service/my_project/settings.py):

```python
CELERY_BEAT_SCHEDULE = {
    "poll-products-hourly": {
        "task": "my_app.tasks.poll_products",
        "schedule": crontab(minute="*"),
    },
}
```

Hiện tại **mỗi phút chạy một lần** theo `crontab(minute="*")`. Celery Beat đưa task `poll_products` vào Redis; Celery Worker gọi Inventory API `/api/v1/product-query-all` với `updatedFrom` và `updatedTo`, validate dữ liệu trả về rồi insert vào `cdm-db`, bỏ qua nội dung trùng hash.

Mỗi lần chạy, polling lấy dữ liệu **được cập nhật trong một giờ gần nhất, tính đến thời điểm chạy**. Thời gian bắt đầu (`from`) là thời điểm hiện tại lùi một giờ; thời gian kết thúc (`to`) là thời điểm hiện tại. Ví dụ chạy lúc **10:35** thì lấy dữ liệu từ **09:35 đến trước 10:35** cùng ngày, không làm tròn về đầu giờ. Trong [poll_products](../backend/cdm-service/my_app/tasks.py), hai mốc này được tính bằng `get_relative_datetime(shift_hours=-1)` và `get_relative_datetime()`.

### Chạy polling thủ công

Gọi API **GET** `/api/v1/product-polling-check` bằng Bash/Git Bash hoặc import vào Postman:

```bash
curl --location 'http://127.0.0.1:8001/api/v1/product-polling-check'
```

API gọi Inventory và insert CDM trực tiếp trong request, không tạo lịch Celery. Response trả danh sách bản ghi mới được insert; nội dung đã có cùng hash được bỏ qua.

Endpoint này hiện có khoảng thời gian riêng trong [ProductPollingCheckView](../backend/cdm-service/my_app/views/views.py), với `to` đặt cố định ngày 5 của tháng; cần hoàn thiện trước khi dùng để kiểm tra dữ liệu cập nhật trong một giờ gần nhất.

## Theo dõi kết quả

Xem log Worker cho upload Excel và polling:

```powershell
docker compose logs -f cdm-worker
```

Nhấn `Ctrl+C` để thoát theo dõi log. Có thể kiểm tra số bản ghi đã lưu trong CDM:

```powershell
docker compose exec cdm-service python manage.py shell -c "from my_app.models.change_data import ChangeData; print(ChangeData.objects.count())"
```
