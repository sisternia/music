# Run Project

## Requirements

- Python 3.10+

## Install Dependencies

### Using Virtual Environment

Create virtual environment:

```bash
python -m venv .venv
```

Activate virtual environment:

**Windows**

```bash
.venv\Scripts\activate
```

**macOS/Linux**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run project:

```bash
python main.py
```

Access API:

```text
http://127.0.0.1:8000
```

Access Swagger UI:

```text
http://127.0.0.1:8000/swagger
```

Access OpenAPI Schema:

```text
http://127.0.0.1:8000/openapi.json
```

Access ReDoc:

```text
http://127.0.0.1:8000/redoc
```

Deactivate virtual environment:

```bash
deactivate
```

---

### Without Virtual Environment

Install dependencies:

```bash
pip install -r requirements.txt
```

Run project:

```bash
python main.py
```

Access API:

```text
http://127.0.0.1:8000
```

Access Swagger UI:

```text
http://127.0.0.1:8000/swagger
```

Access OpenAPI Schema:

```text
http://127.0.0.1:8000/openapi.json
```

Access ReDoc:

```text
http://127.0.0.1:8000/redoc
```

---

## Environment Variables

Create `.env` from `.env.example` and update the required values before running the project.
