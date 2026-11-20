from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.services import registration as reg_service

reg_bp = Blueprint('registrations', __name__)


@reg_bp.route('/my-events', methods=['GET'])
@login_required
def my_events():
    """US-09: Sự kiện của tôi."""
    status_filter = request.args.get('status', 'all')
    return render_template(
        'registrations/my_events.html',
        events_data=reg_service.get_my_events(current_user.id, status_filter),
        current_status=status_filter,
    )


@reg_bp.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def register(event_id):
    """US-01: đăng ký tham gia sự kiện."""
    ok, message = reg_service.register_for_event(event_id, current_user.id)
    flash(message, 'success' if ok else 'danger')
    return redirect(url_for('events.event_detail', event_id=event_id))


@reg_bp.route('/events/<int:event_id>/cancel-registration', methods=['POST'])
@login_required
def cancel_registration(event_id):
    """US-02: hủy đăng ký của chính mình."""
    ok, message = reg_service.cancel_registration(event_id, current_user.id)
    flash(message, 'success' if ok else 'danger')
    return redirect(url_for('registrations.my_events'))
