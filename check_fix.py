# -*- coding: utf-8 -*-
import http.cookiejar, re, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta
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

from app import create_app
from app.extensions import db
from app.models import Event
app = create_app()

def db_check(fn):
    with app.app_context():
        return fn()

jar = http.cookiejar.CookieJar()
_, body = request('/login', jar)
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', body)
request('/login', jar, {'csrf_token': m.group(1), 'email': 'a@xyz.com', 'password': '123456'})

now = datetime.now()
sec = lambda t: t.strftime('%Y-%m-%dT%H:%M:%S')  # định dạng CÓ GIÂY như trình duyệt của bạn
token, _ = get_csrf('/manage/events/new', jar)
fields = {
    'csrf_token': token, 'name': 'Test giây cuối',
    'description': 'test', 'location': 'test',
    'start_time': sec(now + timedelta(days=3)),
    'end_time': sec(now + timedelta(days=3, hours=2)),
    'registration_deadline': sec(now + timedelta(hours=2)),
    'max_attendees': '10', 'target_audience': 'Toàn công ty',
}
code, body = request('/manage/events/new', jar, fields)
check('Tạo với CẢ 3 ô thời gian có giây → 302 thành công', code == 302, 'code=' + str(code))
created = db_check(lambda: Event.query.filter_by(name='Test giây cuối').first())
check('Sự kiện đã lưu vào CSDL', created is not None)
eid = created.id if created else 0

token, _ = get_csrf('/manage/events/new', jar)
fields2 = dict(fields); fields2['name'] = 'Test giây lỗi hạn'; fields2['registration_deadline'] = sec(now + timedelta(days=4))
code, body = request('/manage/events/new', jar, fields2)
check('Có giây + hạn ĐK sau thời gian diễn ra → báo lỗi đúng AC4', code == 200 and 'Thời hạn đăng ký phải trước hoặc bằng thời gian diễn ra' in body)

code, body = request('/manage/events', jar)
check('Trang quản lý có modal xác nhận hủy', 'cancelModal' in body and 'data-cancel-event' in body)
check('Không còn dùng confirm()', 'onsubmit="return confirm' not in body)

token, _ = get_csrf('/manage/events', jar)
code, body = request('/manage/events/' + str(eid) + '/cancel', jar, {'csrf_token': token})
check('POST hủy sự kiện → 302', code == 302, 'code=' + str(code))
check('Sự kiện chuyển trạng thái Đã hủy (giữ bản ghi — BR05)', db_check(lambda: db.session.get(Event, eid).is_cancelled) is True)
code, body = request('/manage/events', jar)
check('Flash "Hủy sự kiện thành công" hiển thị', 'Hủy sự kiện thành công' in body)

failed = len(results) - sum(results)
print('TỔNG: ' + str(sum(results)) + ' PASS / ' + str(failed) + ' FAIL')
sys.exit(1 if failed else 0)
