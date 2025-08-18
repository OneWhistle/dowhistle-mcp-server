# MCP Server Documentation

## Project Structure

```
mcp-server/
├── config/
│   └── settings.py              # Configuration management
├── utils/
│   └── http_client.py          # HTTP client with retry logic
├── agents/
│   ├── __init__.py
│   ├── search.py               # Search functionality
│   ├── auth.py                 # Authentication tools
│   ├── whistle.py              # Whistle management
│   └── user.py                 # User settings management
├── tests/
│   ├── __init__.py
│   ├── test_agents.py          # Agent tests
│   └── conftest.py             # Test configuration
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Multi-container setup
├── .env.example               # Environment variables template
└── README.md                  # Documentation
```

## Agents and Tools

### 1. Search Agent (`agents/search.py`)
- **Tool**: `search`
- **Purpose**: Search functionality through Express API

### 2. Authentication Agent (`agents/auth.py`)
- **Tools**: 
  - `sign_in`: User authentication
  - `verify_otp`: OTP verification
  - `resend_otp`: Resend OTP code
- **Purpose**: Handle all authentication flows

### 3. Whistle Agent (`agents/whistle.py`)
- **Tools**:
  - `create_whistle`: Create new whistle reports
  - `update_whistle`: Update existing whistles
  - `delete_whistle`: Delete whistles
  - `list_whistles`: List whistles with pagination
- **Purpose**: Complete whistle management

### 4. User Agent (`agents/user.py`)
- **Tools**:
  - `toggle_live_tracking`: Enable/disable live tracking
  - `toggle_visibility`: Control user visibility
  - `toggle_whistle_sound`: Control sound notifications
- **Purpose**: User preference management

## Installation and Setup

### Prerequisites
- Python 3.11+
- Access to your Express.js API
- Docker (optional)

### Local Development

1. **Clone and setup**:
```bash
git clone https://github.com/OneWhistle/dowhistle-mcp-server
cd dowhistle-mcp-server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configuration**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Run the server**:
```bash
python main.py
```

### Docker Deployment

1. **Build and run**:
```bash
docker-compose up --build
```

2. **Production deployment**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Configuration

All configuration is managed through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `EXPRESS_API_BASE_URL` | Your Express API base URL | `https://dowhistle.herokuapp.com/v3` |
| `MCP_SERVER_PORT` | MCP server port | `8000` |
| `HEALTH_PORT` | Health server port | `8080` |
| `API_KEY` | API authentication key | `None` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_RETRIES` | API request retry count | `3` |
| `RETRY_DELAY` | Retry delay in seconds | `1.0` |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per minute | `60` |
