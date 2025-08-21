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
├── app.py                      # Entry point
├── pyproject.toml              # Dependencies
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Multi-container setup
├── .env.example                # Environment variables template
└── README.md                   # Documentation
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

uv sync

source .venv/bin/activate  # On Windows: .venv\Scripts\activate

```

1. **Configuration**:
```bash
cp env.example .env
# Edit .env with your settings
```

1. **Run the server**:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 
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
| `PORT` | MCP server port | `8000` |
| `HEALTH_PORT` | Health server port | `8080` |
| `API_KEY` | API authentication key | `None` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_RETRIES` | API request retry count | `3` |
| `RETRY_DELAY` | Retry delay in seconds | `1.0` |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per minute | `60` |

---

## MCP Client 

1. **New ENV setup**:
```bash

python -m venv mcp-venv
source mcp-venv/bin/activate  # On Windows: mcp-venv\Scripts\activate
pip install -r requirements-mcp-client.txt
```

2. **Run the MCP Client**
```bash
python mcp_client.py interactive 
```

3. **Sample NLP Sentences**

     1. Search Tool

            

        ## 🍔 Burger Queries

        **1.**

        ```text
        Looking for burger restaurants near latitude 10.997170885242573 and longitude 76.96196491003371.
        ```

        **2.**

        ```text
        Find burger spots within 30 km of the coordinates (10.997170885242573, 76.96196491003371), limited to 30 results.
        ```

        **3.**

        ```text
        Show me up to 30 burger joints around latitude 10.997170885242573 and longitude 76.96196491003371.
        ```

        **4.**

        ```text
        Searching for nearby burger places close to 10.997170885242573, 76.96196491003371.
        ```

        **5.**

        ```text
        Retrieve burger restaurants near the location (10.997170885242573, 76.96196491003371) within a 30 km radius.
        ```

        ---

        ## 🔧 Plumber Queries

        **6.**

        ```text
        Looking for plumber services near latitude 10.997170885242573 and longitude 76.96196491003371.
        ```

        **7.**

        ```text
        Find up to 30 plumbers around the coordinates (10.997170885242573, 76.96196491003371), within 30 km.
        ```

        **8.**

        ```text
        Show me plumbers available near the point (10.997170885242573, 76.96196491003371).
        ```

        **9.**

        ```text
        Retrieve plumber listings close to latitude 10.997170885242573 and longitude 76.96196491003371, restricted to 30 results.
        ```

        **10.**

        ```text
        Searching for nearby plumbers within 30 kilometers of 10.997170885242573, 76.96196491003371.
        ```

        ---

        ## ☕ Coffee Queries

        **11.**

        ```text
        Looking for coffee shops near latitude 10.997170885242573 and longitude 76.96196491003371.
        ```

        **12.**

        ```text
        Find coffee places within 30 km of the location (10.997170885242573, 76.96196491003371), limited to 30 results.
        ```

        **13.**

        ```text
        Show me coffee shops around latitude 10.997170885242573 and longitude 76.96196491003371.
        ```

        **14.**

        ```text
        Searching for nearby coffee spots close to 10.997170885242573, 76.96196491003371, with a maximum of 30 results.
        ```

        **15.**

        ```text
        Retrieve coffee locations near the coordinates (10.997170885242573, 76.96196491003371), restricted to 30 km radius.
        ```

        ---




        In auth_flow Add one more options along with ask the value one by one, this need to be secoundary, primary user enter the in NLP we need to undersant and extract the args and call the approipate tool with that args

        For example
        My number is +91 9994076214 and my name is Paramaswari and locations is latitude 10.997170885242573 and longitude 76.96196491003371. [Call SignIn Tool]

        verify my OTP 164318 for this user_id xxxx  [Call Verify Tool]

        Resend OTP for this user_id xxxx [Call Resend OTP Tool]







