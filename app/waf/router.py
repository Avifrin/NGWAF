from flask import Blueprint, request, jsonify, redirect, url_for
from .analyzer import analyze_request
from ..models import RequestLog
from ..extensions import db

waf_bp = Blueprint("waf", __name__)

@waf_bp.before_app_request  # _app_ т.к. блупринт
def waf_middleware():

    if request.path.startswith(("/static", "/dashboard")):
        return None

    body = ""
    if request.method in ("POST", "PUT", "PATCH"):
        body = request.get_data(as_text=True) or ""

    result = analyze_request(request, body)
    print(result)

    log = RequestLog(
        client_ip=result["ip"],
        method=request.method,
        path=request.path,
        query_string=request.query_string.decode('utf-8') if request.query_string else None,
        headers=dict(request.headers),
        body=body[:4096],
        content_type=request.content_type,
        score=result["score"],
        decision=result["decision"],
        reason=result["reason"],
    )
    db.session.add(log)
    db.session.commit()

    if result["decision"] == "allow":
        return None
    elif result["decision"] == "block":
        return jsonify({"status": "blocked", "reason": result["reason"]}), 403
    elif result["decision"] == "honeypot":
        from ..honeypot.views import trap
        return trap()
