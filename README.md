# TTB Label Verifier

A FastAPI prototype for verifying alcohol label compliance against submitted application data.

## Local setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000` in a browser. The verification and Claude integration modules are scaffolded for implementation.

## Render deployment

Use Render's native Python runtime with:

```text
Build command: pip install -r requirements.txt
Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set `ANTHROPIC_API_KEY` as a Render environment variable; do not commit `.env` or secrets.
