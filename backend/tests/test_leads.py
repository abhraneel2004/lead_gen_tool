import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models.models import Job, User, Lead
from app.config import settings
from main import app

# We use the actual Postgres database for testing, but ideally this would point to a separate
# logical database (e.g. `mydb_test`), but for the simplicity of the test container, we'll
# use the same one, but keep the transactions isolated and clean up.
# Production grade code often uses a secondary test DB in CI/CD.
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """
    Setup the database for tests. We drop and recreate tables to ensure a clean slate.
    Warning: Since this uses the main DB url, it clears data! In a real system you would 
    use a different database name for tests in your pytest.ini or conftest.py.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Populate dummy data
    db = TestingSessionLocal()
    try:
        dummy_user = User(email="dummy_test@example.com", hashed_password="hashed_password", full_name="Test User")
        db.add(dummy_user)
        db.commit()
        db.refresh(dummy_user)
        
        dummy_job = Job(user_id=dummy_user.id, intent="sales", lead_count=50, status="completed")
        db.add(dummy_job)
        db.commit()
        db.refresh(dummy_job)
        
        dummy_lead1 = Lead(job_id=dummy_job.id, name="Alice CEO", email="alice@test.com", confidence=0.95)
        dummy_lead2 = Lead(job_id=dummy_job.id, name="Bob CTO", email="bob@test.com", confidence=0.88)
        db.add_all([dummy_lead1, dummy_lead2])
        db.commit()
    finally:
        db.close()
        
    yield
    
    # Teardown
    Base.metadata.drop_all(bind=engine)


def test_generate_leads(setup_database):
    response = client.post(
        "/api/leads/generate",
        json={"intent": "career", "lead_count": 50},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["intent"] == "career"
    assert data["lead_count"] == 50
    assert data["status"] == "pending"
    assert "id" in data


def test_get_job_status_existing(setup_database):
    # Fetch the previously populated dummy completed job
    response = client.get("/api/leads/jobs/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["intent"] == "sales"
    assert data["status"] == "completed"


def test_get_job_not_found(setup_database):
    response = client.get("/api/leads/jobs/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_get_job_results_populated(setup_database):
    # Fetch results for the pre-populated sales job (id 1)
    response = client.get("/api/leads/jobs/1/results")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    
    names = [lead["name"] for lead in data]
    assert "Alice CEO" in names
    assert "Bob CTO" in names

def test_get_job_results_empty(setup_database):
    # Create a new pending job 
    create_response = client.post(
        "/api/leads/generate",
        json={"intent": "growth", "lead_count": 5},
    )
    job_id = create_response.json()["id"]

    # Now fetch results (should be empty since no leads are generated for a pending job)
    response = client.get(f"/api/leads/jobs/{job_id}/results")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0
