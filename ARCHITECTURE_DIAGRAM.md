# System Architecture Diagrams

## High-Level System Overview

```mermaid
graph TB
    subgraph "External Services"
        RSS[RSS Feeds<br/>Reuters, Investing.com]
        OpenAI[OpenAI API<br/>GPT-4, Embeddings]
        TG[Telegram API<br/>Bot & Channel]
    end
    
    subgraph "Core System"
        RF[RSS Fetcher]
        GEN[Content Generator]
        MOD[Moderation Bot]
        PUB[Publisher Bot]
        SCH[Scheduler]
        DB[(SQLite Database)]
        TRK[Click Tracker]
    end
    
    subgraph "Storage"
        IMG[Image Bank]
        FILES[Generated Images]
        BACKUP[Backup Storage]
    end
    
    RSS --> RF
    RF --> GEN
    GEN --> DB
    DB --> MOD
    MOD --> DB
    DB --> PUB
    PUB --> TG
    SCH --> RF
    SCH --> DB
    GEN --> IMG
    GEN --> FILES
    DB --> BACKUP
    TRK --> DB
    GEN --> OpenAI
    MOD --> TG
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant RSS as RSS Feeds
    participant RF as RSS Fetcher
    participant GEN as Generator
    participant DB as Database
    participant MOD as Moderation Bot
    participant PUB as Publisher
    participant TG as Telegram

    Note over RSS,TG: Content Generation Flow
    
    RSS->>RF: Fetch news items
    RF->>GEN: Process RSS items
    GEN->>OpenAI: Generate content
    OpenAI-->>GEN: Return generated text
    GEN->>DB: Store post (on_moderation)
    
    Note over RSS,TG: Moderation Flow
    
    MOD->>DB: Fetch next post
    DB-->>MOD: Return post data
    MOD->>TG: Send to moderator
    TG-->>MOD: User action (approve/reject)
    MOD->>DB: Update post status
    
    Note over RSS,TG: Publishing Flow
    
    PUB->>DB: Get approved posts
    DB-->>PUB: Return approved post
    PUB->>TG: Publish to channel
    PUB->>DB: Update status (published)
```

## Database Schema

```mermaid
erDiagram
    POSTS {
        int id PK
        string source_title
        string source_url
        string raw_rss
        string text
        string image_path
        string status
        int channel_id
        string category
        string tags
        string embedding
        int created_at
        int updated_at
    }
    
    AFFILIATES {
        int id PK
        string target_url
        string notes
    }
    
    CLICKS {
        int id PK
        int affiliate_id FK
        int post_id FK
        int ts
        string ip
        string ua
    }
    
    POSTS ||--o{ CLICKS : "tracks"
    AFFILIATES ||--o{ CLICKS : "generates"
```

## Component Interaction Diagram

```mermaid
graph LR
    subgraph "Scheduler Process"
        SCH[Scheduler]
        RF[RSS Fetcher]
        GEN[Generator]
        CLN[Cleanup]
    end
    
    subgraph "Moderation Process"
        MOD[Moderator Bot]
        UI[Telegram UI]
        ACT[Actions]
    end
    
    subgraph "Publishing Process"
        PUB[Publisher]
        QUE[Queue Manager]
    end
    
    subgraph "Data Layer"
        DB[(SQLite)]
        IMG[Image Storage]
    end
    
    subgraph "External APIs"
        OPENAI[OpenAI API]
        TGAPI[Telegram API]
    end
    
    SCH --> RF
    SCH --> GEN
    SCH --> CLN
    RF --> GEN
    GEN --> OPENAI
    GEN --> DB
    GEN --> IMG
    
    MOD --> UI
    UI --> ACT
    ACT --> DB
    ACT --> OPENAI
    
    PUB --> QUE
    QUE --> DB
    PUB --> TGAPI
    
    CLN --> DB
    CLN --> IMG
```

## Service Architecture

```mermaid
graph TB
    subgraph "Systemd Services"
        SVC1[telegram_ai_scheduler.service]
        SVC2[telegram_ai_moderator.service]
        SVC3[telegram_ai_tracker.service]
    end
    
    subgraph "Python Modules"
        SCH[app.scheduler]
        MOD[app.moderator_bot]
        TRK[app.tracker]
        GEN[app.generator]
        RF[app.rss_fetcher]
        PUB[app.poster]
        DB[app.db]
        UTIL[app.utils]
        CFG[app.config]
    end
    
    subgraph "External Dependencies"
        OPENAI[OpenAI API]
        TG[Telegram API]
        RSS[RSS Feeds]
        RCLONE[rclone]
    end
    
    SVC1 --> SCH
    SVC2 --> MOD
    SVC3 --> TRK
    
    SCH --> RF
    SCH --> GEN
    SCH --> DB
    SCH --> UTIL
    
    MOD --> DB
    MOD --> UTIL
    MOD --> TG
    
    TRK --> DB
    
    GEN --> OPENAI
    GEN --> DB
    GEN --> UTIL
    
    RF --> RSS
    PUB --> TG
    PUB --> DB
    PUB --> UTIL
    
    UTIL --> OPENAI
    UTIL --> TG
    
    CFG --> SCH
    CFG --> MOD
    CFG --> TRK
    CFG --> GEN
    CFG --> RF
    CFG --> PUB
    CFG --> DB
    CFG --> UTIL
```

## State Machine - Post Lifecycle

```mermaid
stateDiagram-v2
    [*] --> on_moderation : Generated
    on_moderation --> approved : Moderator approves
    on_moderation --> rejected : Moderator rejects
    on_moderation --> on_moderation : AI improvement
    on_moderation --> on_moderation : Image change
    on_moderation --> on_moderation : Category change
    approved --> published : Publisher posts
    rejected --> [*] : Cleanup (24h)
    published --> [*] : Final state
```

## Error Handling Flow

```mermaid
graph TD
    START[Operation Start]
    TRY[Try Operation]
    SUCCESS{Success?}
    ERROR[Log Error]
    RETRY{Retry Count < 3?}
    WAIT[Wait & Retry]
    FAIL[Operation Failed]
    SUCCESS_END[Operation Complete]
    
    START --> TRY
    TRY --> SUCCESS
    SUCCESS -->|Yes| SUCCESS_END
    SUCCESS -->|No| ERROR
    ERROR --> RETRY
    RETRY -->|Yes| WAIT
    WAIT --> TRY
    RETRY -->|No| FAIL
```

## Security Architecture

```mermaid
graph TB
    subgraph "External Access"
        USER[Moderator User]
        CLICK[Click Tracker Users]
        API[External APIs]
    end
    
    subgraph "Authentication Layer"
        AUTH[User ID Check]
        TOKEN[Bot Token Auth]
        API_KEY[API Key Auth]
    end
    
    subgraph "Application Layer"
        MOD[Moderator Bot]
        TRK[Click Tracker]
        SYS[Core System]
    end
    
    subgraph "Data Layer"
        DB[(Database)]
        FILES[File System]
    end
    
    USER --> AUTH
    AUTH --> MOD
    CLICK --> TRK
    TRK --> DB
    MOD --> DB
    SYS --> API_KEY
    API_KEY --> API
    SYS --> FILES
    MOD --> FILES
```

## Monitoring and Logging

```mermaid
graph LR
    subgraph "Application Logs"
        LOG1[Scheduler Logs]
        LOG2[Moderator Logs]
        LOG3[Tracker Logs]
    end
    
    subgraph "System Logs"
        SYS[Systemd Journal]
        SVC[Service Status]
    end
    
    subgraph "Database Monitoring"
        DB[(Database)]
        QUERY[Query Logs]
        STATS[Statistics]
    end
    
    subgraph "External Monitoring"
        API[API Health]
        NET[Network Status]
    end
    
    LOG1 --> SYS
    LOG2 --> SYS
    LOG3 --> SYS
    SYS --> SVC
    DB --> QUERY
    DB --> STATS
    API --> NET
```

## Backup and Recovery

```mermaid
graph TB
    subgraph "Backup Sources"
        DB[(Database)]
        IMG[Images]
        CFG[Configuration]
    end
    
    subgraph "Backup Process"
        BACKUP[backup.sh]
        SQLITE[SQLite Backup]
        TAR[Archive Creation]
        RCLONE[rclone Upload]
    end
    
    subgraph "Storage"
        LOCAL[Local Storage]
        CLOUD[Cloud Storage]
    end
    
    subgraph "Recovery"
        RESTORE[Restore Process]
        VERIFY[Integrity Check]
    end
    
    DB --> SQLITE
    IMG --> TAR
    CFG --> TAR
    SQLITE --> BACKUP
    TAR --> BACKUP
    BACKUP --> LOCAL
    BACKUP --> RCLONE
    RCLONE --> CLOUD
    LOCAL --> RESTORE
    CLOUD --> RESTORE
    RESTORE --> VERIFY
```

## Performance Characteristics

```mermaid
graph TB
    subgraph "Bottlenecks"
        API[OpenAI API Rate Limits]
        DB[SQLite Concurrency]
        NET[Network Latency]
    end
    
    subgraph "Optimization Points"
        CACHE[Embedding Cache]
        BATCH[Batch Processing]
        ASYNC[Async Operations]
    end
    
    subgraph "Resource Usage"
        CPU[CPU Usage]
        MEM[Memory Usage]
        DISK[Disk I/O]
    end
    
    API --> CACHE
    DB --> BATCH
    NET --> ASYNC
    CACHE --> CPU
    BATCH --> MEM
    ASYNC --> DISK
```

This architecture documentation provides visual representations of the system's structure, data flow, and operational characteristics, making it easier to understand the system's design and identify areas for improvement.