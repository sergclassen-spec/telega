from flask import Flask, request
import sqlite3, html
from app.db import get_connection

app = Flask(__name__)


def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)


@app.route("/track")
def track():
    aid = html.escape(request.args.get("aid", "unknown"))
    ip = get_client_ip()
    conn = get_connection()
    conn.execute("INSERT INTO clicks (aid, ip) VALUES (?, ?)", (aid, ip))
    conn.commit()
    conn.close()
    return "OK"
