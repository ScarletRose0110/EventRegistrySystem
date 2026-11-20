"""Nghiệp vụ đăng ký / hủy đăng ký / Sự kiện của tôi (US-01, US-02, US-09).

Mọi hàm ghi dữ liệu trả về tuple (ok: bool, message: str) để route chỉ việc flash().
"""
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Event, Registration, User
from app.utils.text import normalize_text
from app.services.event_status import (
    STATUS_DEADLINE_PASSED, STATUS_FULL, STATUS_OPEN,
)

# Trạng thái đăng ký mà nhân viên được phép tự hủy (BR23).
CANCELLABLE_STATUSES = ('Registered', 'Confirmed')


def _active_count(event_id):
    """Số đăng ký còn hiệu lực của sự kiện (BR01): is_active = 1."""
    return db.session.query(func.count(Registration.id)).filter(
        Registration.event_id == event_id, Registration.is_active == 1).scalar() or 0


def can_cancel_registration(reg, event, now=None):
    """Quy tắc duy nhất cho phép hủy — dùng cho cả nút trên giao diện lẫn khi xử lý POST.

    Hủy được khi: đăng ký còn hiệu lực, sự kiện chưa bị hủy, và chưa quá
    hạn đăng ký (BR09: hết hạn đăng ký thì không hủy được).
    """
    now = now or datetime.now()
    return (
        reg.is_active == 1
        and reg.status in CANCELLABLE_STATUSES
        and not event.is_cancelled
        and now <= event.registration_deadline
    )


def get_active_registration(event_id, user_id):
    """Đăng ký còn hiệu lực (is_active = 1) của người dùng với sự kiện, hoặc None."""
    return db.session.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.user_id == user_id,
        Registration.is_active == 1).first()


def register_block_reason(status):
    """Lý do không cho đăng ký theo trạng thái sự kiện (US-01-AC2/AC3/AC6); None nếu đang mở."""
    if status == STATUS_OPEN:
        return None
    if status == STATUS_FULL:
        return 'Sự kiện đã đủ số lượng đăng ký'
    if status == STATUS_DEADLINE_PASSED:
        return 'Đã hết hạn đăng ký sự kiện'
    return 'Sự kiện hiện không mở đăng ký'  # đã hủy / đang diễn ra / đã kết thúc


def register_for_event(event_id, user_id):
    """US-01. Thứ tự kiểm tra theo US-01-AC7: AC6 -> AC1 -> AC2 -> AC3."""
    try:
        # Khóa dòng sự kiện: 2 người đăng ký đồng thời chỗ cuối chỉ 1 người thành công (BR14).
        event = db.session.query(Event).filter(Event.id == event_id).with_for_update().first()
        if event is None:
            db.session.rollback()
            return False, 'Không tìm thấy sự kiện'

        now = datetime.now()
        # AC6: sự kiện đã hủy hoặc đã bắt đầu
        if event.is_cancelled or now >= event.start_time:
            db.session.rollback()
            return False, 'Sự kiện hiện không mở đăng ký'

        # AC1: đã đăng ký còn hiệu lực
        duplicated = db.session.query(Registration.id).filter(
            Registration.event_id == event_id,
            Registration.user_id == user_id,
            Registration.is_active == 1).first()
        if duplicated:
            db.session.rollback()
            return False, 'Bạn đã đăng ký sự kiện này'

        # AC2: đủ chỗ
        if _active_count(event_id) >= event.max_attendees:
            db.session.rollback()
            return False, 'Sự kiện đã đủ số lượng đăng ký'

        # AC3: quá hạn đăng ký
        if now > event.registration_deadline:
            db.session.rollback()
            return False, 'Đã hết hạn đăng ký sự kiện'

        reg = Registration(event_id=event_id, user_id=user_id, status='Registered')
        reg.set_active()
        db.session.add(reg)
        db.session.commit()
        return True, 'Đăng ký tham gia thành công'
    except IntegrityError:
        # Vi phạm uq_reg_active: có đăng ký trùng chen vào giữa 2 request
        db.session.rollback()
        return False, 'Bạn đã đăng ký sự kiện này'
    except Exception:
        db.session.rollback()
        raise


def cancel_registration(event_id, user_id):
    """US-02. Chỉ hủy đăng ký còn hiệu lực của chính người dùng, trước hạn đăng ký."""
    try:
        event = db.session.query(Event).filter(Event.id == event_id).with_for_update().first()
        if event is None:
            db.session.rollback()
            return False, 'Không tìm thấy sự kiện'

        reg = db.session.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.user_id == user_id,
            Registration.is_active == 1).first()
        if reg is None or reg.status not in CANCELLABLE_STATUSES or event.is_cancelled:
            db.session.rollback()
            return False, 'Đăng ký này không thể hủy'

        if not can_cancel_registration(reg, event):
            db.session.rollback()
            return False, 'Đã quá thời hạn hủy đăng ký'

        reg.status = 'Cancelled'
        reg.set_active()  # is_active -> NULL, nếu thiếu sẽ vi phạm ck_reg_active (BR01)
        db.session.commit()
        return True, 'Hủy đăng ký thành công'
    except Exception:
        db.session.rollback()
        raise


def get_my_events(user_id, status_filter=None):
    """US-09. Danh sách đăng ký của người dùng, mới nhất trước, kèm cờ can_cancel."""
    query = (
        db.session.query(Registration, Event)
        .join(Event, Registration.event_id == Event.id)
        .filter(Registration.user_id == user_id)
    )
    if status_filter and status_filter.lower() != 'all':
        query = query.filter(Registration.status == status_filter)

    now = datetime.now()
    return [
        {
            'registration': reg,
            'event': event,
            'can_cancel': can_cancel_registration(reg, event, now),
        }
        for reg, event in query.order_by(Registration.created_at.desc(), Registration.id.desc()).all()
    ]


# Thứ tự và nhãn hiển thị các trạng thái đăng ký (BR23)
REGISTRATION_STATUS_LABELS = {
    'Registered': 'Đã đăng ký',
    'Confirmed': 'Đã xác nhận',
    'Rejected': 'Không xác nhận',
    'Attended': 'Đã tham dự',
    'Cancelled': 'Đã hủy',
}


def list_event_registrations(event_id, q='', status='', department_id=None):
    """US-10. Danh sách người đăng ký của một sự kiện.

    Trả về (rows, counts):
    - rows: list[(Registration, User)] đã lọc, đăng ký sớm nhất lên trước (AC1).
      Tìm theo họ tên không phân biệt hoa thường và có/không dấu (AC2); lọc theo
      trạng thái và phòng ban, kết hợp được với tìm kiếm (AC3).
    - counts: số đăng ký theo từng trạng thái của TOÀN BỘ sự kiện, không phụ thuộc bộ lọc (AC4).
    """
    all_rows = (
        db.session.query(Registration, User)
        .join(User, Registration.user_id == User.id)
        .filter(Registration.event_id == event_id)
        .order_by(Registration.created_at.asc(), Registration.id.asc())
        .all()
    )
    counts = {key: 0 for key in REGISTRATION_STATUS_LABELS}
    for reg, _user in all_rows:
        counts[reg.status] = counts.get(reg.status, 0) + 1

    keyword = normalize_text(q) if q else ''
    rows = [
        (reg, user) for reg, user in all_rows
        if (not keyword or keyword in normalize_text(user.full_name))
        and (not status or reg.status == status)
        and (not department_id or user.department_id == department_id)
    ]
    return rows, counts
