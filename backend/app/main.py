from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import shutil
from typing import Dict

from app.core.parser import RequirementsParser
from app.agents.planner import RequirementsPlanner
from app.agents.generator import TestCaseGenerator
from app.agents.coder import TestCoder
from app.agents.validator import TestValidator
from app.agents.debugger import TestDebugger
from app.core.test_runner import TestRunner
from app.core.models import TestSession
from app.core.learning_store import LearningStore

app = FastAPI(title="AI Test Platform")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Session storage (in-memory for demo)
sessions: Dict[str, TestSession] = {}

# Initialize agents
parser = RequirementsParser()
planner = RequirementsPlanner()
generator = TestCaseGenerator()  # uses GigaChat if configured
coder = TestCoder()
validator = TestValidator()
debugger = TestDebugger()  # uses GigaChat if configured
test_runner = TestRunner()
learning_store = LearningStore()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main page"""
    try:
        with open("app/static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>index.html file not found</h1>", status_code=404)

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload requirements file"""
    try:
        print(f"Received file: {file.filename}")
        
        # Save file temporarily
        file_path = f"temp_{file.filename}"
        content = await file.read()
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        print(f"File saved to: {file_path}")
        
        # Parse document
        requirements = parser.parse(file_path)
        print(f"Parsed {len(requirements)} requirements")
        
        # Create session
        session_id = f"session_{len(sessions) + 1}"
        sessions[session_id] = TestSession(session_id)
        sessions[session_id].requirements = requirements
        
        # Remove temporary file
        os.remove(file_path)
        print(f"Temporary file removed")
        
        return JSONResponse({
            "session_id": session_id,
            "requirements": [req.to_dict() for req in requirements]
        })
    except Exception as e:
        print(f"Error in upload: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/requirements/{session_id}")
async def set_requirements_text(session_id: str, payload: dict = Body(...)):
    """Set requirements text directly (useful for textarea UX)."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    text = (payload or {}).get("text", "")
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Missing 'text'")
    requirements = parser.parse_text(text)
    sessions[session_id].requirements = requirements
    return {"session_id": session_id, "requirements": [r.to_dict() for r in requirements]}

@app.post("/api/generate/{session_id}")
async def generate_tests(session_id: str):
    """Generate test cases from requirements"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Planner analyzes requirements
    test_units = planner.plan(session.requirements)
    
    # Generator creates test cases
    test_cases = generator.generate(test_units)
    session.test_cases = test_cases
    
    # Coder creates executable code
    code = coder.generate_code(test_cases)
    session.generated_code = code
    
    return JSONResponse({
        "test_cases": [tc.to_dict() for tc in test_cases],
        "code": code.to_dict()
    })

@app.post("/api/run/{session_id}")
async def run_tests(session_id: str):
    """Run generated tests"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    if not session.generated_code:
        raise HTTPException(status_code=400, detail="No code generated yet")
    
    # Save code to temporary file
    test_file = f"tests/test_{session_id}.py"
    os.makedirs("tests", exist_ok=True)
    
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(session.generated_code.code)
    
    # Run tests
    results = test_runner.run(test_file)
    session.test_results = results
    # Keep the latest test file around for learning/fixes
    session.last_test_file_path = test_file
    
    payload = results.to_dict()
    payload["code"] = session.generated_code.to_dict() if session.generated_code else None
    return JSONResponse(payload)

@app.post("/api/debug/{session_id}")
async def debug_results(session_id: str):
    """Analyze results and debug"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    if not session.test_results:
        raise HTTPException(status_code=400, detail="No test results yet")
    
    # Debugger analyzes results
    debug_info = debugger.analyze(
        session.test_results,
        session.generated_code,
        session.test_cases
    )
    session.debug_info = debug_info
    
    return JSONResponse(debug_info.to_dict())


@app.post("/api/chat/{session_id}")
async def chat_after_debug(session_id: str, payload: dict = Body(...)):
    """Chat with the system after Analyze Results."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    msg = (payload or {}).get("message", "")
    if not msg or not isinstance(msg, str):
        raise HTTPException(status_code=400, detail="Missing 'message'")

    session = sessions[session_id]

    pytest_output = ""
    try:
        pytest_output = getattr(session.test_results, "raw_output", "") or ""
    except Exception:
        pytest_output = ""

    session.chat_history.append({"role": "user", "content": msg})

    reply = debugger.chat(
        session.chat_history,
        context={
            "session_id": session_id,
            "tests_count": len(session.test_cases),
            "pytest_output": pytest_output,
            "debug_summary": session.debug_info.to_dict() if session.debug_info else {}
        }
    )

    session.chat_history.append({"role": "assistant", "content": reply})

    return {"reply": reply, "history": session.chat_history[-20:]}


@app.post("/api/fix_tests/{session_id}")
async def fix_tests(session_id: str, payload: dict = Body(...)):
    """Generate a corrected version of the pytest file based on user instruction + pytest output."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    if not session.test_results or not session.generated_code:
        raise HTTPException(status_code=400, detail="Run tests first")

    instruction = (payload or {}).get("instruction", "")
    if not isinstance(instruction, str):
        instruction = ""

    pytest_output = getattr(session.test_results, "raw_output", "") or ""
    original = session.generated_code.code or ""

    fixed = debugger.generate_fixed_tests(
        instruction=instruction,
        pytest_output=pytest_output,
        original_test_code=original,
    )

    # Store into session for easy "learn" UX
    session.last_fixed_test_code = fixed
    return {"fixed_code": fixed}


@app.post("/api/learn/{session_id}")
async def learn_from_fix(session_id: str, payload: dict = Body(...)):
    """Persist a user-approved correction so the system can reuse it as few-shot examples."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    if not session.test_results or not session.generated_code:
        raise HTTPException(status_code=400, detail="Run tests first")

    corrected = (payload or {}).get("corrected_test_code", "")
    notes = (payload or {}).get("notes", "")

    if not corrected or not isinstance(corrected, str):
        raise HTTPException(status_code=400, detail="Missing 'corrected_test_code'")

    pytest_output = getattr(session.test_results, "raw_output", "") or ""
    original = session.generated_code.code or ""

    ex = learning_store.add(
        session_id=session_id,
        pytest_output=pytest_output,
        original_test_code=original,
        corrected_test_code=corrected,
        notes=str(notes or ""),
    )

    return {"status": "ok", "stored": ex.to_dict()}

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return JSONResponse(session.to_dict())

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)