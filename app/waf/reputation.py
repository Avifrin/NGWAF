from ..extensions import redis_client

def get_ip_reputation(ip: str) -> float:
    score = redis_client.client.get(f"ip_rep:{ip}")
    if score is None:
        return 0.0
    return float(score)

def update_ip_reputation(ip: str, delta: float):
    key = f"ip_rep:{ip}"
    current = get_ip_reputation(ip)
    new_score = max(0.0, min(1.0, current + delta))
    redis_client.client.set(key, new_score, ex=24 * 3600)
