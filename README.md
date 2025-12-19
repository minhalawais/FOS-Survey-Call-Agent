# FOS AI Survey Agent

> AI-powered Urdu voice survey agent for FOS HRDD Worker Hotline

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# The database initializes automatically on first run
# Or manually:
python -c "from backend.app.database import init_db; init_db()"
```

### 3. Run CLI Test

```bash
python cli/test_agent.py
```

### 4. Run API Server

```bash
cd backend
python -m uvicorn main:app --reload
```

Then open: http://localhost:8000/docs

## Project Structure

```
fos-survey-agent/
├── ai/                     # AI services
│   ├── stt/               # Whisper STT
│   └── tts/               # Piper TTS
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── agent/        # Survey agent logic
│   │   ├── api/          # REST endpoints
│   │   └── services/     # External service clients
│   └── main.py
├── cli/                   # CLI tools
├── dummy_data/            # Sample data (JSON)
└── docker-compose.yml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/surveys` | List all surveys |
| GET | `/api/v1/employees` | List all employees |
| POST | `/api/v1/agent/start` | Start survey session |
| POST | `/api/v1/agent/respond` | Send text response |
| GET | `/api/v1/agent/session/{id}` | Get session status |

## Testing

```bash
# CLI test
python cli/test_agent.py

# API test
curl http://localhost:8000/api/v1/surveys
```

## License

Proprietary - Fruit of Sustainability
