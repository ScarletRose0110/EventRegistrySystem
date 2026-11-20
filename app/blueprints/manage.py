from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from app.extensions import db
from app.forms.event import EventForm
from app.models import Department, Event, Registration
from app.services.event_status import STATUS_KEYS, compute_event_status
from app.services.notification import notify_all_active_users, notify_event_cancelled
from app.services.registration import REGISTRATION_STATUS_LABELS, list_event_registrations
from app.utils.decorators import roles_required
from app.utils.permissions import can_manage
from app.utils.text import normalize_text

manage_bp = Blueprint('manage', __name__, url_prefix='/manage')

# TODO Day 5 (US-11, US-05): xác nhận / không xác nhận và điểm danh trên danh sách đăng ký


def _active_count_map(events):
    ids = [e.id for e in events]
    if not ids:
        return {}
    rows = db.session.query(Registration.event_id, func.count(Registration.id)).filter(
        Registration.is_active == 1, Registration.event_id.in_(ids)).group_by(Registration.event_id).all()
    return dict(rows)


@manage_bp.route('/events')
@roles_required('Organizer', 'Admin')
def manage_events():
    query = Event.query
    if not current_user.has_role('Admin'):  # BR15
        query = query.filter(or_(
            Event.organizer_id == current_user.id,
            Event.department_id == current_user.department_id,
        ))
    events = query.order_by(Event.created_at.desc()).all()
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
    return render_template(
        'manage/manage_events.html',
        items=items,
        can_manage_all=current_user.has_role('Admin'),
    )


@manage_bp.route('/events/new', methods=['GET', 'POST'])
@login_required
def create_event():
    if not (current_user.has_role('Organizer') or current_user.has_role('Admin')):
        abort(403, description='Bạn không có quyền tạo sự kiện')  # US-03-AC1
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            name=form.name.data.strip(),
            description=form.description.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            location=form.location.data.strip(),
            max_attendees=form.max_attendees.data,
            registration_deadline=form.registration_deadline.data,
            target_audience=form.target_audience.data or 'Toàn công ty',
            organizer_id=current_user.id,
            department_id=current_user.department_id,  # US-03-AC5
        )
        db.session.add(event)
        db.session.commit()
        notify_all_active_users(event)  # BR30 / US-03-AC6
        flash('Tạo sự kiện thành công', 'success')  # US-03-AC3
        return redirect(url_for('manage.manage_events'))
    return render_template('manage/event_form.html', form=form, mode='create')


@manage_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    if not can_manage(current_user, event):
        abort(403, description='Bạn không có quyền chỉnh sửa sự kiện này')  # US-04A-AC4
    if not current_user.has_role('Admin'):
        if event.is_cancelled or event.start_time <= datetime.now():
            flash('Không thể chỉnh sửa sự kiện đã bắt đầu hoặc đã hủy', 'danger')  # US-04A-AC1
            return redirect(url_for('manage.manage_events'))

    form = EventForm(obj=event)
    form.creating = False  # BR11: khi sửa không kiểm tra lại 'sau thời điểm hiện tại'
    if form.validate_on_submit():
        active_count = _active_count_map([event]).get(event.id, 0)
        if form.max_attendees.data < active_count:
            flash('Số lượng tối đa không được nhỏ hơn số người đã đăng ký', 'danger')  # US-04A-AC3
            return render_template('manage/event_form.html', form=form, mode='edit', event=event)
        form.populate_obj(event)
        event.name = event.name.strip()
        event.location = event.location.strip()
        event.name_normalized = normalize_text(event.name)
        db.session.commit()
        flash('Cập nhật sự kiện thành công', 'success')  # US-04A-AC5
        return redirect(url_for('manage.manage_events'))
    return render_template('manage/event_form.html', form=form, mode='edit', event=event)


@manage_bp.route('/events/<int:event_id>/cancel', methods=['POST'])
@login_required
def cancel_event(event_id):
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    if not can_manage(current_user, event):
        abort(403, description='Bạn không có quyền hủy sự kiện này')  # US-04B-AC5
    if datetime.now() >= event.end_time:
        flash('Không thể hủy sự kiện đã kết thúc', 'danger')  # US-04B-AC1 / BR05
        return redirect(url_for('manage.manage_events'))
    event.is_cancelled = True  # US-04B-AC2
    db.session.commit()
    notify_event_cancelled(event)  # US-04B-AC3
    flash('Hủy sự kiện thành công', 'success')
    return redirect(url_for('manage.manage_events'))


@manage_bp.route('/events/<int:event_id>/registrations')
@login_required
def event_registrations(event_id):
    """US-10: xem và tìm kiếm danh sách người đăng ký của sự kiện."""
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    if not can_manage(current_user, event):  # US-10-AC6 / BR15, kể cả truy cập thẳng URL
        abort(403, description='Bạn không có quyền xem danh sách đăng ký của sự kiện này')

    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    if status not in REGISTRATION_STATUS_LABELS:
        status = ''
    department = request.args.get('department', type=int) or None

    rows, counts = list_event_registrations(event.id, q=q, status=status, department_id=department)
    active_count = counts['Registered'] + counts['Confirmed'] + counts['Attended']  # AC4
    return render_template(
        'manage/event_registrations.html',
        event=event,
        rows=rows,
        counts=counts,
        total=sum(counts.values()),
        active_count=active_count,
        status_labels=REGISTRATION_STATUS_LABELS,
        departments=Department.query.order_by(Department.name).all(),
        q=q, status=status, department=department,
        has_filter=bool(q or status or department),
    )
