"""Quiz Generation Service + Pipeline: topic → quiz prompt → LLM → PDF."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import httpx
import json
from typing import List, Dict
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

app = FastAPI(title="Quiz Service")

PROMPT_BUILDER_URL = os.getenv("PROMPT_BUILDER_URL", "http://prompt-builder:8002")
LLM_CLIENT_URL = os.getenv("LLM_CLIENT_URL", "http://llm-client:8003")

class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 5
    difficulty: str = "medium"

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct: str  # 'A', 'B', etc.

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/generate_quiz")
async def generate_quiz(request: QuizRequest):
    async with httpx.AsyncClient(timeout=180) as client:
        # 1. Build quiz prompt
        try:
            prompt_resp = await client.post(
                f"{PROMPT_BUILDER_URL}/build_quiz_prompt",
                json={"topic": request.topic, "num_questions": request.num_questions, "difficulty": request.difficulty}
            )
            if prompt_resp.status_code != 200:
                raise HTTPException(500, "Prompt builder failed")
            quiz_prompt = prompt_resp.json()["quiz_prompt"]
        except Exception as e:
            raise HTTPException(500, f"Prompt error: {str(e)}")

        # 2. Generate with LLM
        try:
            llm_resp = await client.post(
                f"{LLM_CLIENT_URL}/generate",
                json={"prompt": quiz_prompt}
            )
            if llm_resp.status_code != 200:
                raise HTTPException(500, "LLM failed")
            llm_output = llm_resp.json()["response"]
        except Exception as e:
            raise HTTPException(500, f"LLM error: {str(e)}")

        # 3. Parse JSON
        try:
            questions: List[QuizQuestion] = [QuizQuestion(**q) for q in json.loads(llm_output)]
        except Exception as e:
            raise HTTPException(500, f"Parse error: {llm_output[:500]}... Error: {str(e)}")

        if len(questions) != request.num_questions:
            raise HTTPException(500, f"Expected {request.num_questions} questions, got {len(questions)}")

        # 4. Format text for PDF
        content = []
        for i, q in enumerate(questions, 1):
            content.append(f"q{i} {q.question}")
            for opt in q.options:
                content.append(opt)
            content.append("")  # spacer

        content.append("Answer Key:")
        for i, q in enumerate(questions, 1):
            content.append(f"q{i}: {q.correct}")

        # 5. Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=30)
        story.append(Paragraph(f"Quiz: {request.topic} ({request.difficulty})", title_style))
        story.append(Spacer(1, 12))

        for line in content:
            if line.startswith('q') or line.startswith('Answer Key:'):
                p = Paragraph(line, styles['Heading2'])
            else:
                p = Paragraph(line, styles['Normal'])
            story.append(p)
            story.append(Spacer(1, 6))

        doc.build(story)
        buffer.seek(0)

        return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=quiz_{request.topic.replace(' ', '_')}.pdf"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
