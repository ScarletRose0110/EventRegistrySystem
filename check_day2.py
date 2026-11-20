# -*- coding: utf-8 -*-
"""Day 2: CRUD sự kiện (US-03/04A/04B) + tìm kiếm/lọc/phân trang (US-07)."""
import http.cookiejar
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://127.0.0.1:5000'
results = []


def check(name, ok, detail=''):
    results.append(ok)
    print(('PASS' if ok else 'FAIL') + ' | ' + name + (' | ' + detail if detail else ''))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(path, jar, data=None):
    opener = urllib.request.build_opener(NoRedirect, urllib.request.HTTPCookieProcessor(jar))
    if data is None:
        req = urllib.request.Request(BASE + path)
    else:
        req = urllib.request.Request(BASE + path, data=urllib.parse.urlencode(data).encode())
    try:
        r = opener.open(req)
        return r.getcode(), r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')


def get_csrf(path, jar):
    _, body = request(path, jar)
    m = re.search(r'name="csrf-token" content="([^"]+)"', body) or re.search(r'name="csrf_token"[^>]*value="([^"]+)"', body)
    return m.group(1) if m else '', body


def login(jar, email, password):
    token, _ = get_csrf('/login', jar)
    return request('/login', jar, {'csrf_token': token, 'email': email, 'password': password})


def post_form(path, jar, fields):
    token, _ = get_csrf(path, jar)
    fields = dict(fields)
    fields['csrf_token'] = token
    return request(path, jar, fields)


# Kiểm tra DB trực tiếp
from app import create_app
from app.extensions import db
from app.models import Event, Notification

app = create_app()


def db_check(fn):
    with app.app_context():
        return fn()


def event_fields(eid, **over):
    def f():
        e = db.session.get(Event, eid)
        base = {
            'name': e.name,
            'description': e.description,
            'location': e.location,
            'start_time': e.start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': e.end_time.strftime('%Y-%m-%dT%H:%M'),
            'registration_deadline': e.registration_deadline.strftime('%Y-%m-%dT%H:%M'),
            'max_attendees': str(e.max_attendees),
            'target_audience': e.target_audience,
        }
        base.update(over)
        return base
    return db_check(f)


from datetime import datetime, timedelta
now = datetime.now()
FUT = {
    'name': 'Tech Talks mùa 2',
    'description': 'Chuỗi chia sẻ công nghệ nội bộ quý IV.',
    'location': 'Hội trường lớn tầng 1',
    'start_time': (now + timedelta(days=14)).strftime('%Y-%m-%dT%H:%M'),
    'end_time': (now + timedelta(days=14, hours=3)).strftime('%Y-%m-%dT%H:%M'),
    'registration_deadline': (now + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M'),
    'max_attendees': '30',
    'target_audience': 'Toàn công ty',
}

jarC = http.cookiejar.CookieJar()
login(jarC, 'c@xyz.com', '123456')

print('--- US-03: TẠO SỰ KIỆN (c = Organizer+Admin) ---')
code, body = request('/manage/events', jarC)
check('GET /manage/events → 200 + nút tạo mới', code == 200 and 'Tạo sự kiện mới' in body)
code, body = request('/manage/events/new', jarC)
check('GET /manage/events/new → 200 + form', code == 200 and 'Tạo sự kiện' in body)

bad1 = dict(FUT); bad1['registration_deadline'] = (now + timedelta(days=15)).strftime('%Y-%m-%dT%H:%M')
code, body = post_form('/manage/events/new', jarC, bad1)
check('Tạo với hạn ĐK sau thời gian diễn ra → báo lỗi đúng AC4', code == 200 and 'Thời hạn đăng ký phải trước hoặc bằng thời gian diễn ra' in body)

bad2 = dict(FUT); bad2['name'] = ''
code, body = post_form('/manage/events/new', jarC, bad2)
check('Tạo thiếu tên → "Vui lòng nhập tên sự kiện"', code == 200 and 'Vui lòng nhập tên sự kiện' in body)

bad3 = dict(FUT); bad3['start_time'] = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'); bad3['registration_deadline'] = (now - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
code, body = post_form('/manage/events/new', jarC, bad3)
check('Tạo với thời gian trong quá khứ → báo lỗi', code == 200 and 'Thời gian diễn ra phải sau thời điểm hiện tại' in body)

code, _ = post_form('/manage/events/new', jarC, FUT)
check('Tạo hợp lệ → 302', code == 302)
created = db_check(lambda: Event.query.filter_by(name='Tech Talks mùa 2').first())
check('Sự kiện mới đã lưu + người tổ chức = c', created is not None and created.organizer_id == db_check(lambda: [u.id for u in __import__('app.models', fromlist=['User']).User.query.filter_by(email='c@xyz.com')][0]))
n_notify = db_check(lambda: Notification.query.filter(Notification.content.like('%Sự kiện mới%')).count())
check('BR30: thông báo sự kiện mới cho cả 3 nhân viên', n_notify == 3, 'count=' + str(n_notify))
eid_new = created.id if created else 0

print('--- PHÂN QUYỀN (US-06/BR06/BR15) ---')
jarB = http.cookiejar.CookieJar()
login(jarB, 'b@xyz.com', '123456')
code, _ = request('/manage/events', jarB)
check('b (Employee) GET /manage/events → 403', code == 403)
token, _ = get_csrf('/events', jarB)
code, body = request('/manage/events/new', jarB, dict(FUT, csrf_token=token))
check('b POST tạo sự kiện → 403 "Bạn không có quyền tạo sự kiện"', code == 403 and 'Bạn không có quyền tạo sự kiện' in body)
code, body = request('/manage/events/1/edit', jarB)
check('b sửa sự kiện của người khác → 403', code == 403 and 'Bạn không có quyền chỉnh sửa sự kiện này' in body)
token, _ = get_csrf('/events', jarB)
code, body = request('/manage/events/1/cancel', jarB, {'csrf_token': token})
check('b hủy sự kiện của người khác → 403', code == 403 and 'Bạn không có quyền hủy sự kiện này' in body)

print('--- US-04A: SỬA (a = Organizer phòng IT) ---')
jarA = http.cookiejar.CookieJar()
login(jarA, 'a@xyz.com', '123456')
code, body = request('/manage/events', jarA)
check('a xem danh sách quản lý → 200', code == 200)
code, body = request('/manage/events/1/edit', jarA)
check('a sửa sự kiện phòng IT (BR15 theo phòng ban) → 200', code == 200)
fields = event_fields(1, location='Phòng hội thảo tầng 5')
code, _ = post_form('/manage/events/1/edit', jarA, fields)
check('Sửa hợp lệ → 302', code == 302)
loc = db_check(lambda: db.session.get(Event, 1).location)
check('Dữ liệu đã cập nhật trong CSDL', loc == 'Phòng hội thảo tầng 5', 'loc=' + str(loc))

fields = event_fields(2, max_attendees='1')
code, body = post_form('/manage/events/2/edit', jarA, fields)
check('Sửa max < số đã đăng ký → báo lỗi đúng AC3', code == 200 and 'Số lượng tối đa không được nhỏ hơn số người đã đăng ký' in body)

code, _ = request('/manage/events/4/edit', jarA)
check('a sửa sự kiện đang diễn ra → bị chặn (302)', code == 302)
code, body = request('/manage/events', jarA)
check('Thông báo "Không thể chỉnh sửa sự kiện đã bắt đầu hoặc đã hủy"', 'Không thể chỉnh sửa sự kiện đã bắt đầu hoặc đã hủy' in body)

code, body = request('/manage/events/4/edit', jarC)
check('Admin ngoại lệ BR28: sửa được sự kiện đang diễn ra → 200', code == 200)
fields = event_fields(4, location='Sân vận động XYZ')
code, _ = post_form('/manage/events/4/edit', jarC, fields)
check('Admin sửa sự kiện đang diễn ra → 302', code == 302)
check('CSDL đã đổi địa điểm', db_check(lambda: db.session.get(Event, 4).location) == 'Sân vận động XYZ')

print('--- US-04B: HỦY ---')
token, _ = get_csrf('/manage/events', jarC)
code, _ = request('/manage/events/5/cancel', jarC, {'csrf_token': token})
check('Hủy sự kiện đã kết thúc → bị chặn (302 + giữ nguyên)', code == 302)
check('Sự kiện 5 vẫn chưa hủy trong CSDL', db_check(lambda: db.session.get(Event, 5).is_cancelled) is False)
token, _ = get_csrf('/manage/events', jarC)
code, _ = request('/manage/events/1/cancel', jarC, {'csrf_token': token})
check('Hủy sự kiện đang mở → 302', code == 302)
check('Sự kiện 1 đã chuyển Cancelled', db_check(lambda: db.session.get(Event, 1).is_cancelled) is True)
code, body = request('/manage/events', jarC)
check('Flash "Hủy sự kiện thành công"', 'Hủy sự kiện thành công' in body)
n_cancel = db_check(lambda: Notification.query.filter(Notification.content.like('%đã bị hủy%')).count())
check('US-04B-AC3: thông báo hủy cho người đã đăng ký', n_cancel >= 1, 'count=' + str(n_cancel))

print('--- US-07: TÌM KIẾM / LỌC / PHÂN TRANG ---')
code, body = request('/events?q=hoi+thao', jarA)
check('Tìm "hoi thao" không dấu → ra "Hội thảo"', code == 200 and 'Hội thảo' in body)
code, body = request('/events?q=THAO', jarA)
check('Tìm "THAO" (hoa, không dấu, khớp một phần) → ra "Hội thảo"', code == 200 and 'Hội thảo' in body)
code, body = request('/events?q=hoi+thao', jarA)
check('Giữ nguyên từ khóa trong ô tìm kiếm (US-07-AC8)', 'value="hoi thao"' in body)
code, body = request('/events?department=2', jarA)
check('Lọc phòng ban IT (id=2) → có "Hội thảo" (IT), không có "Workshop" (HR)', code == 200 and 'Hội thảo' in body and 'Workshop' not in body)
code, body = request('/events?status=' + urllib.parse.quote('Đã hủy'), jarA)
check('Lọc trạng thái "Đã hủy" → có sự kiện hủy, không có sự kiện mở', 'Dã ngoại' in body and 'Team building' not in body)
code, body = request('/events?from_date=2026-12-10&to_date=2026-12-01', jarA)
check('Khoảng ngày đảo → báo lỗi AC5', code == 200 and 'Ngày bắt đầu không được sau ngày kết thúc' in body)
code, body = request('/events?q=xyz-khong-co', jarA)
check('Không có kết quả → "Không tìm thấy sự kiện phù hợp"', 'Không tìm thấy sự kiện phù hợp' in body)
code, body = request('/events', jarA)
check('Mặc định: ẩn sự kiện đã hủy (US-07-AC2)', 'Hội thảo' not in body and 'Dã ngoại' not in body)

failed = len(results) - sum(results)
print('')
print('TỔNG: ' + str(sum(results)) + ' PASS / ' + str(failed) + ' FAIL')
sys.exit(1 if failed else 0)
