from apscheduler.schedulers.background import BackgroundScheduler
from app.rss_fetcher import fetch_rss
from app.generator import generate_from_rss
from app.poster import post_to_telegram


def job():
    items = fetch_rss()
    generated = generate_from_rss(items)
    print(f"Generated {generated} posts.")


def run_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, 'interval', minutes=30)
    scheduler.start()
    print("Scheduler started.")
