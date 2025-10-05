# API Reference

## OpenAI Integration

### Chat Completions API

**Endpoint**: `https://api.openai.com/v1/chat/completions`

**Usage in Code**: `app/utils.py:openai_chat()`

```python
def openai_chat(prompt: str, max_tokens: int = 250, temperature: float = 0.8) -> str:
    """Call OpenAI ChatCompletions via REST API"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
```

**Parameters**:
- `prompt`: Input text for content generation
- `max_tokens`: Maximum tokens to generate (default: 250)
- `temperature`: Randomness level 0.0-1.0 (default: 0.8)

**Retry Logic**: 3 attempts with exponential backoff (2s, 4s, 6s)

### Embeddings API

**Endpoint**: `https://api.openai.com/v1/embeddings`

**Usage in Code**: `app/utils.py:openai_embedding()`

```python
def openai_embedding(text: str) -> Optional[list]:
    """Get embedding vector from OpenAI REST API"""
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": EMBEDDING_MODEL,
        "input": text
    }
```

**Parameters**:
- `text`: Input text to embed
- `model`: Embedding model (default: "text-embedding-3-small")

**Returns**: List of float values representing the embedding vector

## Telegram Bot API

### Send Message

**Endpoint**: `https://api.telegram.org/bot{token}/sendMessage`

**Usage in Code**: `app/utils.py:post_message_to_channel()`

```python
def post_message_to_channel(token: str, channel_id: str, text: str):
    """Send text message via Telegram Bot API"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text,
        "disable_web_page_preview": True
    }
```

**Parameters**:
- `token`: Bot token for authentication
- `channel_id`: Target channel ID (e.g., -1001234567890)
- `text`: Message content

### Send Photo

**Endpoint**: `https://api.telegram.org/bot{token}/sendPhoto`

**Usage in Code**: `app/utils.py:post_photo_to_channel()`

```python
def post_photo_to_channel(token: str, channel_id: str, photo_path: str, caption: str):
    """Send photo with caption via Telegram Bot API"""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(photo_path, "rb") as f:
        files = {"photo": f}
        data = {
            "chat_id": channel_id,
            "caption": caption,
            "disable_web_page_preview": True
        }
```

**Parameters**:
- `token`: Bot token for authentication
- `channel_id`: Target channel ID
- `photo_path`: Local path to image file
- `caption`: Photo caption text

## Database API

### Connection Management

**Function**: `app/db.py:get_conn()`

```python
def get_conn():
    """Return sqlite3 connection with WAL and row factory"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn
```

**Features**:
- WAL mode for better concurrency
- Row factory for dictionary-like access
- Thread-safe connection handling

### Schema Management

**Function**: `app/db.py:ensure_schema()`

Creates the following tables:
- `posts`: Main content storage
- `affiliates`: Affiliate link management
- `clicks`: Click tracking data

### Query Functions

#### Count Posts by Status
```python
def count_posts_with_status(status: str) -> int:
    """Count posts with specific status"""
    conn = get_conn()
    c = conn.cursor()
    r = c.execute("SELECT COUNT(1) as cnt FROM posts WHERE status = ?", (status,)).fetchone()
    conn.close()
    return int(r["cnt"]) if r else 0
```

#### Get Old Posts for Cleanup
```python
def get_old_rejected_and_stale(on_moderation_days: int, rejected_hours: int) -> List[Tuple[int, str]]:
    """Get old posts for cleanup based on age and status"""
    now = int(time.time())
    stale_ts = now - int(on_moderation_days) * 86400
    rejected_ts = now - int(rejected_hours) * 3600
    # ... query implementation
```

## Click Tracker API

### Redirect Endpoint

**Route**: `GET /r/<int:aid>`

**Usage**: `app/tracker.py:redirect_affiliate()`

```python
@app.route("/r/<int:aid>")
def redirect_affiliate(aid):
    """Redirect affiliate link and log click"""
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT target_url FROM affiliates WHERE id=?", (aid,)).fetchone()
    if not row:
        conn.close()
        return abort(404)
    target = row["target_url"]
    cur.execute("INSERT INTO clicks (affiliate_id, post_id, ts, ip, ua) VALUES (?,?,?,?,?)",
                (aid, None, int(time.time()), client_ip(), request.headers.get("User-Agent")))
    conn.commit()
    conn.close()
    return redirect(target)
```

**Parameters**:
- `aid`: Affiliate ID from database

**Response**:
- `302 Redirect`: To target URL
- `404 Not Found`: If affiliate ID doesn't exist

**Side Effects**:
- Logs click with IP, User-Agent, and timestamp
- Updates database with click statistics

## Moderation Bot Commands

### Start Command
```
/start
```
**Description**: Authentication check and bot initialization
**Access**: Moderator only (MODERATOR_CHAT_ID)

### Moderate Command
```
/moderate
```
**Description**: Show next post awaiting moderation
**Access**: Moderator only
**Response**: Post content with interactive buttons

### Rejected Command
```
/rejected
```
**Description**: List recent rejected posts
**Access**: Moderator only
**Response**: List of rejected post IDs and content previews

### Stats Command
```
/stats
```
**Description**: Show moderation statistics
**Access**: Moderator only
**Response**: Count of posts by status (on_moderation, rejected, published)

## Interactive Callbacks

### Approve Post
```
approve_{post_id}
```
**Description**: Approve post for publishing
**Effect**: Updates post status to "approved"

### Reject Post
```
reject_{post_id}
```
**Description**: Reject post
**Effect**: Updates post status to "rejected"

### Improve with AI
```
improve_{post_id}
```
**Description**: Use AI to improve post text
**Effect**: Calls OpenAI API and updates post text

### Random Image
```
randimg_{post_id}
```
**Description**: Assign random image from bank
**Effect**: Updates post image_path with random image

### Set Category
```
setcat_{post_id}
```
**Description**: Show category selection menu
**Effect**: Displays available categories

### Set Category Action
```
setcat_do_{post_id}_{category}
```
**Description**: Set specific category for post
**Effect**: Updates post category field

## Error Handling

### OpenAI API Errors
- **Retry Logic**: 3 attempts with exponential backoff
- **Timeout**: 30 seconds per request
- **Fallback**: Returns empty string on failure

### Telegram API Errors
- **HTTP Errors**: Raises exception on non-2xx status
- **Timeout**: 30-60 seconds depending on operation
- **File Upload**: Handles binary file reading

### Database Errors
- **Connection**: Graceful handling with proper cleanup
- **Transactions**: Automatic rollback on exceptions
- **Schema**: Idempotent table creation

## Rate Limiting

### OpenAI API
- **Chat Completions**: Varies by model and tier
- **Embeddings**: 3000 requests/minute (text-embedding-3-small)
- **Implementation**: Built-in retry with delays

### Telegram Bot API
- **General**: 30 messages/second per bot
- **File Upload**: 20 files/minute
- **Implementation**: No built-in rate limiting (relies on API limits)

### Internal Rate Limiting
- **Generation**: 1-second delay between posts
- **Queue Management**: Configurable maximum drafts (default: 10)
- **Scheduler**: Configurable intervals (default: 60 minutes)