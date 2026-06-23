# Hướng Dẫn Chạy Dự Án

## Yêu Cầu

- Python 3.10 trở lên
- PostgreSQL

---

# 1. Thiết Lập Môi Trường (Setup)

### Bước 1: Tạo Project Django

Tạo cấu trúc project Django trong thư mục hiện tại.

```bash
django-admin startproject config .
```

---

### Bước 2: Tạo Django App

Tạo một app mới trong thư mục `apps`.

```bash
python manage.py startapp <app_name> apps/<app_name>
```

---

### Bước 3: Tạo Migration

Sinh file migration từ các model đã khai báo.

```bash
python manage.py makemigrations
```

---

### Bước 4: Đồng Bộ Database

Tạo hoặc cập nhật các bảng trong cơ sở dữ liệu.

```bash
python manage.py migrate
```

---

# 2. Thiết Lập Cơ Sở Dữ Liệu

### Bước 1: Đăng Nhập PostgreSQL

```bash
psql -U postgres
```

---

### Bước 2: Kiểm Tra Danh Sách Database

```sql
\l
```

---

### Bước 3: Tạo Database

```sql
CREATE DATABASE music;
```

---

### Bước 4: Thoát PostgreSQL

```sql
\q
```

---

# 3. Chạy Dự Án Bằng Virtual Environment (Khuyến Nghị)

### Bước 1: Tạo Virtual Environment

```bash
python -m venv .venv
```

### Bước 2: Kích Hoạt Virtual Environment

**Windows**

```bash
.venv\Scripts\activate
```

**macOS/Linux**

```bash
source .venv/bin/activate
```

### Bước 3: Cài Đặt Thư Viện

```bash
pip install -r requirements.txt
```

### Bước 4: Cấu Hình Biến Môi Trường

Tạo file `.env` từ file `.env.example` và cập nhật các giá trị cần thiết.

### Bước 5: Khởi Động Dự Án

```bash
python manage.py runserver
```

### Bước 6: Truy Cập Hệ Thống

**Trang Chủ**

```text
http://127.0.0.1:8000
```

**Swagger UI**

```text
http://127.0.0.1:8000/swagger/
```

**ReDoc**

```text
http://127.0.0.1:8000/redoc/
```

### Bước 7: Tắt Virtual Environment

```bash
deactivate
```

---

# 4. Chạy Dự Án Không Dùng Virtual Environment

### Bước 1: Cài Đặt Thư Viện

```bash
pip install -r requirements.txt
```

### Bước 2: Cấu Hình Biến Môi Trường

Tạo file `.env` từ file `.env.example` và cập nhật các giá trị cần thiết.

### Bước 3: Khởi Động Dự Án

```bash
python manage.py runserver
```

### Bước 4: Truy Cập Hệ Thống

**Trang Chủ**

```text
http://127.0.0.1:8000
```

**Swagger UI**

```text
http://127.0.0.1:8000/swagger/
```

**ReDoc**

```text
http://127.0.0.1:8000/redoc/
```
