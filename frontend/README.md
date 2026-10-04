# KSynerX Frontend

Mã bản nháp ReactJS + Vite cho Inventory Service và CDM Service. **Frontend chưa hoàn thành**, chưa xác nhận toàn bộ các luồng với backend và chưa thuộc phạm vi demo prototype hiện tại.

## Chạy local

Yêu cầu Node.js 20.19+ hoặc 22.12+. Khởi chạy backend Inventory trên cổng 8000 và CDM trên cổng 8001 (cùng database, Redis và Celery worker theo cấu hình backend).

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Mở http://localhost:5173. Trên hệ điều hành khác có thể dùng `npm` thay cho `npm.cmd`.

Vite proxy `/inventory-api/*` tới `http://127.0.0.1:8000/api/v1/*` và `/cdm-api/*` tới `http://127.0.0.1:8001/api/v1/*`. Khi đổi cổng, sao chép `.env.example` thành `.env`, chỉnh `INVENTORY_TARGET` / `CDM_TARGET`, rồi khởi động lại Vite.

## Chức năng

- Danh sách sản phẩm, lọc Keyword/SKUs/PartnerSKUs và phân trang PageIndex bắt đầu từ 0.
- Tạo sản phẩm với payload mảng theo API; xem chi tiết danh mục và đơn vị quy đổi.
- Tra cứu sản phẩm trong khoảng cập nhật `[updatedFrom, updatedTo)`. Thời gian nhập theo múi giờ trình duyệt, gửi dạng ISO UTC.
- Tải file `.xlsx`, hiển thị taskId/fileName khi backend nhận và xếp hàng. Backend chưa có endpoint tra cứu trạng thái tác vụ.
- Kiểm tra đồng bộ (thao tác có ghi dữ liệu CDM) và hiển thị bản ghi mới.
- Kiểm tra sức khỏe từng service độc lập.

Excel cần các sheet `products`, `categories`, `product_units`, liên kết bằng cột `sku`. Cột products dùng tên API: `sku`, `partnerSKU`, `productName`, `unitCode`, `unitName`, `serialType`, `isExpiryDate`; categories: `sku`, `categoryCode`, `categoryName`; product_units: `sku`, `unitCode`, `unitName`, `baseUnitQty`, `isBaseUnit`.

## Build và kiểm tra

```powershell
npm.cmd test
npm.cmd run build
npm.cmd run preview
```

Build nằm tại `dist/`. Khi triển khai static build, cấu hình reverse proxy cùng origin cho `/inventory-api` và `/cdm-api` tương tự Vite; cấu hình proxy Vite không được đóng gói vào `dist`.
