from app.extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=True)
    content = db.Column(db.String(500), nullable=False)
    email_sent = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    recipient = db.relationship('User', back_populates='notifications')
    event = db.relationship('Event', back_populates='notifications')

    def __repr__(self):
        return f'<Notification to={self.recipient_id}>'
