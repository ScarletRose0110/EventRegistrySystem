from app.extensions import db


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # tên duy nhất (US-15-AC3)
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # Hoạt động / Ngừng (BR21)

    users = db.relationship('User', back_populates='department')
    events = db.relationship('Event', back_populates='department')

    def __repr__(self):
        return f'<Department {self.name}>'
