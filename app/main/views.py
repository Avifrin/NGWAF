from flask import Blueprint, jsonify

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return jsonify({"status": "ok", "message": "Protected backend"})

@main_bp.route("/api/data")
def api_data():
    return jsonify({"data": [1, 2, 3]})
