"""Hàm DUY NHẤT tính trạng thái sự kiện (sheet Trạng thái).

Dùng chung cho: danh sách (US-07), chi tiết (US-08), My Events (US-09) và test.
Không lưu trạng thái vào CSDL — luôn tính từ thời điểm hiện tại, số đăng ký
còn hiệu lực và cờ hủy.
"""
from datetime import datetime, timedelta

CHECKIN_GRACE_MINUTES = 30  # BR13: điểm danh tối đa 30 phút sau khi kết thúc

STATUS_OPEN = 'Đang mở đăng ký'
STATUS_FULL = 'Đã đủ số lượng'
STATUS_DEADLINE_PASSED = 'Hết hạn đăng ký'
STATUS_ONGOING = 'Đang diễn ra'
STATUS_FINISHED = 'Đã kết thúc'
STATUS_CANCELLED = 'Đã hủy'

STATUS_KEYS = {
    STATUS_OPEN: 'open',
    STATUS_FULL: 'full',
    STATUS_DEADLINE_PASSED: 'deadline',
    STATUS_ONGOING: 'ongoing',
    STATUS_FINISHED: 'finished',
    STATUS_CANCELLED: 'cancelled',
}
STATUS_ORDER = [
    STATUS_OPEN, STATUS_FULL, STATUS_DEADLINE_PASSED,
    STATUS_ONGOING, STATUS_FINISHED, STATUS_CANCELLED,
]


def compute_event_status(event, now=None, active_count=None):
    now = now or datetime.now()
    if event.is_cancelled:
        return STATUS_CANCELLED
    if now < event.start_time:
        if active_count is None:
            active_count = sum(1 for r in event.registrations if r.is_active == 1)
        if active_count >= event.max_attendees:
            return STATUS_FULL
        if now > event.registration_deadline:
            return STATUS_DEADLINE_PASSED
        return STATUS_OPEN
    if now <= event.end_time + timedelta(minutes=CHECKIN_GRACE_MINUTES):
        return STATUS_ONGOING
    return STATUS_FINISHED
