#!/usr/bin/env python3
"""
FastAPI Backend - REST API for Conversation Evaluation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
from pathlib import Path
import logging

from facet_manager import FacetManager
from conversation_evaluator import ConversationEvaluator, ConversationTurn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Conversation Evaluation Benchmark API",
    description="API for evaluating conversations on multiple facets",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
facet_manager: Optional[FacetManager] = None
evaluator: Optional[ConversationEvaluator] = None
initialized = False

# ==================== Request Models ====================

class ConversationTurnRequest(BaseModel):
    speaker: str  # "user" or "assistant"
    content: str

class ConversationEvaluationRequest(BaseModel):
    turns: List[ConversationTurnRequest]
    facet_ids: Optional[List[int]] = None
    batch_evaluation: bool = True

class FacetQuery(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    difficulty: Optional[str] = None

# ==================== Response Models ====================

class FacetResponse(BaseModel):
    id: int
    name: str
    category: str
    priority: str
    description: str

class FacetScoreResponse(BaseModel):
    facet_id: int
    facet_name: str
    score: int
    confidence: float
    reasoning: str
    evidence: List[str]

class TurnEvaluationResponse(BaseModel):
    turn_id: str
    speaker: str
    content: str
    facet_scores: List[FacetScoreResponse]
    overall_quality: float

class ConversationEvaluationResponse(BaseModel):
    conversation_id: str
    total_score: float
    average_confidence: float
    turn_evaluations: List[TurnEvaluationResponse]

# ==================== Initialization ====================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global facet_manager, evaluator, initialized
    
    try:
        logger.info("Initializing Conversation Evaluation API...")
        
        # Load facets
        facets_path = Path("data/facets_processed.json")
        if facets_path.exists():
            facet_manager = FacetManager(str(facets_path))
            logger.info(f"✓ Loaded {facet_manager.total_facets} facets")
        else:
            logger.warning("Facets file not found, initializing empty manager")
            facet_manager = FacetManager()
        
        # Initialize evaluator
        evaluator = ConversationEvaluator(facet_manager=facet_manager)
        logger.info("✓ Evaluator initialized")
        
        initialized = True
        logger.info("✓ API initialization complete")
    
    except Exception as e:
        logger.error(f"✗ Initialization failed: {e}")
        raise

# ==================== Health & Status Endpoints ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "initialized": initialized,
        "facets_loaded": facet_manager.total_facets if facet_manager else 0
    }

@app.get("/status", tags=["Status"])
async def get_status():
    """Get system status"""
    if not initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    stats = facet_manager.get_facet_statistics()
    return {
        "system": "operational",
        "facet_manager": {
            "total_facets": stats['total_facets'],
            "categories": stats['categories'],
            "priority_distribution": stats['priority_distribution'],
            "difficulty_distribution": stats['difficulty_distribution']
        },
        "evaluator": {
            "evaluations_completed": len(evaluator.evaluation_history)
        }
    }

# ==================== Facet Endpoints ====================

@app.get("/facets", tags=["Facets"], response_model=List[FacetResponse])
async def get_facets(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100
):
    """Get facets with optional filtering"""
    if not initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    facets = []
    
    if category:
        facets = facet_manager.get_facets_by_category(category)
    elif priority:
        facets = facet_manager.get_facets_by_priority(priority)
    else:
        facets = list(facet_manager.facets.values())
    
    return [
        FacetResponse(
            id=f.id,
            name=f.name,
            category=f.category,
            priority=f.priority,
            description=f.description
        )
        for f in facets[:limit]
    ]

@app.get("/facets/{facet_id}", tags=["Facets"], response_model=FacetResponse)
async def get_facet(facet_id: int):
    """Get specific facet by ID"""
    if not initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    facet = facet_manager.get_facet(facet_id)
    if not facet:
        raise HTTPException(status_code=404, detail="Facet not found")
    
    return FacetResponse(
        id=facet.id,
        name=facet.name,
        category=facet.category,
        priority=facet.priority,
        description=facet.description
    )

@app.get("/facets/category/{category}", tags=["Facets"])
async def get_facets_by_category(category: str, limit: int = 50):
    """Get all facets in a category"""
    if not initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    facets = facet_manager.get_facets_by_category(category)
    
    if not facets:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {
        "category": category,
        "count": len(facets),
        "facets": [
            {
                "id": f.id,
                "name": f.name,
                "priority": f.priority,
                "difficulty": f.evaluation_difficulty
            }
            for f in facets[:limit]
        ]
    }

@app.get("/facets/statistics", tags=["Facets"])
async def get_facets_statistics():
    """Get facet statistics"""
    if not initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return facet_manager.get_facet_statistics()

# ==================== Evaluation Endpoints ====================

@app.post("/evaluate/conversation", tags=["Evaluation"], response_model=ConversationEvaluationResponse)
async def evaluate_conversation(request: ConversationEvaluationRequest):
    """Evaluate a conversation"""
    if not initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Convert request to conversation
        turns = [
            (turn.speaker, turn.content)
            for turn in request.turns
        ]
        
        conversation = evaluator.create_conversation(turns)
        
        # Evaluate
        evaluated = evaluator.evaluate_conversation(conversation)
        
        # Format response
        turn_evals = []
        for turn_eval in evaluated.turn_evaluations:
            turn_evals.append(TurnEvaluationResponse(
                turn_id=turn_eval.turn_id,
                speaker=turn_eval.speaker,
                content=turn_eval.content,
                facet_scores=[
                    FacetScoreResponse(
                        facet_id=score.facet_id,
                        facet_name=score.facet_name,
                        score=score.score,
                        confidence=score.confidence,
                        reasoning=score.reasoning,
                        evidence=score.evidence
                    )
                    for score in turn_eval.facet_scores
                ],
                overall_quality=turn_eval.overall_quality
            ))
        
        return ConversationEvaluationResponse(
            conversation_id=evaluated.conversation_id,
            total_score=evaluated.total_score,
            average_confidence=evaluated.get_average_confidence(),
            turn_evaluations=turn_evals
        )
    
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate/turn", tags=["Evaluation"])
async def evaluate_turn(request: ConversationTurnRequest):
    """Evaluate a single turn"""
    if not initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        turn = ConversationTurn(
            speaker=request.speaker,
            content=request.content
        )
        
        turn_eval = evaluator.evaluate_turn(turn, use_batch=True)
        
        return {
            "turn_id": turn_eval.turn_id,
            "speaker": turn_eval.speaker,
            "overall_quality": turn_eval.overall_quality,
            "facet_scores": [
                {
                    "facet_id": score.facet_id,
                    "facet_name": score.facet_name,
                    "score": score.score,
                    "confidence": score.confidence,
                    "reasoning": score.reasoning,
                    "evidence": score.evidence
                }
                for score in turn_eval.facet_scores
            ]
        }
    
    except Exception as e:
        logger.error(f"Turn evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Batch Operations ====================

@app.post("/evaluate/batch", tags=["Evaluation"])
async def batch_evaluate(requests: List[ConversationEvaluationRequest], background_tasks: BackgroundTasks):
    """Batch evaluate multiple conversations"""
    if not initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Process in background
    def process_batch():
        results = []
        for req in requests:
            try:
                turns = [(t.speaker, t.content) for t in req.turns]
                conversation = evaluator.create_conversation(turns)
                evaluated = evaluator.evaluate_conversation(conversation)
                results.append({
                    "conversation_id": evaluated.conversation_id,
                    "total_score": evaluated.total_score,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "status": "error",
                    "error": str(e)
                })
        
        # Save results
        output_file = Path("output/batch_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    background_tasks.add_task(process_batch)
    
    return {
        "status": "processing",
        "message": f"Batch processing {len(requests)} conversations",
        "results_file": "output/batch_results.json"
    }

# ==================== Error Handlers ====================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "detail": str(exc)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
