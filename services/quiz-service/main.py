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
    context: str = ""

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct: str  # 'A', 'B', etc.

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/generate_quiz")
async def generate_quiz(request: QuizRequest):
    print(f"INFO: Quiz request: topic='{request.topic}', nq={request.num_questions}, diff='{request.difficulty}'")
    async with httpx.AsyncClient(timeout=180) as client:
        # 1. Build quiz prompt
        print("INFO: Calling prompt-builder...")
        try:
            prompt_resp = await client.post(
                f"{PROMPT_BUILDER_URL}/build_quiz_prompt",
                json={"topic": request.topic, "num_questions": request.num_questions, "difficulty": request.difficulty}
            )
            print(f"INFO: Prompt-builder status: {prompt_resp.status_code}")
            print(f"INFO: Prompt-builder response preview: {prompt_resp.text[:200]}...")
            if prompt_resp.status_code != 200:
                print(f"ERROR: Prompt-builder failed body: {prompt_resp.text}")
                raise HTTPException(500, "Prompt builder failed")
            quiz_data = prompt_resp.json()
            quiz_prompt = quiz_data["quiz_prompt"]
            print(f"INFO: Quiz prompt length: {len(quiz_prompt)} chars")
            print(f"INFO: Prompt-builder OK")
        except Exception as e:
            print(f"ERROR: Prompt-builder exception: {str(e)}")
            raise HTTPException(500, f"Prompt error: {str(e)}")

        # 2. Generate with LLM
        print("INFO: Calling LLM...")

        # 2. Generate with LLM
        print("INFO: Calling LLM...")
        try:
            llm_resp = await client.post(
                f"{LLM_CLIENT_URL}/generate",
                json={"prompt": quiz_prompt}
            )
            print(f"INFO: LLM status: {llm_resp.status_code}")
            print(f"INFO: LLM response preview: {llm_resp.text[:200]}...")
            if llm_resp.status_code != 200:
                print(f"ERROR: LLM failed: {llm_resp.text}")
                raise HTTPException(500, "LLM failed")
            llm_data = llm_resp.json()
            llm_output = llm_data["response"]
            print(f"INFO: LLM output length: {len(llm_output)} chars")
        except Exception as e:
            raise HTTPException(500, f"LLM error: {str(e)}")

        # 3. Parse JSON
        print("INFO: Parsing LLM output as JSON...")
        print(f"LLM output preview: {llm_output[:300]}...")
        try:
            parsed = json.loads(llm_output)
            print(f"INFO: Parsed JSON type: {type(parsed)}, len: {len(parsed) if isinstance(parsed, list) else 'N/A'}")
            questions: List[QuizQuestion] = [QuizQuestion(**q) for q in parsed]
        except Exception as e:
            print(f"ERROR: JSON parse failed: {str(e)}")
            print(f"Raw LLM output: {llm_output[:1000]}")
            raise HTTPException(500, f"Parse error (check logs): {str(e)}")

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
