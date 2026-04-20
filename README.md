# SkillBridge API

## 1. Live API Base URL

https://skillbridge-api-ya76.onrender.com

## 2. Local Setup Instructions

1. **Clone the repository and open it**
   ```bash
   git clone https://github.com/JayanthC6/SkillBridge-API
   cd skillbridge-api
   ```

2. **Create a virtual environment**
   - Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Create a `.env` file in the project root.
   - Add your Neon/Postgres connection string and keys:
     ```env
     DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>
     SECRET_KEY=<your-secret-key>
     MONITORING_API_KEY=<your-monitoring-api-key>
     ```

5. **Create database tables**
   ```bash
   python init_db.py
   ```

6. **Start the API server with Uvicorn**
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Verify service health**
   - Open [http://localhost:8000](http://localhost:8000)
   - Expected response:
     ```json
     {"status":"ok"}
     ```

## 3. Test Accounts

Paste seeded accounts here after running the seed script.

| Role | Email | Password |
|---|---|---|
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |

## 4. Sample cURL Commands

### POST `/auth/signup`

```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Student One",
    "email": "student.one@example.com",
    "password": "password123",
    "role": "student"
  }'
```

### POST `/auth/login`

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student.one@example.com",
    "password": "password123"
  }'
```

### POST `/auth/monitoring-token`

```bash
curl -X POST "http://localhost:8000/auth/monitoring-token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <MONITORING_OFFICER_STANDARD_JWT>" \
  -d '{
    "key": "<MONITORING_API_KEY>"
  }'
```

### GET `/monitoring/attendance` (with scoped token)

```bash
curl -X GET "http://localhost:8000/monitoring/attendance" \
  -H "Authorization: Bearer <MONITORING_SCOPED_JWT>"
```

## 5. Schema Decisions

- **Many-to-many trainers and batches (`batch_trainers`)**  
  A trainer can support multiple batches, and each batch can have multiple trainers. This is modeled using the `batch_trainers` join table with a composite primary key (`batch_id`, `trainer_id`), which prevents duplicate trainer assignments.

- **Single-use invite flow (`batch_invites`)**  
  Batch onboarding uses tokenized invites. Each invite stores `token`, `expires_at`, and `used`. On join, the API validates token existence, expiration, and usage state. If valid, the student is enrolled and `used` is set to `True` to enforce one-time consumption.

- **Dual-token model for Monitoring Officer**  
  Monitoring starts with a normal auth JWT (24h) from login/signup. The officer must then call `/auth/monitoring-token` with `MONITORING_API_KEY` to obtain a scoped JWT (1h, `scope=monitoring_only`) for monitoring endpoints. This narrows privilege and limits exposure.

## 6. Known Security Issue

The current JWT approach is stateless. Once issued, tokens remain valid until expiry (24 hours for standard access tokens), even if a user logs out or an account must be immediately revoked.

With more time, I would add a Redis-backed token blocklist (denylist) keyed by JWT `jti` and expiry time. Logout and forced revocation would push tokens to Redis, and auth middleware would reject blocked tokens on every request.

## 7. Assignment Status

- Task 1: Fully complete and tested
- Task 2: Fully complete and tested
- Task 3: Fully complete and tested
- Task 5: Fully complete and tested
