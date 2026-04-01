from flask import Blueprint, request, jsonify
from ..models import HoneypotEvent
from ..extensions import db

honeypot_bp = Blueprint("honeypot", __name__)

@honeypot_bp.route("/trap", methods=["GET", "POST", "PUT", "DELETE"])
def trap():
    body = request.get_data(as_text=True) or ""
    event = HoneypotEvent(
        client_ip=request.headers.get("X-Forwarded-For", request.remote_addr),
        path=request.path,
        payload=body[:4096],
        user_agent=request.headers.get("User-Agent"),
        extra={
            "method": request.method,
            "headers": dict(request.headers),
        },
    )
    db.session.add(event)
    db.session.commit()
    # Можно эмулировать уязвимый ответ
    return jsonify({"status": "ok"}), 200
