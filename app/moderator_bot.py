# app/moderator_bot.py
"""
Moderator bot: provides interactive moderation UI for posts in 'on_moderation' status.
Uses python-telegram-bot v20+ (async).
"""

import logging
import time
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from .db import get_conn, ensure_schema
from .utils import openai_chat, get_random_image_from_bank, post_message_to_channel, post_photo_to_channel
from .config import MODERATOR_BOT_TOKEN, MODERATOR_CHAT_ID, AVAILABLE_CATEGORIES, CHANNELS, PUBLISHER_BOT_TOKEN, PUBLISHER_CHANNEL_ID

logger = logging.getLogger("app.moderator")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def fetch_next_on_moderation():
    conn = get_conn(); c = conn.cursor()
    row = c.execute("SELECT * FROM posts WHERE status='on_moderation' ORDER BY created_at DESC LIMIT 1").fetchone()
    conn.close(); return row


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MODERATOR_CHAT_ID:
        await update.message.reply_text("⛔ Access denied.")
        return
    await update.message.reply_text("Moderator bot active. Use /moderate to review posts.")


async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MODERATOR_CHAT_ID:
        await update.message.reply_text("⛔ Access denied."); return

    row = fetch_next_on_moderation()
    if not row:
        await update.message.reply_text("✅ No posts awaiting moderation."); return

    post = dict(row)
    channel_name = CHANNELS.get(post.get("channel_id"), f"Channel {post.get('channel_id')}")
    kb = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{post['id']}"),
         InlineKeyboardButton("❌ Reject", callback_data=f"reject_{post['id']}")],
        [InlineKeyboardButton("✏️ Improve with AI", callback_data=f"improve_{post['id']}"),
         InlineKeyboardButton("🎲 Random Image", callback_data=f"randimg_{post['id']}")],
        [InlineKeyboardButton("🏷️ Set Category", callback_data=f"setcat_{post['id']}")]
    ]
    reply = InlineKeyboardMarkup(kb)
    text = f"📋 Post ID: {post['id']}\n📺 Channel: {channel_name}\n🏷️ Category: {post.get('category') or 'Not set'}\n\n{post['text']}"
    if post.get("image_path") and os.path.exists(post["image_path"]):
        with open(post["image_path"], "rb") as ph:
            await update.message.reply_photo(photo=ph, caption=text, reply_markup=reply)
    else:
        await update.message.reply_text(text, reply_markup=reply)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.from_user.id != MODERATOR_CHAT_ID:
        await query.edit_message_text("⛔ Access denied."); return

    data = query.data
    conn = get_conn(); cur = conn.cursor()
    try:
        if data.startswith("approve_"):
            pid = int(data.split("_", 1)[1])
            cur.execute("UPDATE posts SET status=?, updated_at=? WHERE id=?", ("approved", int(time.time()), pid))
            conn.commit()
            await query.edit_message_text(f"✅ Post {pid} moved to APPROVED.")
        elif data.startswith("reject_"):
            pid = int(data.split("_", 1)[1])
            cur.execute("UPDATE posts SET status=?, updated_at=? WHERE id=?", ("rejected", int(time.time()), pid))
            conn.commit()
            await query.edit_message_text(f"❌ Post {pid} rejected.")
        elif data.startswith("improve_"):
            pid = int(data.split("_", 1)[1])
            r = cur.execute("SELECT text FROM posts WHERE id=?", (pid,)).fetchone()
            if not r:
                await query.edit_message_text("Post not found."); return
            await query.edit_message_text("🔄 Improving text with AI...")
            improved = openai_chat(f"Improve this Telegram post and keep <=280 chars for engagement: {r['text']}", max_tokens=120)
            if improved:
                cur.execute("UPDATE posts SET text=?, updated_at=? WHERE id=?", (improved, int(time.time()), pid)); conn.commit()
                await query.edit_message_text("✅ Text improved and saved.")
            else:
                await query.edit_message_text("❌ AI improvement failed.")
        elif data.startswith("randimg_"):
            pid = int(data.split("_", 1)[1])
            img = get_random_image_from_bank()
            if not img:
                await query.edit_message_text("❌ No images in bank.")
            else:
                cur.execute("UPDATE posts SET image_path=?, updated_at=? WHERE id=?", (img, int(time.time()), pid)); conn.commit()
                await query.edit_message_text("✅ Random image applied.")
        elif data.startswith("setcat_do_"):
            # pattern: setcat_do_<pid>_<category>
            parts = data.split("_", 3)
            if len(parts) == 4:
                pid = int(parts[2])
                cat = parts[3]
                cur.execute("UPDATE posts SET category=?, updated_at=? WHERE id=?", (cat, int(time.time()), pid)); conn.commit()
                await query.edit_message_text(f"✅ Category set to {cat} for post {pid}")
            else:
                await query.edit_message_text("Invalid category selection.")
        elif data.startswith("setcat_"):
            pid = int(data.split("_", 1)[1])
            kb = [[InlineKeyboardButton(cat.capitalize(), callback_data=f"setcat_do_{pid}_{cat}")] for cat in AVAILABLE_CATEGORIES]
            await query.edit_message_text("Select category:", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await query.edit_message_text("Unknown action.")
    except Exception as e:
        logger.exception("Callback handling error: %s", e)
        await query.edit_message_text("❌ Error processing action.")
    finally:
        conn.close()


async def rejected_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MODERATOR_CHAT_ID:
        await update.message.reply_text("⛔ Access denied."); return
    conn = get_conn(); cur = conn.cursor()
    rows = cur.execute("SELECT id, text, updated_at FROM posts WHERE status='rejected' ORDER BY updated_at DESC LIMIT 10").fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No rejected posts"); return
    out = "\n\n".join([f"ID:{r['id']} - {r['text'][:120]}" for r in rows])
    await update.message.reply_text(out)


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MODERATOR_CHAT_ID:
        await update.message.reply_text("⛔ Access denied."); return
    conn = get_conn(); cur = conn.cursor()
    on_mod = cur.execute("SELECT COUNT(1) as cnt FROM posts WHERE status='on_moderation'").fetchone()["cnt"]
    rejected = cur.execute("SELECT COUNT(1) as cnt FROM posts WHERE status='rejected'").fetchone()["cnt"]
    published = cur.execute("SELECT COUNT(1) as cnt FROM posts WHERE status='published'").fetchone()["cnt"]
    conn.close()
    await update.message.reply_text(f"On moderation: {on_mod}\nRejected: {rejected}\nPublished: {published}")


def main():
    ensure_schema()
    app = Application.builder().token(MODERATOR_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("moderate", moderate))
    app.add_handler(CommandHandler("rejected", rejected_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    logger.info("Moderator bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
