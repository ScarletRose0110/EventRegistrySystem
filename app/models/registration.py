from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db

VALID_STATUSES = ('Registered', 'Confirmed', 'Rejected', 'Cancelled', 'Attended')
ACTIVE_STATUSES = ('Registered', 'Confirmed', 'Attended')


class Registration(db.Model):
    __tablename__ = 'registrations'
    __table_args__ = (
        CheckConstraint(
            "status IN ('Registered','Confirmed','Rejected','Cancelled','Attended')",
            name='ck_reg_status',
        ),
        # BR01: is_active = 1 khi status còn hiệu lực, NULL khi Cancelled/Rejected
        CheckConstraint(
            "(is_active = 1 AND status IN ('Registered','Confirmed','Attended')) "
            "OR (is_active IS NULL AND status IN ('Rejected','Cancelled'))",
            name='ck_reg_active',
        ),
        UniqueConstraint('event_id', 'user_id', 'is_active', name='uq_reg_active'),
    )

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Registered')
    rejection_reason = db.Column(db.String(500), nullable=True)  # lý do từ chối (US-11-AC4)
    is_active = db.Column(db.Integer, nullable=True)  # 1 hoặc NULL (BR01)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    event = db.relationship('Event', back_populates='registrations')
    user = db.relationship('User', back_populates='registrations')

    def set_active(self):
        self.is_active = 1 if self.status in ACTIVE_STATUSES else None

    def __repr__(self):
        return f'<Registration event={self.event_id} user={self.user_id} {self.status}>'
