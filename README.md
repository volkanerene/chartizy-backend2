# Graphzy Backend API

FastAPI backend for the Graphzy AI-powered chart generator.

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create .env file)
cp .env.example .env
# Edit .env with your credentials

# Run the server
python run.py
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

Create a `.env` file with:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_jwt_secret
CORS_ORIGINS=http://localhost:3000,http://localhost:8081
```

## Project Structure

```
app/
├── routers/        # API endpoints
│   ├── auth.py     # Authentication
│   ├── charts.py   # Chart generation
│   ├── templates.py # Template CRUD
│   └── subscription.py
├── schemas/        # Pydantic models
├── services/       # Business logic
│   ├── openai_service.py
│   └── supabase_service.py
├── middleware/     # JWT auth
├── config.py       # Settings
└── main.py         # App entry
```

