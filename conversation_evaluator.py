#!/usr/bin/env python3
"""
Conversation Evaluator - Core evaluation engine using LLM for scoring
Provides interface for evaluating conversation turns on multiple facets
"""

import json
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from datetime import datetime
import statistics

@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    speaker: str = ""  # 'user' or 'assistant'
    content: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class FacetScore:
    """Score for a single facet evaluation"""
    facet_id: int
    facet_name: str
    score: int  # 1-5
    confidence: float = 0.0  # 0.0-1.0
    reasoning: str = ""
    evidence: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class TurnEvaluation:
    """Complete evaluation of a conversation turn"""
    turn_id: str
    speaker: str
    content: str
    facet_scores: List[FacetScore] = field(default_factory=list)
    overall_quality: float = 0.0
    evaluation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'facet_scores': [s.to_dict() for s in self.facet_scores]
        }
    
    def get_score_for_facet(self, facet_id: int) -> Optional[FacetScore]:
        """Get score for specific facet"""
        for score in self.facet_scores:
            if score.facet_id == facet_id:
                return score
        return None

@dataclass
class ConversationEvaluation:
    """Complete evaluation of a conversation"""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    turns: List[ConversationTurn] = field(default_factory=list)
    turn_evaluations: List[TurnEvaluation] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    facets_evaluated: int = 0
    total_score: float = 0.0
    category_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'turns': [t.to_dict() for t in self.turns],
            'turn_evaluations': [e.to_dict() for e in self.turn_evaluations]
        }
    
    def add_turn_evaluation(self, evaluation: TurnEvaluation):
        """Add turn evaluation to conversation"""
        self.turn_evaluations.append(evaluation)
        self.facets_evaluated = len(evaluation.facet_scores)
        
        # Update overall scores
        self._recalculate_scores()
    
    def _recalculate_scores(self):
        """Recalculate overall conversation scores"""
        if not self.turn_evaluations:
            return
        
        # Calculate total score
        all_scores = []
        for turn_eval in self.turn_evaluations:
            for facet_score in turn_eval.facet_scores:
                all_scores.append(facet_score.score)
        
        if all_scores:
            self.total_score = statistics.mean(all_scores)
    
    def get_average_confidence(self) -> float:
        """Get average confidence across all facet scores"""
        confidences = []
        for turn_eval in self.turn_evaluations:
            for facet_score in turn_eval.facet_scores:
                confidences.append(facet_score.confidence)
        
        return statistics.mean(confidences) if confidences else 0.0
    
    def get_scores_by_category(self, category: str) -> List[int]:
        """Get all scores for facets in a category"""
        scores = []
        for turn_eval in self.turn_evaluations:
            for facet_score in turn_eval.facet_scores:
                if hasattr(facet_score, 'category') and facet_score.category == category:
                    scores.append(facet_score.score)
        return scores

class EvaluationPromptBuilder:
    """Builds evaluation prompts for LLM"""
    
    @staticmethod
    def build_facet_evaluation_prompt(
        turn_content: str,
        speaker: str,
        facet_name: str,
        facet_description: str,
        score_range: Tuple[int, int] = (1, 5)
    ) -> str:
        """Build prompt for evaluating a single facet"""
        
        min_score, max_score = score_range
        
        prompt = f"""You are evaluating a conversation turn on a specific facet.

CONVERSATION TURN:
Speaker: {speaker}
Content: {turn_content}

FACET TO EVALUATE:
Name: {facet_name}
Description: {facet_description}

EVALUATION TASK:
Score this conversation turn on the "{facet_name}" facet using the scale from {min_score} to {max_score}.
- {min_score} = Fails completely on this facet
- {max_score} = Excellent on this facet

Provide your response in JSON format with the following structure:
{{
    "score": <integer between {min_score} and {max_score}>,
    "confidence": <float between 0.0 and 1.0>,
    "reasoning": "<brief explanation of the score>",
    "evidence": ["<piece of evidence 1>", "<piece of evidence 2>"]
}}

Respond ONLY with the JSON object, no other text."""
        
        return prompt
    
    @staticmethod
    def build_batch_evaluation_prompt(
        turn_content: str,
        speaker: str,
        facets: List[Dict],
        score_range: Tuple[int, int] = (1, 5)
    ) -> str:
        """Build prompt for evaluating multiple facets in one call"""
        
        min_score, max_score = score_range
        facets_text = "\n".join([
            f"{i+1}. {f['name']}: {f.get('description', '')}"
            for i, f in enumerate(facets)
        ])
        
        prompt = f"""Evaluate this conversation turn on multiple facets.

CONVERSATION TURN:
Speaker: {speaker}
Content: {turn_content}

FACETS TO EVALUATE:
{facets_text}

EVALUATION TASK:
Score this conversation turn on each facet using the scale from {min_score} to {max_score}.

Provide your response as a JSON array where each element has this structure:
[
    {{
        "facet_id": <integer>,
        "facet_name": "<facet name>",
        "score": <integer between {min_score} and {max_score}>,
        "confidence": <float between 0.0 and 1.0>,
        "reasoning": "<brief explanation>",
        "evidence": ["<evidence>"]
    }},
    ...
]

Respond ONLY with the JSON array, no other text."""
        
        return prompt

class ConversationEvaluator:
    """
    Main evaluator class
    Can be extended with different LLM backends (Ollama, HuggingFace, etc.)
    """
    
    def __init__(self, facet_manager=None, llm_backend=None):
        """Initialize evaluator"""
        self.facet_manager = facet_manager
        self.llm_backend = llm_backend
        self.evaluations_cache = {}
        self.evaluation_history = []
    
    def create_conversation(self, turns: List[Tuple[str, str]]) -> ConversationEvaluation:
        """Create a conversation object from turn list"""
        conversation = ConversationEvaluation()
        
        for speaker, content in turns:
            turn = ConversationTurn(
                speaker=speaker,
                content=content
            )
            conversation.turns.append(turn)
        
        return conversation
    
    def evaluate_turn(
        self,
        turn: ConversationTurn,
        facet_ids: Optional[List[int]] = None,
        use_batch: bool = False
    ) -> TurnEvaluation:
        """
        Evaluate a single turn
        
        Args:
            turn: The conversation turn to evaluate
            facet_ids: Specific facets to evaluate (None = all)
            use_batch: Whether to use batch evaluation
        
        Returns:
            TurnEvaluation with scores
        """
        
        # Get facets to evaluate
        if facet_ids:
            facets = [self.facet_manager.get_facet(fid) for fid in facet_ids if fid]
        else:
            # Use evaluation subset for efficiency
            facets = self.facet_manager.get_evaluation_subset(batch_size=50)
        
        # Create turn evaluation
        turn_evaluation = TurnEvaluation(
            turn_id=turn.id,
            speaker=turn.speaker,
            content=turn.content
        )
        
        if use_batch and len(facets) > 1:
            # Batch evaluation
            facet_dicts = [
                {'id': f.id, 'name': f.name, 'description': f.description}
                for f in facets
            ]
            scores = self._batch_evaluate_facets(turn.content, turn.speaker, facet_dicts)
            turn_evaluation.facet_scores = scores
        else:
            # Individual evaluation
            for facet in facets:
                score = self._evaluate_single_facet(turn.content, turn.speaker, facet)
                turn_evaluation.facet_scores.append(score)
        
        # Calculate overall quality
        if turn_evaluation.facet_scores:
            scores = [s.score for s in turn_evaluation.facet_scores]
            turn_evaluation.overall_quality = sum(scores) / len(scores)
        
        return turn_evaluation
    
    def _evaluate_single_facet(
        self,
        turn_content: str,
        speaker: str,
        facet
    ) -> FacetScore:
        """Evaluate single facet (stub for LLM integration)"""
        
        # Build prompt
        prompt = EvaluationPromptBuilder.build_facet_evaluation_prompt(
            turn_content=turn_content,
            speaker=speaker,
            facet_name=facet.name,
            facet_description=facet.description
        )
        
        # Call LLM (if available)
        if self.llm_backend:
            response = self.llm_backend.evaluate(prompt)
            return self._parse_facet_response(facet.id, facet.name, response)
        else:
            # Mock scoring for testing
            return self._mock_score_facet(facet)
    
    def _batch_evaluate_facets(
        self,
        turn_content: str,
        speaker: str,
        facets: List[Dict]
    ) -> List[FacetScore]:
        """Batch evaluate multiple facets"""
        
        prompt = EvaluationPromptBuilder.build_batch_evaluation_prompt(
            turn_content=turn_content,
            speaker=speaker,
            facets=facets
        )
        
        # Call LLM (if available)
        if self.llm_backend:
            response = self.llm_backend.evaluate(prompt)
            return self._parse_batch_response(response)
        else:
            # Mock scoring
            return [self._mock_score_facet_dict(f) for f in facets]
    
    def _parse_facet_response(self, facet_id: int, facet_name: str, response: str) -> FacetScore:
        """Parse LLM response for facet score"""
        try:
            data = json.loads(response)
            return FacetScore(
                facet_id=facet_id,
                facet_name=facet_name,
                score=int(data.get('score', 3)),
                confidence=float(data.get('confidence', 0.5)),
                reasoning=data.get('reasoning', ''),
                evidence=data.get('evidence', [])
            )
        except:
            return self._mock_score_facet_dict({'id': facet_id, 'name': facet_name})
    
    def _parse_batch_response(self, response: str) -> List[FacetScore]:
        """Parse LLM response for batch scores"""
        try:
            data = json.loads(response)
            scores = []
            for item in data:
                scores.append(FacetScore(
                    facet_id=item.get('facet_id', 0),
                    facet_name=item.get('facet_name', ''),
                    score=int(item.get('score', 3)),
                    confidence=float(item.get('confidence', 0.5)),
                    reasoning=item.get('reasoning', ''),
                    evidence=item.get('evidence', [])
                ))
            return scores
        except:
            return []
    
    def _mock_score_facet(self, facet) -> FacetScore:
        """Generate mock score for testing"""
        import random
        return FacetScore(
            facet_id=facet.id,
            facet_name=facet.name,
            score=random.randint(1, 5),
            confidence=random.uniform(0.6, 1.0),
            reasoning=f"Mock evaluation of {facet.name}",
            evidence=["Sample evidence"]
        )
    
    def _mock_score_facet_dict(self, facet_dict: Dict) -> FacetScore:
        """Generate mock score from dict"""
        import random
        return FacetScore(
            facet_id=facet_dict.get('id', 0),
            facet_name=facet_dict.get('name', ''),
            score=random.randint(1, 5),
            confidence=random.uniform(0.6, 1.0),
            reasoning=f"Mock evaluation",
            evidence=[]
        )
    
    def evaluate_conversation(
        self,
        conversation: ConversationEvaluation,
        evaluate_all_turns: bool = True
    ) -> ConversationEvaluation:
        """Evaluate entire conversation"""
        
        for i, turn in enumerate(conversation.turns):
            if i > 0 and not evaluate_all_turns:
                # Evaluate only last turn for efficiency
                continue
            
            turn_eval = self.evaluate_turn(turn, use_batch=True)
            conversation.add_turn_evaluation(turn_eval)
        
        # Store in history
        self.evaluation_history.append(conversation)
        
        return conversation
    
    def export_evaluation(self, conversation: ConversationEvaluation, output_path: str):
        """Export evaluation to JSON"""
        with open(output_path, 'w') as f:
            json.dump(conversation.to_dict(), f, indent=2, default=str)
        print(f"✓ Exported evaluation to {output_path}")

if __name__ == "__main__":
    # Test initialization
    evaluator = ConversationEvaluator()
    print("✓ ConversationEvaluator initialized successfully")
