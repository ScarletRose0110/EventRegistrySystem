# Hệ thống Quản lý & Đăng ký Sự kiện Nội bộ XYZ

Web app Flask + MySQL 8 (Docker). Phạm vi và kế hoạch: xem KE_HOACH_XAY_DUNG_WEB.md.

## Cài đặt (lần đầu)

1. Khởi động MySQL:
   docker compose up -d
2. Tạo môi trường ảo và cài thư viện:
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
3. Migration:
   .venv\Scripts\python -m flask --app run.py db upgrade
   (lần đầu tiên sau khi clone: flask db stamp head nếu migration đã có, hoặc flask db migrate -m "init" rồi upgrade)
4. Seed dữ liệu mẫu:
   .venv\Scripts\python seed.py
5. Chạy app:
   .venv\Scripts\python run.py
   → http://127.0.0.1:5000/login

## Tài khoản demo
| Email | Mật khẩu | Role |
|---|---|---|
| a@xyz.com | 123456 | Employee + Organizer |
| b@xyz.com | 123456 | Employee |
| c@xyz.com | 123456 | Organizer + Admin |

## Kiểm thử
pytest tests/ (sẽ bổ sung theo Câu 9) — smoke test nhanh: .venv\Scripts\python smoke_test.py (app phải đang chạy)
