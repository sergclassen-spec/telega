# app/tracker.py
"""
Lightweight Flask tracker for affiliate redirects.
- Uses X-Forwarded-For header when present.
- Logs clicks into clicks table.
"""

from flask import Flask, redirect, request, abort
import os, time
from .db import get_conn
from .config import DB_PATH

app = Flask(__name__)


def client_ip():
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


@app.route("/r/<int:aid>")
def redirect_affiliate(aid: int):
    conn = get_conn(); cur = conn.cursor()
    row = cur.execute("SELECT target_url FROM affiliates WHERE id=?", (aid,)).fetchone()
    if not row:
        conn.close(); return abort(404)
    target = row["target_url"]
    cur.execute("INSERT INTO clicks (affiliate_id, post_id, ts, ip, ua) VALUES (?,?,?,?,?)",
                (aid, None, int(time.time()), client_ip(), request.headers.get("User-Agent")))
    conn.commit(); conn.close()
    return redirect(target)


if __name__ == "__main__":
    # For development only: run Flask built-in server
    app.run(host="0.0.0.0", port=int(os.getenv("TRACKER_PORT", "5000")))
