from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db, Question, init_db
from app.services.embedding import get_embedding
from app.api.contributions import router as contributions_router

app = FastAPI(title="Bot X API", version="1.0.0")

# Include routers
app.include_router(contributions_router)


class QuestionAnswerPair(BaseModel):
    """Request model for question-answer pairs."""
    q: str
    a: str


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.post("/qa")
async def add_question_answer(
    qa: QuestionAnswerPair,
    db: Session = Depends(get_db)
):
    """
    Add a new question-answer pair with its embedding to the database.

    Args:
        qa: Question and answer pair
        db: Database session

    Returns:
        Success message with created record ID
    """
    try:
        # Generate embedding for the question
        embedding = get_embedding(qa.q)

        # Create new question record
        question = Question(
            question=qa.q,
            answer=qa.a,
            embedding=embedding
        )

        db.add(question)
        db.commit()
        db.refresh(question)

        return {
            "message": "Question-answer pair added successfully",
            "id": question.id,
            "question": question.question
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding question-answer pair: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
