import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models.models import Job, User, Lead
from app.config import settings
from main import app

# For testing, we append `_test` to the database name so we don't accidentally
# drop all production tables when running `pytest`.
original_db = settings.DATABASE_URL.split("/")[-1]
TEST_SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace(original_db, f"{original_db}_test")
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
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
    Setup the isolated test database.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Populate dummy data
    db = TestingSessionLocal()
    
    # Create variables to share IDs back to the test suite
    test_state = {}
    
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
        
        test_state["job_id"] = dummy_job.id
    finally:
        db.close()
        
    yield test_state
    
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
    assert data["progress"] == 0
    assert "id" in data


def test_get_job_status_existing(setup_database):
    # Fetch the previously populated dummy completed job
    job_id = setup_database["job_id"]
    response = client.get(f"/api/leads/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["intent"] == "sales"
    assert data["status"] == "completed"


def test_get_job_not_found(setup_database):
    response = client.get("/api/leads/jobs/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_get_job_results_populated(setup_database):
    # Fetch results for the pre-populated sales job
    job_id = setup_database["job_id"]
    response = client.get(f"/api/leads/jobs/{job_id}/results")
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


def test_export_job_results_csv(setup_database):
    job_id = setup_database["job_id"]
    response = client.get(f"/api/leads/jobs/{job_id}/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=" in response.headers["content-disposition"]
    
    # Check CSV header
    csv_content = response.text
    assert "ID,Name,Email,Company,Title,Source URL,Confidence%" in csv_content
    assert "Alice CEO,alice@test.com" in csv_content
