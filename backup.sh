#!/bin/bash
DATE=$(date +%F)
sqlite3 data/posts.db ".backup 'backups/posts_$DATE.db'"
tar -czf backups/posts_$DATE.tar.gz backups/posts_$DATE.db
rclone copy backups/posts_$DATE.tar.gz remote:tg_backups/
