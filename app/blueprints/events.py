from datetime import datetime, timedelta
from math import ceil

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Department, Event, Registration
from app.services.event_status import STATUS_KEYS, STATUS_ORDER, compute_event_status
from app.services.registration import (
    can_cancel_registration, get_active_registration, register_block_reason,
)
from app.utils.text import normalize_text

events_bp = Blueprint('events', __name__)
PER_PAGE = 9


@events_bp.route('/')
@login_required
def index():
    return redirect(url_for('events.list_events'))


def _active_count_map(events):
    ids = [e.id for e in events]
    if not ids:
        return {}
    rows = db.session.query(Registration.event_id, func.count(Registration.id)).filter(
        Registration.is_active == 1, Registration.event_id.in_(ids)).group_by(Registration.event_id).all()
    return dict(rows)


def _build_items(events):
    counts = _active_count_map(events)
    items = []
    for event in events:
        active_count = counts.get(event.id, 0)
        status = compute_event_status(event, active_count=active_count)
        items.append({
            'event': event,
            'active_count': active_count,
            'status': status,
            'status_key': STATUS_KEYS.get(status, 'deadline'),
        })
    return items


@events_bp.route('/events')
@login_required
def list_events():
    q = request.args.get('q', '').strip()
    department = request.args.get('department', type=int) or None
    status = request.args.get('status', '').strip()
    from_date = request.args.get('from_date', '').strip()
    to_date = request.args.get('to_date', '').strip()
    page = max(1, request.args.get('page', 1, type=int))

    now = datetime.now()
    f = t = None
    if from_date:
        try:
            f = datetime.strptime(from_date, '%Y-%m-%d')
        except ValueError:
            f = None
    if to_date:
        try:
            t = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            t = None
    if f and t and f >= t:
        flash('Ngày bắt đầu không được sau ngày kết thúc', 'danger')  # US-07-AC5
        f = t = None  # không thực hiện lọc

    has_filter = bool(q or department or status or f or t)
    query = Event.query
    if q:
        query = query.filter(Event.name_normalized.like('%' + normalize_text(q) + '%'))  # US-07-AC3
    if department:
        query = query.filter(Event.department_id == department)
    if f:
        query = query.filter(Event.start_time >= f)
    if t:
        query = query.filter(Event.start_time < t)
    if not has_filter:
        # US-07-AC2: mặc định chỉ hiện sự kiện chưa bắt đầu, chưa hủy, gần nhất trước
        query = query.filter(Event.is_cancelled.is_(False), Event.start_time > now)

    events = query.order_by(Event.start_time.asc()).all()
    items = _build_items(events)
    if status:
        items = [item for item in items if item['status'] == status]

    total = len(items)
    pages = max(1, ceil(total / PER_PAGE))
    page = min(page, pages)
    page_items = items[(page - 1) * PER_PAGE: page * PER_PAGE]

    pagination = []
    for n in range(1, pages + 1):
        if n == 1 or n == pages or abs(n - page) <= 2:
            pagination.append({'num': n, 'ellipsis': False, 'url': url_for(
                'events.list_events', page=n, q=q, department=department,
                status=status, from_date=from_date, to_date=to_date)})
        elif pagination and not pagination[-1]['ellipsis']:
            pagination.append({'num': None, 'ellipsis': True})

    return render_template(
        'events/list.html',
        items=page_items,
        q=q, department=department, status=status,
        from_date=from_date, to_date=to_date,
        departments=Department.query.order_by(Department.name).all(),
        status_options=STATUS_ORDER,
        pagination=pagination, page=page, pages=pages,
        total=total, has_filter=has_filter,
    )


@events_bp.route('/events/<int:event_id>')
@login_required
def event_detail(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        flash('Không tìm thấy sự kiện', 'warning')  # US-08-AC5
        return redirect(url_for('events.list_events'))
    active_count = db.session.query(func.count(Registration.id)).filter(
        Registration.event_id == event.id, Registration.is_active == 1).scalar() or 0
    status = compute_event_status(event, active_count=active_count)
    registration = get_active_registration(event.id, current_user.id)
    return render_template(
        'events/detail.html',
        event=event,
        status=status,
        status_key=STATUS_KEYS.get(status, 'deadline'),
        active_count=active_count,
        registration=registration,                                  # đăng ký còn hiệu lực của tôi
        can_cancel=bool(registration) and can_cancel_registration(registration, event),
        register_block_reason=register_block_reason(status),         # None = đang mở đăng ký
    )
