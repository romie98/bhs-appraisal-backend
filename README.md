# Mark Book & Register Backend API

FastAPI backend for managing students, attendance register, and assessments.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the `backend` directory:
   ```
   DATABASE_URL=sqlite:///./markbook.db
   SECRET_KEY=your-secret-key-here
   OPENAI_API_KEY=your-openai-api-key-here
   ```
   
   **Important:** For AI features (evidence extraction, portfolio building, appraisal reports), you need to set `OPENAI_API_KEY`:
   - Get your API key from: https://platform.openai.com/api-keys
   - Add it to your `.env` file: `OPENAI_API_KEY=sk-...`
   - Without this key, AI endpoints will return 500 errors

3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

   Or create initial migration:
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

4. **Run the server:**
   
   **Windows PowerShell:**
   ```powershell
   cd backend
   $env:PYTHONPATH = $PWD
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   **Or use the provided script:**
   ```powershell
   .\start_server.ps1
   ```
   
   **Linux/Mac:**
   ```bash
   cd backend
   export PYTHONPATH=$PWD
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Students
- `GET /students` - Get all students (optional `grade` filter)
- `GET /students/{id}` - Get student by ID
- `POST /students` - Create new student
- `PUT /students/{id}` - Update student
- `DELETE /students/{id}` - Delete student

### Register
- `GET /register` - Get register records (optional `grade`, `date`, `student_id` filters)
- `POST /register` - Create register record
- `POST /register/bulk` - Create bulk register records for a class
- `PUT /register/{id}` - Update register record
- `GET /register/summary/weekly?grade=10-9` - Get weekly attendance summary
- `GET /register/summary/monthly?grade=10-9` - Get monthly attendance summary

### Assessments
- `POST /assessments` - Create assessment
- `GET /assessments` - Get all assessments (optional `grade` filter)
- `GET /assessments/{id}` - Get assessment by ID
- `PUT /assessments/{id}` - Update assessment
- `DELETE /assessments/{id}` - Delete assessment

### Assessment Scores
- `POST /assessments/scores/bulk` - Add scores for entire class
- `GET /assessments/scores/by-assessment/{assessment_id}` - Get scores by assessment
- `GET /assessments/scores/by-student/{student_id}` - Get scores by student
- `PUT /assessments/scores/{id}` - Update score
- `DELETE /assessments/scores/{id}` - Delete score

## Database Models

### Student
- `id` (UUID)
- `first_name` (String)
- `last_name` (String)
- `grade` (String, e.g., "10-9")
- `gender` (String, optional)
- `parent_contact` (String, optional)

### RegisterRecord
- `id` (UUID)
- `student_id` (UUID, FK to Student)
- `date` (Date)
- `status` (Enum: Present, Absent, Late, Excused)
- `comment` (Text, optional)

### Assessment
- `id` (UUID)
- `title` (String)
- `type` (Enum: Quiz, Homework, Project, Test, Exam)
- `total_marks` (Integer)
- `date_assigned` (Date)
- `date_due` (Date, optional)
- `grade` (String)

### AssessmentScore
- `id` (UUID)
- `assessment_id` (UUID, FK to Assessment)
- `student_id` (UUID, FK to Student)
- `score` (Float)
- `comment` (Text, optional)

