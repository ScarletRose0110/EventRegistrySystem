# -*- coding: utf-8 -*-
"""Smoke test Day 1: login, phan quyen, truy cap thang URL."""
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
    """Giu nguyen ma 302 de kiem tra chuyen huong - khong tu di theo."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(path, jar, data=None):
    opener = urllib.request.build_opener(
        NoRedirect, urllib.request.HTTPCookieProcessor(jar))
    if data is None:
        req = urllib.request.Request(BASE + path)
    else:
        req = urllib.request.Request(BASE + path, data=urllib.parse.urlencode(data).encode())
    try:
        r = opener.open(req)
        return r.getcode(), r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')


def login(jar, email, password):
    _, body = request('/login', jar)
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', body)
    token = m.group(1) if m else ''
    return request('/login', jar, {'csrf_token': token, 'email': email, 'password': password})


jar = http.cookiejar.CookieJar()
code, body = request('/login', jar)
check('GET /login -> 200 + form dang nhap', code == 200 and 'Đăng nhập' in body, 'code=' + str(code))
check('Form login co CSRF token', 'csrf_token' in body)

code, _ = request('/events', jar)
check('Chua dang nhap vao /events -> chuyen ve /login', code == 302, 'code=' + str(code))

code, _ = login(jar, 'a@xyz.com', '123456')
check('Login dung a@xyz.com -> 302', code == 302, 'code=' + str(code))
code, body = request('/events', jar)
check('Sau login: /events -> 200', code == 200, 'code=' + str(code))
check('Trang danh sach hien thi trang thai tinh dong',
      any(s in body for s in ('Đang mở đăng ký', 'Đã đủ số lượng', 'Hết hạn đăng ký', 'Đang diễn ra', 'Đã kết thúc', 'Đã hủy')))

jar2 = http.cookiejar.CookieJar()
code, body2 = login(jar2, 'a@xyz.com', 'sai-mat-khau')
check('Login sai mat khau -> o lai /login + loi chung',
      code == 200 and 'Email hoặc mật khẩu không đúng' in body2, 'code=' + str(code))

jar3 = http.cookiejar.CookieJar()
login(jar3, 'b@xyz.com', '123456')
code, body3 = request('/manage/events', jar3)
check('b (chi Employee) vao /manage/events -> 403', code == 403, 'code=' + str(code))
check('Trang 403 hien thi thong bao quyen', 'Bạn không có quyền' in body3)

jar4 = http.cookiejar.CookieJar()
login(jar4, 'c@xyz.com', '123456')
code, _ = request('/manage/events', jar4)
check('c (Admin+Organizer) vao /manage/events -> 200', code == 200, 'code=' + str(code))

code, _ = request('/events/999999', jar)
check('Chi tiet su kien khong ton tai -> quay lai danh sach', code == 302, 'code=' + str(code))

failed = len(results) - sum(results)
print('TỔNG: ' + str(sum(results)) + ' PASS / ' + str(failed) + ' FAIL')
sys.exit(1 if failed else 0)
