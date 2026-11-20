from sqlalchemy import CheckConstraint

from app.extensions import db

VALID_ROLES = ('Employee', 'Organizer', 'Admin')


class UserRole(db.Model):
    __tablename__ = 'user_roles'
    __table_args__ = (
        CheckConstraint("role IN ('Employee', 'Organizer', 'Admin')", name='ck_user_roles_role'),
    )

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    role = db.Column(db.String(20), primary_key=True)  # BR18: một tài khoản nhiều role

    user = db.relationship('User', back_populates='roles')

    def __repr__(self):
        return f'<UserRole {self.user_id}:{self.role}>'
