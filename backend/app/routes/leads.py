"""
Lead management routes.
"""

from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.schemas.schemas import JobCreate, JobResponse, LeadResponse
from app.models.models import Job, Lead, User
from app.database import get_db

router = APIRouter()


@router.post("/generate", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_leads(
    job_in: JobCreate,
    db: Session = Depends(get_db)
):
    """Queue a new lead generation job."""
    # TODO: dispatch Celery task with the new Job ID
    
    # Normally we would retrieve the user from an auth dependency mechanism
    # Here we are defaulting it to user ID 1 or creating a dummy one for the sake of completeness.
    # In a real scenario, remove this block and inject current_user.
    user_stmt = select(User).where(User.id == 1)
    user = db.execute(user_stmt).scalars().first()
    if not user:
        user = User(email="dummy@example.com", hashed_password="hashed_password", full_name="Dummy User")
        db.add(user)
        db.commit()
        db.refresh(user)

    new_job = Job(
        user_id=user.id,
        intent=job_in.intent,
        lead_count=job_in.lead_count,
        status="pending"
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Poll the status of a lead-generation job."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    return job


@router.get("/jobs/{job_id}/results", response_model=List[LeadResponse])
async def get_job_results(job_id: int, db: Session = Depends(get_db)):
    """Retrieve the scraped leads for a completed job."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    stmt = select(Lead).where(Lead.job_id == job_id)
    leads = db.execute(stmt).scalars().all()
    
    return leads
