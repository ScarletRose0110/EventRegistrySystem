from sqlalchemy import CheckConstraint

from app.extensions import db
from app.utils.text import normalize_text


class Event(db.Model):
    __tablename__ = 'events'
    __table_args__ = (
        CheckConstraint('max_attendees >= 1', name='ck_events_max_attendees'),
        CheckConstraint('registration_deadline <= start_time', name='ck_events_deadline'),
        CheckConstraint('start_time < end_time', name='ck_events_time'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # độ dài tối đa tự chọn → test biên
    name_normalized = db.Column(db.String(200), nullable=False, default='', server_default='', index=True)  # tìm không dấu
    description = db.Column(db.Text, nullable=False)  # ≤ 2000 ký tự (validate app)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    max_attendees = db.Column(db.Integer, nullable=False)
    registration_deadline = db.Column(db.DateTime, nullable=False)
    target_audience = db.Column(db.String(100), nullable=False, default='Toàn công ty')  # BR08
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # US-03-AC5
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    is_cancelled = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    organizer = db.relationship('User', back_populates='events_organized')
    department = db.relationship('Department', back_populates='events')
    registrations = db.relationship('Registration', back_populates='event')
    notifications = db.relationship('Notification', back_populates='event')

    def __init__(self, **kwargs):
        if 'name' in kwargs and 'name_normalized' not in kwargs:
            kwargs['name_normalized'] = normalize_text(kwargs['name'])
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Event {self.name}>'
