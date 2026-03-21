"""Prompt Builder Service - builds prompts from context and question."""

from fastapi import FastAPI
import os

app = FastAPI(title="Prompt Builder Service")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/build")
async def build_prompt(request_data: dict):
    """Build prompt from context and question."""

    context = request_data.get("context", "")
    question = request_data.get("question", "")

    # Improved RAG prompt template
    prompt = f"""
    ```

    You are a precise AI assistant. Answer the user's question using ONLY the information provided in the context below.

    Rules:

    1. Use only the provided context to answer the question.
    2. Do NOT use outside knowledge.
    3. If the answer is not present in the context, respond with: "The answer is not available in the provided context."
    4. Be concise, clear, and factual.
    5. If relevant, reference the context in your explanation.

    ---

    Context:
    {context}
    ---------

    Question:
    {question}

    Answer:
    """
    return {"prompt": prompt}

@app.post("/build_quiz_prompt")
async def build_quiz_prompt(request_data: dict):
    """Build quiz-specific prompt."""
    topic = request_data.get("topic", "")
    num_questions = request_data.get("num_questions", 5)
    difficulty = request_data.get("difficulty", "medium")

    quiz_prompt = f"""
You are an expert quiz generator. Create exactly {num_questions} multiple-choice questions on the topic: "{topic}" at {difficulty} difficulty level.

STRICT RULES:
1. EXACTLY 4 options per question (A, B, C, D).
2. EXACTLY ONE correct option per question.
3. If concept has multiple correct aspects, COMBINE into ONE option (e.g., "Both A and C", "All of the above").
4. Questions must test understanding, not trivia.
5. Use your knowledge up to cutoff; be accurate.

Output ONLY valid JSON array, no other text:
[
  {{
    "question": "Full question text?",
    "options": [
      "A) Option one",
      "B) Option two", 
      "C) Option three (or 'A, B and D' if combined)",
      "D) Option four"
    ],
    "correct": "C"
  }}
  // exactly {num_questions} objects
]
"""
    return {"quiz_prompt": quiz_prompt}
