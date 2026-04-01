from datetime import datetime
from .extensions import db

class RequestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    client_ip = db.Column(db.String(64), index=True)
    method = db.Column(db.String(10))
    path = db.Column(db.String(255))
    headers = db.Column(db.JSON)
    body = db.Column(db.Text)
    score = db.Column(db.Float)
    decision = db.Column(db.String(32))  # allow / block / honeypot
    reason = db.Column(db.String(255))
    query_string = db.Column(db.Text)  # Добавь для ?params
    content_type = db.Column(db.String(255))

class HoneypotEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    client_ip = db.Column(db.String(64))
    path = db.Column(db.String(255))
    payload = db.Column(db.Text)
    user_agent = db.Column(db.String(255))
    extra = db.Column(db.JSON)
