# app/tracker.py
from flask import Flask, request, redirect, abort
from .db import get_conn
import time, os, logging
from .config import TRACKER_PORT

app = Flask(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


def client_ip():
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


@app.route("/r/<int:aid>")
def redirect_affiliate(aid):
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
    app.run(host="0.0.0.0", port=TRACKER_PORT)
