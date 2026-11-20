# KẾ HOẠCH XÂY DỰNG WEB — HỆ THỐNG QUẢN LÝ & ĐĂNG KÝ SỰ KIỆN NỘI BỘ XYZ

> Tổng hợp từ: User_Stories_MVP_Event_Registration_v9.xlsx, Engineering Progress Plan Template1.xlsx (Gantt),
> Ngan_Sach_Chi_Phi_EVM_XYZ_v8.xlsx (phân công A/B/C), ActivityDiagram.drawio, Actors & UseCases, RACI.
> Môi trường đã sẵn sàng: Docker Desktop 4.98.0 (Engine 29.9.2, Compose v5.6.1, backend WSL2), MySQL 8.0 sẽ chạy trong container.

---

## 1. MỤC TIÊU & PHẠM VI

Xây website hoàn chỉnh 6 màn hình Figma (Login, Event List, Event Detail, Register Event, My Events, Event Management)
đúng AC của các User Story, chạy trên MySQL thật trong Docker, có phân quyền kiểm soát ở máy chủ.

| Mức | Nội dung | Story |
|---|---|---|
| **Bắt buộc (Câu 8)** | Đăng nhập, phân quyền; Quản lý sự kiện: tạo, danh sách, chi tiết, sửa, hủy | US-06, US-03, US-04A, US-04B, US-07, US-08 |
| **Nên có (Gantt Sprint 2–3)** | Đăng ký và hủy đăng ký, Sự kiện của tôi, danh sách người đăng ký, xác nhận, điểm danh | US-01, 02, 09, 10, 11, 05 |
| **Để sau** | Dashboard, quản lý tài khoản, phòng ban, can thiệp sự kiện, xuất Excel | US-12 → US-17 |

> Lưu ý: bảng `departments` và `user_roles` vẫn tạo ngay từ đầu (danh sách sự kiện cần "Phòng ban tổ chức",
> đăng nhập cần phân role) — đây là nền cho US-15/US-13 làm sau.

## 2. CÔNG NGHỆ (ĐÃ CHỐT)

| Lớp | Lựa chọn | Ghi chú |
|---|---|---|
| Ngôn ngữ, khung | Python 3.12 + Flask 3 | Nhóm 3 người, ~9 ngày |
| CSDL | MySQL 8.0 trong Docker Compose | CSDL thật, khớp file ngân sách |
| Truy cập dữ liệu | Flask-SQLAlchemy + Flask-Migrate | Transaction cho BR14; migration dùng chung |
| Đăng nhập, phân quyền | Flask-Login + decorator role | US-06: chưa đăng nhập → /login; sai role → 403 ở máy chủ |
| Form & validation | Flask-WTF (WTForms) + CSRF | Lỗi theo từng trường; thêm HTML5 phía trình duyệt |
| Giao diện | Jinja2 + Bootstrap 5 | Dựng nhanh 6 màn hình theo Figma |
| Kiểm thử | pytest trên CSDL test riêng | Test case Câu 9 chạy được |
| Môi trường chạy | Docker Desktop (đã cài 4.98.0, WSL2 OK) | MySQL chạy container; Flask chạy host trong giai đoạn dev |

## 3. CẤU TRÚC DỰ ÁN

```
DA_FINAL/
├── app/
│   ├── __init__.py            # app factory, đăng ký blueprint, login_manager, db, migrate
│   ├── config.py              # cấu hình theo biến môi trường (.env)
│   ├── models/                # 6 bảng: department, user, user_role, event, registration, notification
│   │   ├── __init__.py  department.py  user.py  user_role.py  event.py  registration.py  notification.py
│   ├── forms/                 # login_form, event_form, register_form, filter_form, attend_form...
│   ├── services/
│   │   ├── event_status.py    # HÀM DUY NHẤT tính trạng thái sự kiện (dùng cho list, detail, test)
│   │   ├── registration.py    # BR14: transaction + SELECT ... FOR UPDATE + 4 kiểm tra + is_active
│   │   └── notification.py    # BR30, US-04B-AC3, US-11-AC6: tạo bản ghi thông báo
│   ├── blueprints/
│   │   ├── auth.py            # /login, /logout (US-06)
│   │   ├── events.py          # /events, /events/<id> (US-07, 08)
│   │   ├── registrations.py   # /events/<id>/register, /cancel-registration (US-01, 02), /my-events (US-09)
│   │   └── manage.py          # /manage/events, /new, /<id>/edit, /<id>/cancel, /<id>/registrations (US-03,04A,04B,10,11,05)
│   ├── templates/             # base.html + 6 màn hình theo Figma
│   ├── static/                # css/js bootstrap + script validate phía client
│   └── utils/                 # tìm kiếm không dấu (bỏ dấu tiếng Việt), phân trang, decorator quyền
├── migrations/                # Flask-Migrate
├── tests/                     # pytest + factory fixture + CSDL test riêng
├── seed.py                    # 3 tài khoản, 4 phòng ban, sự kiện demo
├── docker-compose.yml         # mysql:8.0 (volume, healthcheck, port 3306)
├── .env.example  .gitignore  requirements.txt  README.md
```

## 4. MÔ HÌNH DỮ LIỆU (6 BẢNG)

| Bảng | Cột chính | Ràng buộc |
|---|---|---|
| departments | id, name, is_active | name UNIQUE (không phân biệt hoa thường), mặc định hoạt động |
| users | id, email, password_hash, full_name, department_id FK, is_locked | email UNIQUE (BR16); mật khẩu băm (werkzeug), không lưu rõ |
| user_roles | user_id FK, role ENUM(Employee, Organizer, Admin) | PK (user_id, role); nhiều role 1 tài khoản (BR18) |
| events | name, description, start_time, end_time, location, max_attendees, registration_deadline, target_audience, organizer_id FK, department_id FK, is_cancelled, created_at | CHECK max_attendees >= 1; CHECK registration_deadline <= start_time AND start_time < end_time; target_audience mặc định 'Toàn công ty' (BR08) |
| registrations | event_id, user_id, status ENUM(Registered, Confirmed, Rejected, Cancelled, Attended), rejection_reason, is_active, created_at, updated_at | BR01/BR23 |
| notifications | recipient_id FK, event_id FK, content, email_sent, created_at | BR30, US-04B-AC3, US-11-AC6 |

### Hai điểm kỹ thuật bắt buộc

**BR01 — không đăng ký trùng, vẫn cho đăng ký lại:**
Nhân viên đã Cancelled/Rejected được đăng ký lại → KHÔNG đặt UNIQUE(event_id, user_id) đơn giản.
Dùng cột sinh `is_active`: có giá trị khi trạng thái là Registered/Confirmed/Attended, bằng NULL khi Cancelled/Rejected
(MySQL cho phép nhiều NULL trong UNIQUE). Đặt:
`UNIQUE(event_id, user_id, is_active)` + CHECK (is_active = 1 khi status IN (...) else NULL).

**BR14 — không vượt số lượng (transaction):**
```python
def register(event_id, user_id):
    with db.session.begin():
        event = db.session.query(Event).filter(Event.id == event_id).with_for_update().one()
        # 4 kiểm tra theo thứ tự ưu tiên AC7: AC6 (hủy/đã bắt đầu), AC1 (trùng), AC2 (đủ chỗ), AC3 (quá hạn)
        active_count = đếm đăng ký còn hiệu lực của event (status in Registered/Confirmed/Attended)
        if active_count >= event.max_attendees: raise BusinessError("Sự kiện đã đủ số lượng đăng ký")
        db.session.add(Registration(event_id, user_id, status="Registered", is_active=1))
```
`SELECT ... FOR UPDATE` khóa dòng sự kiện → 2 người đăng ký đồng thời chỗ cuối: chỉ 1 người thành công (US-01-AC8).

## 5. TRẠNG THÁI SỰ KIỆN — HÀM TÍNH ĐỘNG (VIẾT 1 LẦN)

Không lưu trạng thái vào DB. `services/event_status.py` tính từ: thời điểm hiện tại, số đăng ký còn hiệu lực, cờ hủy.
Cùng hàm dùng cho: danh sách (US-07), chi tiết (US-08), My Events (US-09) và test.

| Trạng thái | Điều kiện (thứ tự kiểm tra) | Hệ quả |
|---|---|---|
| Cancelled | is_cancelled | Không nhận đăng ký, không điểm danh (BR07) |
| Đang mở đăng ký | chưa hủy; chưa bắt đầu; còn trước hạn; số ĐK < tối đa | Cho đăng ký (US-01) và hủy ĐK (US-02); Organizer sửa/hủy được |
| Đã đủ số lượng | chưa hủy; chưa bắt đầu; số ĐK >= tối đa | Không nhận ĐK mới; về "Đang mở" khi có người hủy/bị từ chối |
| Hết hạn đăng ký | chưa hủy; chưa bắt đầu; đã quá hạn ĐK (và chưa đủ chỗ) | Không nhận ĐK; không hủy ĐK (BR09) |
| Đang diễn ra | chưa hủy; start <= now <= end + 30 phút bù giờ | Điểm danh được (BR13); Organizer không sửa (Admin ngoại lệ BR28) |
| Đã kết thúc / Quá hạn điểm danh | chưa hủy; now > end + 30 phút | Đóng điểm danh; bảo lưu lịch sử (BR05) |

Vòng đời đăng ký (BR23): Registered → Confirmed/Rejected (Organizer) | Cancelled (nhân viên/khóa TK) | Attended (điểm danh).
Rejected/Cancelled/Attended là trạng thái cuối; số "đã đăng ký" chỉ đếm Registered/Confirmed/Attended.

## 6. PHÂN QUYỀN (KIỂM TRA Ở MÁY CHỦ — KỂ CẢ TRUY CẬP THẲNG URL)

- Decorator `roles_required('Organizer','Admin')` và hàm `can_manage(current_user, event)`:
  Organizer chỉ sửa/hủy/điểm danh/xem danh sách ĐK của sự kiện **mình tạo hoặc của phòng ban mình** (BR15);
  Admin toàn quyền (BR28: được sửa/xử lý ĐK cả khi đã bắt đầu, riêng điểm danh vẫn theo BR13).
- Mọi route kiểm tra quyền trong view (không chỉ ẩn nút ở giao diện). Vi phạm → 403 "Bạn không có quyền …".
- Chưa đăng nhập → chuyển về /login (US-06-AC5); tài khoản khóa → từ chối + chấm dứt phiên (BR17).
- Menu gộp quyền của tất cả role được gán (US-06-AC1, BR18).

## 7. VALIDATION (CẢ 2 PHÍA: HTML5/JS + MÁY CHỦ; MÁY CHỦ QUYẾT ĐỊNH)

| Trường | Quy tắc | Thông báo |
|---|---|---|
| Tên sự kiện | Bắt buộc; ≤ 200 ký tự (tự chọn) | Vui lòng nhập tên sự kiện |
| Mô tả | Bắt buộc; ≤ 2000 ký tự (tự chọn) | Vui lòng nhập mô tả |
| Địa điểm | Bắt buộc; ≤ 255 ký tự | Vui lòng nhập địa điểm |
| Thời gian diễn ra | Sau hiện tại (khi tạo); khi sửa chỉ kiểm tra lại trường đổi (BR11) | Theo AC4 |
| Thời gian kết thúc | Sau thời gian diễn ra | Theo AC4 |
| Thời hạn đăng ký | Sau hiện tại; không sau thời gian diễn ra | Thời hạn đăng ký phải trước hoặc bằng thời gian diễn ra |
| Số lượng tối đa | Số nguyên ≥ 1; khi sửa ≥ số ĐK còn hiệu lực | Số lượng tối đa không được nhỏ hơn số người đã đăng ký |
| Đối tượng tham gia | Mặc định "Toàn công ty" | — |
| Email (login) | Bắt buộc, đúng định dạng | Vui lòng nhập email / Email không đúng định dạng |
| Mật khẩu (login) | Bắt buộc; báo lỗi chung nếu sai | Vui lòng nhập mật khẩu / Email hoặc mật khẩu không đúng |

Thông báo lỗi đăng ký theo thứ tự ưu tiên (US-01-AC7): AC6 "Sự kiện hiện không mở đăng ký" → AC1 "Bạn đã đăng ký sự kiện này" →
AC2 "Sự kiện đã đủ số lượng đăng ký" → AC3 "Đã hết hạn đăng ký sự kiện". Hủy: "Đã quá thời hạn hủy đăng ký" / "Đăng ký này không thể hủy".

## 8. MÀN HÌNH & ĐƯỜNG DẪN (KHỚP 6 MÀN FIGMA)

| Đường dẫn | Chức năng | Story | Quyền |
|---|---|---|---|
| GET/POST /login, GET /logout | Đăng nhập/đăng xuất (Login) | US-06 | mọi người |
| GET /events | Danh sách: tìm không dấu, lọc (thời gian, phòng ban, trạng thái), phân trang (Event List) | US-07 | Employee+ |
| GET /events/<id> | Chi tiết + nút Đăng ký/Hủy theo trạng thái (Event Detail) | US-08 | Employee+ |
| POST /events/<id>/register | Đăng ký (BR14 transaction) | US-01 | Employee+ |
| POST /cancel-registration | Hủy đăng ký | US-02 | Employee+ |
| GET /my-events | Sự kiện đã đăng ký + trạng thái ĐK (My Events) | US-09 | Employee+ |
| GET /manage/events | Quản lý sự kiện của Organizer (Event Management) | US-03.. | Organizer+ |
| GET/POST /manage/events/new | Tạo sự kiện (Register Event) | US-03 | Organizer/Admin |
| GET/POST /manage/events/<id>/edit | Sửa sự kiện | US-04A | BR15 |
| POST /manage/events/<id>/cancel | Hủy sự kiện (+ hộp thoại xác nhận, + thông báo) | US-04B | BR15 |
| GET /manage/events/<id>/registrations | Danh sách ĐK; xác nhận/không xác nhận (US-11); điểm danh (US-05) | US-10,11,05 | BR15 |

Tìm kiếm không dấu: hàm `remove_diacritics()` ở utils, áp dụng cho tên sự kiện và họ tên (US-07-AC3, US-10-AC2):
nhập "hoi thao" vẫn tìm ra "Hội thảo"; kết hợp được với các bộ lọc; giữ nguyên filter khi chuyển trang (US-07-AC8).

## 9. THÔNG BÁO (BR30, US-04B-AC3, US-11-AC6)

`services/notification.py`: tạo sự kiện → thông báo toàn bộ nhân viên đang hoạt động
("Sự kiện mới: [tên], [thời gian], [địa điểm]. Hạn đăng ký: [hạn]");
hủy sự kiện → thông báo người có ĐK còn hiệu lực ("Sự kiện [tên] ngày [thời gian] đã bị hủy");
xác nhận/không xác nhận → thông báo từng nhân viên (kèm lý do nếu có).
Bản ghi lưu bảng notifications; hiển thị trong app (chuông thông báo); cột email_sent dành cho bước gửi email thật (để sau).

## 10. KẾ HOẠCH THEO NGÀY 6/11 → 15/11 (khớp Gantt & phân công ngân sách)

| Ngày | Công việc | Story | Người |
|---|---|---|---|
| 6/11 | Docker Compose (MySQL), cấu trúc dự án, migration, seed (3 TK, 4 phòng ban, vài sự kiện), đăng nhập/đăng xuất, khung giao diện base | US-06 | C (CSDL, login); B (giao diện nền) |
| 7–8/11 | Tạo, sửa, hủy sự kiện + validation + phân quyền theo người tạo/phòng ban | US-03, 04A, 04B | C |
| 7–8/11 | Danh sách (tìm không dấu, lọc, phân trang) + chi tiết | US-07, 08 | B |
| 8–9/11 | Đăng ký, hủy đăng ký (transaction BR14, 4 kiểm tra, is_active/BR01) | US-01, 02 | A |
| 9–10/11 | My Events; thông báo khi tạo/hủy sự kiện | US-09, BR30, US-04B-AC3 | B, C |
| 10–12/11 | Danh sách người ĐK, xác nhận/không xác nhận, điểm danh | US-10, 11, 05 | C |
| 11–13/11 | Viết & chạy test case Câu 9, sửa lỗi | toàn bộ | B + cả nhóm |
| 14–15/11 | Dữ liệu demo, README, kịch bản trình diễn, nghiệm thu | toàn bộ | cả nhóm |

Nhân sự (theo file ngân sách): **A = Nguyễn Văn A** (Scrum Master/Fullstack/Docs — US-01/02 + tài liệu),
**B = Trần Văn B** (UI/QA — giao diện, US-07/08/09, test case), **C = Lê Văn C** (Backend — CSDL, US-06, CRUD sự kiện, US-10/11/05).

## 11. KẾ HOẠCH KIỂM THỬ (CÂU 9) — pytest TRÊN CSDL TEST RIÊNG

Fixture: tạo CSDL MySQL test riêng (`qldapm_test`), tạo/bỏ schema mỗi test, factory tạo user/event nhanh.

| Nhóm | Test chính |
|---|---|
| 1. Đăng nhập & phân quyền | Đúng sai trống email/pass; email sai định dạng; tài khoản khóa; đăng xuất hết phiên; truy cập thẳng URL theo từng role → 403; menu gộp role (BR18) |
| 2. Tạo/sửa/hủy sự kiện | Thiếu từng trường bắt buộc; thời gian sai (deadline > start, end <= start, quá khứ khi tạo); max = 0; sửa sự kiện đã bắt đầu/hủy bị chặn; max mới < số ĐK hiệu lực bị chặn; hủy cần xác nhận; không hủy được sự kiện đã kết thúc (BR05) |
| 3. Danh sách & chi tiết | "hoi thao" → "Hội thảo" (không dấu); lọc kết hợp nhiều điều kiện; khoảng ngày đảo → lỗi; phân trang giữ filter; chi tiết đủ 11 trường; sự kiện không tồn tại → thông báo |
| 4. Đăng ký & hủy | 4 kiểm tra + thứ tự ưu tiên AC7; đăng ký lại sau Cancelled/Rejected (BR01); hủy trước hạn OK, sau hạn từ chối; chỉ hủy Registered/Confirmed; **BR14: 2 luồng đăng ký chỗ cuối đồng thời → đúng 1 thành công, không vượt max** |
| 5. Quản lý ĐK & điểm danh | Xác nhận → Confirmed; không xác nhận kèm lý do → Rejected + giải phóng chỗ; chỉ xử lý Registered khi chưa bắt đầu (BR24); điểm danh trong khung giờ → Attended, ngoài khung/trước giờ → từ chối (BR13); quyền phòng ban (BR15) |
| 6. Biên & dữ liệu | Tên 200/201 ký tự; mô tả 2000/2001; địa điểm 255/256; deadline = start (hợp lệ); end = start (cấm); max=1; email trùng khi tạo tài khoản (BR16) |

Mỗi test ghi rõ: mã AC liên quan + thông báo kỳ vọng (để map ngược vào bảng AC khi báo cáo).

## 12. SEED & KỊCH BẢN DEMO

- 4 phòng ban: HR (Nhân sự), IT (Công nghệ), Công đoàn, Truyền thông.
- 3 tài khoản: a@xyz.com (Employee+Organizer — làm được cả đăng ký lẫn quản lý), b@xyz.com (Employee), c@xyz.com (Organizer+Admin — quản trị + quản lý sự kiện). Mật khẩu demo: 123456 (băm).
- Sự kiện demo phủ 6 trạng thái: đang mở, đã đủ chỗ, hết hạn ĐK, đang diễn ra, đã kết thúc, đã hủy.
- Kịch bản demo 15/11: login từng role → xem menu khác nhau → tạo sự kiện (nhận thông báo) → nhân viên tìm "hoi thao" → đăng ký → Organizer xác nhận/điểm danh → hủy sự kiện (nhận thông báo) → thử truy cập thẳng URL sai quyền → 403.

## 13. RỦI RO & ĐỊNH NGHĨA HOÀN THÀNH

Rủi ro chính (từ file EMV): chậm CRUD do môi trường CSDL (R-03) — đã giảm nhờ Docker+MySQL chuẩn hóa; lệch giao diện so với Figma (R-04) — review UI mỗi Sprint; thời gian hạn chế — bám thứ tự ưu tiên (bắt buộc → nên có → để sau).

DoD (theo Gantt): Pass 100% AC của phạm vi; Code reviewed; Unit test pass; UI khớp Figma; Validation đủ cả client lẫn server.

## 14. BƯỚC KHỞI ĐỘNG NGAY (DAY 1 — 6/11)

1. [x] Cài Docker + WSL2 (đã xong: Docker Desktop 4.98.0, Engine 29.9.2, Compose v5.6.1).
2. [ ] Tạo `docker-compose.yml` (mysql:8.0, volume, healthcheck) → `docker compose up -d`.
3. [ ] Tạo cấu trúc app/, requirements.txt, .env, app factory + config.
4. [ ] 6 models + migration đầu tiên; seed.py (3 TK, 4 phòng ban, sự kiện demo).
5. [ ] Login/logout + decorator role + base template Bootstrap 5 (khớp Figma Login).
6. [ ] Xác minh: đăng nhập 3 role, menu gộp, chặn URL thẳng.
