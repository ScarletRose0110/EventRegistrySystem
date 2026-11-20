"""Thông báo nội bộ (BR30, US-04B-AC3, US-11-AC6).

Ghi bản ghi vào bảng notifications; email thật là bước sau (cột email_sent).
"""
from app.extensions import db
from app.models import Notification, User


def notify_users(recipients, event, content):
    for user in recipients:
        db.session.add(Notification(
            recipient_id=user.id,
            event_id=event.id if event is not None else None,
            content=content,
        ))
    db.session.commit()


def notify_all_active_users(event):
    """BR30: sự kiện mới → thông báo toàn bộ nhân viên đang hoạt động."""
    users = User.query.filter_by(is_locked=False).all()
    content = (
        f'Sự kiện mới: {event.name}, {event.start_time:%d/%m/%Y %H:%M}, '
        f'{event.location}. Hạn đăng ký: {event.registration_deadline:%d/%m/%Y %H:%M}'
    )
    notify_users(users, event, content)


def notify_event_cancelled(event):
    """US-04B-AC3: thông báo cho người có đăng ký còn hiệu lực."""
    users = [reg.user for reg in event.registrations if reg.is_active == 1]
    content = f'Sự kiện {event.name} ngày {event.start_time:%d/%m/%Y %H:%M} đã bị hủy'
    notify_users(users, event, content)
