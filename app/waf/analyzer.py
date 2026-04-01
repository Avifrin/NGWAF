import time
from flask import Request
from .reputation import get_ip_reputation, update_ip_reputation
from ..extensions import redis_client
from .rules import PATTERNS, load_rules
from urllib.parse import unquote, parse_qs

def _behavior_score(ip: str, path: str) -> float:
    now = int(time.time())
    key = f"freq:{ip}:{path}:{now}"
    cnt = redis_client.client.incr(key)
    redis_client.client.expire(key, 60)
    if cnt > 100:
        return 1.0
    return cnt / 100.0


def analyze_request(req: Request, body_text: str):
    ip = req.headers.get("X-Forwarded-For", req.remote_addr or "unknown")

    query_decoded = unquote(req.query_string.decode('utf-8'))
    args_decoded = " ".join(unquote(k) + "=" + unquote(v) for k, vlist in req.args.lists() for v in vlist)

    if body_text:
        try:
            body_text = unquote(body_text)
        except:
            pass

    text_for_match = " ".join([
        req.method,
        req.path,
        query_decoded,
        args_decoded,
        body_text or "",
        " ".join([f"{k}:{unquote(v)}" for k, v in req.headers.items()])
    ])

    sig_matches = []
    for regex, tag, severity in PATTERNS:
        if regex.search(text_for_match):
            sig_matches.append((tag, severity))
            print(f"✅ НАЙДЕНО: {tag} in '{text_for_match[:100]}...'")
    sig_score = sum(sev * 0.4 for _, sev in sig_matches)

    beh_score = _behavior_score(ip, req.path) * 0.4
    rep_score = get_ip_reputation(ip) * 0.2

    total_score = min(sig_score + beh_score + rep_score, 1.0)

    decision = "allow"
    reason = "ok"

    if total_score >= 0.6:
        decision = "honeypot"
        reason = f"high score {total_score:.2f}, sigs={sig_matches}"
        update_ip_reputation(ip, 0.2)
    elif total_score >= 0.4:
        decision = "block"
        reason = f"medium score {total_score:.2f}, sigs={sig_matches}"
        update_ip_reputation(ip, 0.1)

    return {
        "ip": ip,
        "score": total_score,
        "decision": decision,
        "reason": reason,
        "sigs": sig_matches,
    }