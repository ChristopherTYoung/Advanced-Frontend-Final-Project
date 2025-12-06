# Discord Bot Services Architecture

```mermaid
graph TB
    subgraph "FastAPI Application"
        Main[main.py<br/>FastAPI Server]
        EventCtrl[event_controller.py<br/>Event API Routes]
        SettingsCtrl[guild_settings_controller.py<br/>Settings API Routes]
        OffenseCtrl[offense_controller.py<br/>Offense API Routes]
    end

    subgraph "Core Services"
        AuthSvc[auth_service.py<br/>- OAuth flow<br/>- Token exchange<br/>- User info fetch<br/>- Guild access]
        BotSvc[bot_service.py<br/>- Discord bot client<br/>- Message handling<br/>- Event listeners<br/>- LLM integration]
        MsgSvc[message_service.py<br/>- Store messages<br/>- Retrieve history<br/>- DM tracking]
        SettingsSvc[settings_service.py<br/>- Bot personality<br/>- Role permissions<br/>- Content maturity<br/>- Guild config]
        EventSvc[event_service.py<br/>- Create events<br/>- Event proposals<br/>- Approve/reject<br/>- Schedule checks]
        OffenseSvc[offense_service.py<br/>- Record violations<br/>- Track offensive content<br/>- Store evidence]
        LLMSvc[llm_service.py<br/>- Generate responses<br/>- Content moderation<br/>- Tool execution<br/>- Conversation context]
    end

    subgraph "Database"
        DB[(PostgreSQL<br/>- message<br/>- event<br/>- event_proposal<br/>- guild_bot_settings<br/>- offense)]
    end

    subgraph "External Services"
        Discord[Discord API<br/>- OAuth<br/>- User data<br/>- Guilds<br/>- Bot gateway]
        LLM[LLM Server<br/>Gemma3-27b]
    end

    %% Main Application Flow
    Main --> EventCtrl
    Main --> SettingsCtrl
    Main --> OffenseCtrl
    Main --> AuthSvc
    Main --> BotSvc
    Main --> MsgSvc
    Main --> SettingsSvc
    Main --> EventSvc

    %% Controller Dependencies
    EventCtrl --> AuthSvc
    EventCtrl --> EventSvc
    SettingsCtrl --> AuthSvc
    SettingsCtrl --> SettingsSvc
    SettingsCtrl --> BotSvc
    OffenseCtrl --> AuthSvc
    OffenseCtrl --> BotSvc

    %% Bot Service Dependencies
    BotSvc --> MsgSvc
    BotSvc --> SettingsSvc
    BotSvc --> OffenseSvc
    BotSvc --> LLMSvc
    BotSvc --> Discord

    %% Service to Database
    MsgSvc --> DB
    SettingsSvc --> DB
    EventSvc --> DB
    OffenseSvc --> DB

    %% External API Calls
    AuthSvc --> Discord
    LLMSvc --> LLM

    %% Styling
    classDef controller fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef external fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef database fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px

    class EventCtrl,SettingsCtrl,OffenseCtrl controller
    class AuthSvc,BotSvc,MsgSvc,SettingsSvc,EventSvc,OffenseSvc,LLMSvc service
    class Discord,LLM external
    class DB database
```

## Service Responsibilities

### Controllers (API Layer)
- **event_controller.py**: REST endpoints for event creation, proposals, approval/rejection
- **guild_settings_controller.py**: REST endpoints for guild configuration, roles, permissions, maturity preferences
- **offense_controller.py**: REST endpoints for retrieving content violations

### Core Services

#### auth_service.py
- Manages Discord OAuth2 authentication flow
- Exchanges authorization codes for access tokens
- Fetches user information and guild memberships
- Generates authorization URLs and handles redirects

#### bot_service.py
- Main Discord bot client using discord.py
- Registers and handles Discord events (messages, guild joins, etc.)
- Processes mentions and DMs with LLM integration
- Manages conversation history and context
- Moderates content using LLM service
- Executes bot commands (nickname changes, message sending)

#### message_service.py
- Persists all bot messages to database
- Retrieves conversation history
- Tracks DM conversations
- Filters messages by guild/channel/user

#### settings_service.py
- Stores and retrieves guild-specific bot settings
- Manages bot personality configurations
- Handles role-based permission systems
- Controls content maturity preferences

#### event_service.py
- Creates scheduled events
- Manages event proposals workflow
- Handles proposal approval/rejection
- Retrieves upcoming events
- Cancels events

#### offense_service.py
- Records content violations detected by LLM
- Stores offensive messages and attachments
- Tracks offensive scores and timestamps
- Provides violation history per guild

#### llm_service.py
- Generates AI responses using Gemma3-27b model
- Performs content moderation and scoring
- Manages tool registration and execution
- Builds system prompts with personality/context
- Handles conversation history for contextual responses

## Data Flow Examples

### 1. User Authentication
```
Client → Main → AuthSvc → Discord API → Main → Session Storage
```

### 2. Bot Receives Message
```
Discord → BotSvc → MsgSvc → DB
              ↓
         LLMSvc → LLM Server
              ↓
     Generate Response → Discord
```

### 3. Create Event
```
Client → EventCtrl → AuthSvc → Discord (verify)
              ↓
         EventSvc → DB
```

### 4. Content Moderation
```
Discord Message → BotSvc → SettingsSvc → DB (get maturity prefs)
                     ↓
                LLMSvc → LLM Server (analyze)
                     ↓
              OffenseSvc → DB (if offensive)
                     ↓
              Delete Message (if score too high)
```
