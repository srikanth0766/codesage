"""
FastAPI backend for the CodeSage (Agile-Aware Agentic Smell-Aware Compiler).

Endpoints:
  POST /predict          – runtime error prediction (CodeBERT)
  POST /review           – comprehensive multi-layer code review
  POST /chat             – interactive chat about analysis results
  POST /analyze-smells   – standalone smell detection
  POST /refactor         – LLM-based smell refactoring agent
  POST /log-sprint       – store sprint smell metrics
  POST /predict-sprint-risk – sprint risk prediction
  GET  /sprint-analytics – full sprint history for dashboard
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager
from pathlib import Path
from model import ErrorDetectionModel
from agent_orchestrator import CodeReviewAgent
from chat_handler import ChatHandler, ChatContext, ChatMessage
from analyzers.smell_detector import SmellDetector
import uvicorn
import os
import datetime

def log_action(action: str):
    """Write semantic logs to action.log for the UI Activity Feed."""
    try:
        timestamp = datetime.datetime.now().strftime("%I:%M %p")
        with open("action.log", "a") as f:
            f.write(f"[{timestamp}] {action}\n")
    except Exception:
        pass


# Global instances (loaded once at startup)
model: ErrorDetectionModel = None
agent: CodeReviewAgent = None
chat_handler: ChatHandler = None
smell_detector: SmellDetector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global model, agent, chat_handler, smell_detector
    
    # Startup
    print("Starting up... Loading model...")
    model = ErrorDetectionModel()
    print("Model loaded successfully!")

    print("Initializing code review agent...")
    agent = CodeReviewAgent(runtime_model=model)
    print("Agent initialized and ready!")

    print("Initializing chat handler...")
    chat_handler = ChatHandler()
    print("Chat handler ready!")

    print("Initializing smell detector...")
    smell_detector = SmellDetector()
    print("Smell detector ready!")

    # Initialise sprint store (creates file if missing)
    from agile_risk.sprint_store import SprintStore
    SprintStore()
    print("Sprint store ready!")
    
    yield
    
    # Shutdown (cleanup if needed)
    print("Shutting down...")


# Request/Response models
class PredictRequest(BaseModel):
    """Request model for /predict endpoint."""
    code: str = Field(..., description="Python source code to analyze")


class PredictResponse(BaseModel):
    """Response model for /predict endpoint."""
    error_type: str = Field(..., description="Predicted error type")
    confidence: float = Field(..., description="Confidence score (0.0 - 1.0)")


class ReviewRequest(BaseModel):
    """Request model for /review endpoint."""
    code: str = Field(..., description="Source code to analyze")
    language: str = Field(default="python", description="Programming language (python, javascript, typescript, etc.)")
    include_logic_analysis: bool = Field(True, description="Include LLM-based logic analysis")
    include_optimizations: bool = Field(True, description="Include optimization suggestions")
    include_control_flow: bool = Field(True, description="Include control flow graph analysis")


class ReviewResponse(BaseModel):
    """Response model for /review endpoint."""
    compile_time: Dict = Field(..., description="Compile-time analysis results")
    runtime_risks: List[Dict] = Field(..., description="Runtime error predictions")
    logical_concerns: List[str] = Field(..., description="Logical issues and edge cases")
    optimizations: List[Dict] = Field(..., description="Code optimization suggestions")
    control_flow: Optional[Dict] = Field(None, description="Control flow graph and issues")
    smells: List[Dict] = Field(default=[], description="Code smells detected")
    summary: str = Field(..., description="Human-readable summary")


class ChatRequest(BaseModel):
    """Request model for /chat endpoint."""
    message: str = Field(..., description="User's question or message")
    code: str = Field(..., description="Python source code being discussed")
    analysis_results: Dict = Field(..., description="Previous analysis results for context")
    chat_history: List[Dict] = Field(default=[], description="Previous messages in conversation")


class ChatResponse(BaseModel):
    """Response model for /chat endpoint."""
    response: str = Field(..., description="AI-generated response to user's message")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Python Error Detection API",
    description="AI-based error detection for Python code using CodeBERT",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow requests from VS Code extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "message": "Python Error Detection API is running",
        "endpoint": "/predict"
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Predict the error type for given Python code.
    
    Args:
        request: PredictRequest containing Python code
        
    Returns:
        PredictResponse with error_type and confidence
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    try:
        # Get prediction from model
        error_type, confidence = model.predict(request.code)
        
        log_action(f"Predicted error risk ({error_type}: {confidence*100:.1f}%)")
        
        return PredictResponse(
            error_type=error_type,
            confidence=round(confidence, 4)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during prediction: {str(e)}"
        )


@app.post("/review", response_model=ReviewResponse)
async def review_code(request: ReviewRequest):
    """
    Comprehensive code review using agentic AI.
    
    This endpoint orchestrates multiple analysis tools:
    - Compile-time error detection (AST-based)
    - Runtime error prediction (CodeBERT model)
    - Logical error detection (LLM reasoning)
    - Optimization suggestions (heuristics + LLM)
    
    Args:
        request: ReviewRequest with code and options
        
    Returns:
        ReviewResponse with comprehensive analysis
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not loaded yet")
    
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    try:
        # Run comprehensive review
        result = agent.review_code(
            code=request.code,
            language=request.language,
            include_logic_analysis=request.include_logic_analysis,
            include_optimizations=request.include_optimizations,
            include_control_flow=request.include_control_flow
        )
        
        return ReviewResponse(
            compile_time=result.compile_time,
            runtime_risks=result.runtime_risks,
            logical_concerns=result.logical_concerns,
            optimizations=result.optimizations,
            control_flow=result.control_flow,
            smells=result.smells,
            summary=result.summary
        )
        
        log_action(f"Comprehensive code review completed ({len(result.smells)} smells)")
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during code review: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Interactive chat about code analysis.
    
    This endpoint allows users to ask follow-up questions about their code
    and the analysis results. The chat maintains context from previous messages.
    
    Args:
        request: ChatRequest with user message, code, analysis, and history
        
    Returns:
        ChatResponse with AI-generated answer
    """
    if chat_handler is None:
        raise HTTPException(status_code=503, detail="Chat handler not loaded yet")
    
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        # Convert chat history to ChatMessage objects
        history = [
            ChatMessage(role=msg.get("role", "user"), content=msg.get("content", ""))
            for msg in request.chat_history
        ]
        
        # Create context
        context = ChatContext(
            code=request.code,
            analysis_results=request.analysis_results,
            chat_history=history
        )
        
        # Generate response
        response_text = chat_handler.chat(request.message, context)
        
        return ChatResponse(response=response_text)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during chat: {str(e)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# SMELL ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

class SmellRequest(BaseModel):
    """Request model for /analyze-smells endpoint."""
    code: str = Field(..., description="Source code to analyse")
    language: str = Field(default="python", description="Programming language")


class SmellResponse(BaseModel):
    """Response model for /analyze-smells endpoint."""
    smells: List[Dict] = Field(..., description="List of detected code smells")
    smell_count: int = Field(..., description="Total number of smells")
    high_confidence_count: int = Field(..., description="Smells with confidence > 0.75")
    overall_smell_score: float = Field(..., description="0-1 aggregate smell density")


@app.post("/analyze-smells", response_model=SmellResponse)
async def analyze_smells(request: SmellRequest):
    """
    Detect code smells using the rule-based smell detector.

    Returns smell probabilities for: Long Method, God Class, Feature Envy,
    Large Parameter List, Deep Nesting, High Complexity.
    """
    if smell_detector is None:
        raise HTTPException(status_code=503, detail="Smell detector not loaded")
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    try:
        smells = smell_detector.detect_to_dict(request.code)
        high_conf = [s for s in smells if s["confidence"] > 0.75]
        score = max((s["confidence"] for s in smells), default=0.0)
        
        log_action(f"Analyzed {request.language} codebase ({len(smells)} smells detected)")
        
        return SmellResponse(
            smells=smells,
            smell_count=len(smells),
            high_confidence_count=len(high_conf),
            overall_smell_score=round(score, 3),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smell detection error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# REFACTORING AGENT ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

class RefactorRequest(BaseModel):
    """Request model for /refactor endpoint."""
    code: str = Field(..., description="Source code containing the smell")
    smell: str = Field(..., description="Smell identifier e.g. 'long_method'")
    confidence: float = Field(default=0.8, description="Smell confidence score")


class RefactorResponse(BaseModel):
    """Response model for /refactor endpoint."""
    original_code: str
    refactored_code: str
    smell: str
    strategy: str
    success: bool
    notes: str


@app.post("/refactor", response_model=RefactorResponse)
async def refactor_code(request: RefactorRequest):
    """
    Use the LLM refactoring agent to fix a detected smell.
    """
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    try:
        from refactor_agent.refactor_agent import RefactorAgent
        ra_agent = RefactorAgent()
        result = ra_agent.refactor(
            code=request.code,
            smell=request.smell,
            confidence=request.confidence
        )
        if result.get("success"):
            log_action(f"Successfully auto-refactored '{request.smell}' smell")
        else:
            log_action(f"Failed to auto-refactor '{request.smell}' (AST invalid)")
        return RefactorResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refactoring error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# AGILE SPRINT RISK ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

class SprintLogRequest(BaseModel):
    """Log smell metrics for a sprint."""
    sprint_id: str = Field(..., description="Sprint identifier e.g. 'Sprint-3'")
    smell_count: int = Field(..., description="Total smells detected this sprint")
    refactor_count: int = Field(default=0, description="Smells refactored this sprint")
    module: str = Field(default="default", description="Module or service name")


class SprintRiskRequest(BaseModel):
    """Request model for /predict-sprint-risk."""
    sprint_history: List[int] = Field(..., description="Historical smell counts per sprint")
    refactor_history: Optional[List[int]] = Field(None, description="Historical refactor counts")
    threshold: int = Field(default=10, description="Smell count threshold to check against")


class SprintRiskResponse(BaseModel):
    risk_probability: float
    predicted_smell_count: float
    threshold: int
    trend: str
    recommendation: str


@app.post("/log-sprint")
async def log_sprint(request: SprintLogRequest):
    """Store sprint smell metrics for analytics and risk prediction."""
    try:
        from agile_risk.sprint_store import SprintStore
        store = SprintStore()
        store.log_sprint(
            sprint_id=request.sprint_id,
            smell_count=request.smell_count,
            refactor_count=request.refactor_count,
            module=request.module
        )
        return {"status": "logged", "sprint_id": request.sprint_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SprintUpdateInfo(BaseModel):
    smells_delta: int = 0
    refactor_delta: int = 0

@app.post("/update-latest-sprint")
async def update_latest_sprint(request: SprintUpdateInfo):
    """Update the most recent logged sprint with delta metrics from the Neural Auditor."""
    try:
        from agile_risk.sprint_store import SprintStore
        store = SprintStore()
        updated_sprint_id = store.update_latest_sprint(
            smells_delta=request.smells_delta,
            refactor_delta=request.refactor_delta
        )
        if not updated_sprint_id:
            return {"status": "ignored", "message": "No sprints exist to update."}
        return {"status": "updated", "sprint_id": updated_sprint_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-sprint-risk", response_model=SprintRiskResponse)
async def predict_sprint_risk(request: SprintRiskRequest):
    """Predict probability of smell count exceeding threshold next sprint."""
    if len(request.sprint_history) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 sprints of history")
    try:
        from agile_risk.sprint_risk_model import SprintRiskModel
        model_risk = SprintRiskModel()
        result = model_risk.predict(
            smell_history=request.sprint_history,
            refactor_history=request.refactor_history or [],
            threshold=request.threshold
        )
        return SprintRiskResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sprint-analytics")
async def sprint_analytics():
    """Return full sprint history for the dashboard."""
    try:
        from agile_risk.sprint_store import SprintStore
        store = SprintStore()
        return store.get_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sprints/{sprint_id}")
async def delete_sprint(sprint_id: str):
    """Delete a specific sprint from the history log."""
    try:
        from agile_risk.sprint_store import SprintStore
        store = SprintStore()
        success = store.delete_sprint(sprint_id)
        if not success:
            raise HTTPException(status_code=404, detail="Sprint not found")
        return {"status": "deleted", "sprint_id": sprint_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/logs/reset")
async def reset_logs():
    """Clear the action.log file."""
    try:
        log_path = Path("action.log")
        with open(log_path, "w") as f:
            f.write("")
        return {"status": "success", "message": "Logs cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
async def get_logs():
    """Return the last 50 lines of the action.log file."""
    try:
        log_path = Path("action.log")
        if not log_path.exists():
            return {"logs": ["System initialized. Awaiting telemetry..."]}
        
        with open(log_path, "r") as f:
            lines = f.readlines()
            
        return {"logs": lines[-50:]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
        



if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
