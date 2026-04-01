# dashboard/views.py

from flask import Blueprint, render_template, request, jsonify, abort
from ..extensions import db
from sqlalchemy import text, desc
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint("dashboard", __name__, template_folder="../templates")


def get_stats():
    """100% raw SQL — никаких моделей!"""
    with db.engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM request_log")).scalar()
        blocked = conn.execute(text("SELECT COUNT(*) FROM request_log WHERE decision = 'block'")).scalar()
        honeypot = conn.execute(text("SELECT COUNT(*) FROM request_log WHERE decision = 'honeypot'")).scalar()
        avg_score = conn.execute(text("SELECT AVG(score) FROM request_log")).scalar() or 0.0

        top_ips = conn.execute(text("""
            SELECT client_ip, COUNT(*) as cnt 
            FROM request_log 
            WHERE decision = 'block' 
            GROUP BY client_ip 
            ORDER BY cnt DESC 
            LIMIT 5
        """)).fetchall()

        return {
            'total': int(total) if total else 0,
            'blocked': int(blocked) if blocked else 0,
            'honeypot_count': int(honeypot) if honeypot else 0,
            'avg_score': round(float(avg_score), 2),
            'top_ips_labels': [row[0] for row in top_ips],
            'top_ips_values': [int(row[1]) for row in top_ips]
        }


@dashboard_bp.route("/")
def index():
    stats = get_stats()

    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Raw SQL для списка запросов
    with db.engine.connect() as conn:
        where_clause = "1=1"
        params = {}

        status = request.args.get('status')
        search = request.args.get('search', '').strip()

        if status:
            where_clause += " AND decision = :status"
            params['status'] = status
        if search:
            where_clause += " AND (client_ip ILIKE :search OR path ILIKE :search)"
            params['search'] = f'%{search}%'

        total_count = conn.execute(text(f"""
            SELECT COUNT(*) FROM request_log WHERE {where_clause}
        """), params).scalar()

        requests = conn.execute(text(f"""
            SELECT id, timestamp, client_ip, method, path, score, decision, reason
            FROM request_log 
            WHERE {where_clause}
            ORDER BY timestamp DESC 
            LIMIT :limit OFFSET :offset
        """), {**params, 'limit': per_page, 'offset': offset}).fetchall()

    return render_template(
        "dashboard/index.html",
        last_requests=[{
            'id': r[0], 'timestamp': r[1], 'client_ip': r[2], 'method': r[3],
            'path': r[4], 'score': r[5], 'decision': r[6], 'reason': r[7]
        } for r in requests],
        total_requests=int(total_count) if total_count else 0,
        stats=stats,
        hours=json.dumps([]),
        total_per_hour=json.dumps([]),
        blocked_per_hour=json.dumps([]),
        current_page=page,
        total_pages=(int(total_count) + per_page - 1) // per_page if total_count else 1,
        status_filter=status,
        search_query=search,
        per_page=per_page,
    )


@dashboard_bp.route("/request/<int:req_id>")
def request_detail(req_id):
    with db.engine.connect() as conn:
        log = conn.execute(text("""
            SELECT id, timestamp, client_ip, method, path, headers, body, 
                   score, decision, reason
            FROM request_log WHERE id = :id
        """), {'id': req_id}).fetchone()

        if not log:
            abort(404)

        log = {
            'id': log[0], 'timestamp': log[1], 'client_ip': log[2],
            'method': log[3], 'path': log[4], 'headers': log[5],
            'body': log[6], 'score': log[7], 'decision': log[8],
            'reason': log[9], 'query_string': None, 'content_type': None
        }

        related = conn.execute(text("""
            SELECT id, timestamp, path, score, decision
            FROM request_log 
            WHERE client_ip = :ip AND id != :id 
            ORDER BY timestamp DESC LIMIT 10
        """), {'ip': log['client_ip'], 'id': req_id}).fetchall()

    return render_template("dashboard/request_detail.html",
                           log=log,
                           related=[{
                               'id': r[0], 'timestamp': r[1], 'path': r[2],
                               'score': r[3], 'decision': r[4]
                           } for r in related])


@dashboard_bp.route("/stats/api")
def stats_api():
    stats = get_stats()
    return jsonify(stats)
