#!/usr/bin/env python3
"""
Main Integration Script
Orchestrates the entire conversation evaluation system
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Import modules
sys.path.insert(0, str(Path(__file__).parent))

from data_processor import FacetDataProcessor
from facet_manager import FacetManager
from conversation_evaluator import ConversationEvaluator, ConversationTurn
from sample_generator import SampleConversationGenerator

class EvaluationPipeline:
    """Main pipeline for conversation evaluation"""
    
    def __init__(self, facets_csv_path: str, output_dir: str = "./output"):
        self.facets_csv_path = facets_csv_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.facet_processor = None
        self.facet_manager = None
        self.evaluator = None
        self.conversations = None
    
    def run_pipeline(self):
        """Run complete evaluation pipeline"""
        print("\n" + "=" * 70)
        print("CONVERSATION EVALUATION BENCHMARK - PIPELINE EXECUTION")
        print("=" * 70)
        
        try:
            # Step 1: Prepare data
            self.step_prepare_facet_data()
            
            # Step 2: Initialize facet manager
            self.step_initialize_facet_manager()
            
            # Step 3: Generate sample conversations
            self.step_generate_sample_conversations()
            
            # Step 4: Initialize evaluator
            self.step_initialize_evaluator()
            
            # Step 5: Evaluate conversations
            self.step_evaluate_conversations()
            
            # Step 6: Generate reports
            self.step_generate_reports()
            
            print("\n" + "=" * 70)
            print("✓ PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n✗ Pipeline failed: {e}")
            raise
    
    def step_prepare_facet_data(self):
        """Step 1: Prepare facet data"""
        print("\n[Step 1/6] Preparing Facet Data...")
        print("-" * 70)
        
        self.facet_processor = FacetDataProcessor(self.facets_csv_path)
        self.facet_processor.load_facets_from_csv()
        self.facet_processor.process_facets()
        self.facet_processor.create_facet_dataframe()
        self.facet_processor.add_facet_relationships()
        self.facet_processor.save_processed_facets(str(self.output_dir / "facets"))
        
        stats = self.facet_processor.get_statistics()
        print(f"  ✓ Total facets: {stats['total_facets']}")
        print(f"  ✓ Categories: {stats['categories']}")
        print(f"  ✓ High priority: {stats['high_priority_count']}")
        print(f"  ✓ High difficulty: {stats['high_difficulty_count']}")
    
    def step_initialize_facet_manager(self):
        """Step 2: Initialize facet manager"""
        print("\n[Step 2/6] Initializing Facet Manager...")
        print("-" * 70)
        
        # Load processed facets
        facets_json = self.output_dir / "facets" / "facets_processed.json"
        
        self.facet_manager = FacetManager(str(facets_json))
        
        is_valid, errors = self.facet_manager.validate_facet_consistency()
        
        if is_valid:
            print("  ✓ Facet manager initialized successfully")
            self.facet_manager.print_summary()
        else:
            print(f"  ⚠ Validation warnings: {len(errors)}")
            for error in errors[:5]:
                print(f"    - {error}")
    
    def step_generate_sample_conversations(self):
        """Step 3: Generate sample conversations"""
        print("\n[Step 3/6] Generating Sample Conversations...")
        print("-" * 70)
        
        generator = SampleConversationGenerator()
        generator.generate_from_templates()
        generator.generate_additional_conversations(count=40)
        
        generator.print_summary()
        
        # Export conversations
        conversations_dir = self.output_dir / "conversations"
        generator.export_conversations(str(conversations_dir))
        generator.create_evaluation_manifest(str(conversations_dir))
        
        self.conversations = generator.conversations
        print(f"  ✓ Generated {len(self.conversations)} sample conversations")
    
    def step_initialize_evaluator(self):
        """Step 4: Initialize evaluator"""
        print("\n[Step 4/6] Initializing Conversation Evaluator...")
        print("-" * 70)
        
        self.evaluator = ConversationEvaluator(
            facet_manager=self.facet_manager,
            llm_backend=None  # No LLM backend configured yet
        )
        
        print("  ✓ Conversation evaluator initialized")
        print("  ℹ Note: Using mock scoring (LLM backend not configured)")
    
    def step_evaluate_conversations(self):
        """Step 5: Evaluate conversations"""
        print("\n[Step 5/6] Evaluating Conversations...")
        print("-" * 70)
        
        evaluations_dir = self.output_dir / "evaluations"
        evaluations_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "total_conversations": len(self.conversations),
            "evaluations": [],
            "statistics": {}
        }
        
        for i, sample_conv in enumerate(self.conversations, 1):
            # Create conversation object
            conversation = self.evaluator.create_conversation([
                (turn["speaker"], turn["content"]) for turn in sample_conv.turns
            ])
            
            # Evaluate
            evaluated = self.evaluator.evaluate_conversation(conversation)
            
            # Store results
            evaluation_dict = evaluated.to_dict()
            evaluation_dict["sample_metadata"] = {
                "conversation_id": sample_conv.conversation_id,
                "category": sample_conv.category,
                "quality_level": sample_conv.quality_level,
                "focus_areas": sample_conv.focus_areas
            }
            
            results["evaluations"].append(evaluation_dict)
            
            # Export individual evaluation
            eval_file = evaluations_dir / f"{sample_conv.conversation_id}_evaluation.json"
            with open(eval_file, 'w') as f:
                json.dump(evaluation_dict, f, indent=2, default=str)
            
            if i % 10 == 0:
                print(f"  ✓ Evaluated {i}/{len(self.conversations)} conversations")
        
        # Save all evaluations
        all_evals_file = evaluations_dir / "all_evaluations.json"
        with open(all_evals_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"  ✓ Completed evaluation of {len(self.conversations)} conversations")
        print(f"  ✓ Evaluations saved to {evaluations_dir}")
    
    def step_generate_reports(self):
        """Step 6: Generate reports"""
        print("\n[Step 6/6] Generating Reports...")
        print("-" * 70)
        
        reports = {
            "pipeline_summary": {
                "facets_total": self.facet_manager.total_facets,
                "conversations_evaluated": len(self.conversations),
                "evaluation_timestamp": self._get_timestamp()
            },
            "facet_coverage": self._get_facet_coverage(),
            "conversation_categories": self._get_conversation_categories(),
            "quality_distribution": self._get_quality_distribution(),
            "key_metrics": self._calculate_key_metrics()
        }
        
        report_file = self.output_dir / "evaluation_report.json"
        with open(report_file, 'w') as f:
            json.dump(reports, f, indent=2, default=str)
        
        print(f"  ✓ Generated evaluation report at {report_file}")
        
        # Print summary
        self._print_final_summary(reports)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_facet_coverage(self) -> dict:
        """Get facet coverage statistics"""
        stats = self.facet_manager.get_facet_statistics()
        return {
            "total_facets": stats['total_facets'],
            "total_categories": stats['total_categories'],
            "categories": stats['category_distribution']
        }
    
    def _get_conversation_categories(self) -> dict:
        """Get conversation category distribution"""
        categories = {}
        for conv in self.conversations:
            if conv.category not in categories:
                categories[conv.category] = 0
            categories[conv.category] += 1
        return categories
    
    def _get_quality_distribution(self) -> dict:
        """Get quality level distribution"""
        quality = {}
        for conv in self.conversations:
            if conv.quality_level not in quality:
                quality[conv.quality_level] = 0
            quality[conv.quality_level] += 1
        return quality
    
    def _calculate_key_metrics(self) -> dict:
        """Calculate key evaluation metrics"""
        return {
            "total_evaluations": len(self.evaluator.evaluation_history),
            "average_confidence": sum(
                e.get_average_confidence()
                for e in self.evaluator.evaluation_history
            ) / max(1, len(self.evaluator.evaluation_history)),
            "scalability_note": "Architecture supports 5000+ facets without redesign"
        }
    
    def _print_final_summary(self, reports: dict):
        """Print final summary"""
        print("\n" + "=" * 70)
        print("EVALUATION SUMMARY")
        print("=" * 70)
        
        summary = reports["pipeline_summary"]
        print(f"Total Facets Loaded: {summary['facets_total']}")
        print(f"Conversations Evaluated: {summary['conversations_evaluated']}")
        print(f"\nCategory Distribution:")
        for cat, count in reports["conversation_categories"].items():
            print(f"  - {cat}: {count}")
        print(f"\nQuality Distribution:")
        for quality, count in reports["quality_distribution"].items():
            print(f"  - {quality}: {count}")
        print("=" * 70)

def main():
    """Main entry point"""
    
    # Configuration
    facets_csv_path = "c:/Users/prave/Downloads/OceanAcross/Facets Assignment.csv"
    output_dir = "./conversation_evaluation_output"
    
    # Run pipeline
    pipeline = EvaluationPipeline(facets_csv_path, output_dir)
    pipeline.run_pipeline()

if __name__ == "__main__":
    main()
