import io
import csv
from typing import List

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.schemas.schemas import JobCreate, JobResponse, LeadResponse
from app.models.models import Job, Lead, User
from app.database import get_db
from app.tasks.generate_leads import generate_leads_task

router = APIRouter()


@router.post("/generate", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_leads(
    job_in: JobCreate,
    db: Session = Depends(get_db)
):
    """Queue a new lead generation job."""
    # Normally we would retrieve the user from an auth dependency mechanism.
    # For now, we assume a preconfigured user with ID 1 exists.
    # In a real scenario, remove this block and inject current_user.
    user_stmt = select(User).where(User.id == 1)
    user = db.execute(user_stmt).scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authenticated user available; configure authentication or user ID 1.",
        )

    new_job = Job(
        user_id=user.id,
        intent=job_in.intent,
        lead_count=job_in.lead_count,
        status="pending"
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # Process scraping jobs asynchronously via Celery
    generate_leads_task.delay(new_job.id)

    return new_job


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Poll the status of a lead-generation job."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    return job


@router.get("/jobs/{job_id}/results", response_model=List[LeadResponse])
async def get_job_results(job_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve the scraped leads for a completed job."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
    if job.status != "completed":
        return []
        
    stmt = select(Lead).where(Lead.job_id == job_id).offset(skip).limit(limit)
    leads = db.execute(stmt).scalars().all()
    
    return leads


@router.get("/jobs/{job_id}/export")
async def export_job_results(job_id: int, db: Session = Depends(get_db)):
    """
    Stream the scraped leads for a completed job as a CSV file to the client directly
    from PostgreSQL (bypassing the need for S3 cloud storage).
    """
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    # Optionally fail if not completed
    # if job.status != "completed":
    #    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not completed yet.")

    def iter_csv():
        # Using a generator avoids loading all records into memory at once
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["ID", "Name", "Email", "Company", "Title", "Source URL", "Confidence%"])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # Iterate over results chunks locally
        chunk_size = 500
        offset = 0
        while True:
            stmt = select(Lead).where(Lead.job_id == job_id).offset(offset).limit(chunk_size)
            chunk = db.execute(stmt).scalars().all()
            if not chunk:
                break
                
            for lead in chunk:
                writer.writerow([
                    lead.id,
                    lead.name or "",
                    lead.email or "",
                    lead.company or "",
                    lead.title or "",
                    lead.source_url or "",
                    round((lead.confidence or 0.0) * 100, 2)
                ])
                
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            offset += chunk_size
            
    response = StreamingResponse(iter_csv(), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=leads_job_{job_id}.csv"
    return response
