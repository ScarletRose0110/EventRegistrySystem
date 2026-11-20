from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)  # BR16
    password_hash = db.Column(db.String(255), nullable=False)  # băm một chiều (US-06-AC7)
    full_name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    is_locked = db.Column(db.Boolean, nullable=False, default=False)  # BR17

    department = db.relationship('Department', back_populates='users')
    roles = db.relationship('UserRole', back_populates='user', cascade='all, delete-orphan')
    events_organized = db.relationship('Event', back_populates='organizer')
    registrations = db.relationship('Registration', back_populates='user')
    notifications = db.relationship('Notification', back_populates='recipient')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        return any(r.role == role for r in self.roles)

    @property
    def role_names(self):
        return sorted(r.role for r in self.roles)  # BR18: menu gộp tất cả role

    def __repr__(self):
        return f'<User {self.email}>'
