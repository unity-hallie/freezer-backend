# Freezer App Backend

FastAPI backend for the household freezer tracking application.

## Features

- User authentication (JWT)
- Household management
- Storage locations (freezer, fridge, pantry)
- Item tracking with expiration dates
- RESTful API endpoints

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

FastAPI provides interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests with:
```bash
pytest
```

## Database Models

- **User**: Authentication and user info
- **Household**: Shared storage spaces
- **Location**: Storage locations within households (freezer, fridge, pantry)
- **Item**: Food items tracked in locations