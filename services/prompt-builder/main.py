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
    """Build quiz-specific prompt optimized for small LLMs."""
    
    topic = request_data.get("topic", "")
    num_questions = request_data.get("num_questions", 5)
    difficulty = request_data.get("difficulty", "medium")
    context = request_data.get("context", "")

    context_part = f"Context:\n{context}\n\n" if context else ""

    quiz_prompt = f"""
    {context_part}Generate {num_questions} MCQ questions about: {topic}
    Difficulty: {difficulty}

    RULES:
    - Return ONLY JSON
    - No explanation, no text outside JSON
    - Each question has EXACTLY 4 options
    - Options must be labeled A, B, C, D
    - Only ONE correct answer
    - Use ONLY the context

    FORMAT:
    [
      {{
        "question": "question text",
        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "correct": "A"
      }}
    ]

    IMPORTANT:
    - Output must start with [ and end with ]
    - Do NOT add markdown or text

    OUTPUT:
    """
    
    return {"quiz_prompt": quiz_prompt}