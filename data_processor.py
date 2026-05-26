#!/usr/bin/env python3
"""
Data preparation and preprocessing module for Facets
Loads, cleans, and enhances facet data for the evaluation benchmark
"""

import pandas as pd
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from enum import Enum
from dataclasses import dataclass, asdict

class FacetCategory(Enum):
    """Categories for grouping facets"""
    LINGUISTIC = "linguistic"
    PRAGMATIC = "pragmatic"
    SAFETY = "safety"
    EMOTION = "emotion"
    COGNITIVE = "cognitive"
    PERSONALITY = "personality"
    BEHAVIORAL = "behavioral"
    UNKNOWN = "unknown"

@dataclass
class Facet:
    """Represents a single evaluation facet"""
    id: int
    name: str
    category: FacetCategory
    description: str = ""
    subcategories: List[str] = None
    priority: str = "medium"  # low, medium, high
    data_type: str = "ordinal"  # ordinal, continuous, categorical
    applicable_context: str = "conversation"  # conversation, user, assistant, both
    
    def to_dict(self):
        return asdict(self)

class FacetDataProcessor:
    """Processes and manages facet data"""
    
    # Mapping patterns for categorization
    CATEGORY_PATTERNS = {
        FacetCategory.LINGUISTIC: [
            r"linguistic", r"grammar", r"syntax", r"vocabulary", r"spelling",
            r"language use", r"sentence structure", r"readability", r"coherence",
            r"clarity", r"comprehension", r"articulation", r"communication"
        ],
        FacetCategory.PRAGMATIC: [
            r"pragmatic", r"context", r"relevance", r"appropriateness",
            r"engagement", r"turn-taking", r"topic", r"goal-oriented",
            r"efficiency", r"effectiveness", r"cooperative", r"collaborative"
        ],
        FacetCategory.SAFETY: [
            r"safety", r"harmful", r"toxic", r"violence", r"abuse",
            r"harassment", r"bias", r"discrimination", r"privacy",
            r"security", r"ethical", r"compliance", r"appropriate"
        ],
        FacetCategory.EMOTION: [
            r"emotion", r"sentiment", r"feeling", r"mood", r"affect",
            r"empathy", r"compassion", r"warmth", r"hostility",
            r"frustration", r"joy", r"happiness", r"sadness", r"anger"
        ],
        FacetCategory.COGNITIVE: [
            r"reasoning", r"thinking", r"logical", r"analytical",
            r"problem.solving", r"decision", r"judgment", r"inference",
            r"understanding", r"knowledge", r"learning"
        ],
        FacetCategory.PERSONALITY: [
            r"personality", r"trait", r"character", r"disposition",
            r"temperament", r"attitude", r"belief", r"value"
        ],
        FacetCategory.BEHAVIORAL: [
            r"behavior", r"action", r"conduct", r"performance",
            r"competence", r"skill", r"ability", r"capability"
        ]
    }
    
    def __init__(self, csv_path: str):
        """Initialize processor with facet CSV file"""
        self.csv_path = Path(csv_path)
        self.raw_facets = []
        self.processed_facets = []
        self.facet_df = None
        
    def load_facets_from_csv(self) -> List[str]:
        """Load facets from CSV file"""
        try:
            # Try reading as simple list
            df = pd.read_csv(self.csv_path, header=None, names=["Facets"])
            self.raw_facets = df["Facets"].dropna().unique().tolist()
            print(f"✓ Loaded {len(self.raw_facets)} facets from CSV")
            return self.raw_facets
        except Exception as e:
            print(f"✗ Error loading CSV: {e}")
            raise
    
    def clean_facet_name(self, name: str) -> str:
        """Clean and standardize facet names"""
        # Remove numbering prefix if exists (e.g., "596. Religious practice")
        name = re.sub(r'^\d+\.\s+', '', str(name).strip())
        # Clean up special characters
        name = re.sub(r'\s+', ' ', name)
        # Remove trailing colons
        name = name.rstrip(':')
        return name.strip()
    
    def categorize_facet(self, name: str) -> FacetCategory:
        """Automatically categorize facet based on name patterns"""
        name_lower = name.lower()
        
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    return category
        
        return FacetCategory.UNKNOWN
    
    def extract_subcategories(self, name: str) -> List[str]:
        """Extract subcategories from facet name if present"""
        # Look for patterns like "Category: Subcategory"
        parts = name.split(':')
        return [part.strip() for part in parts[1:]] if len(parts) > 1 else []
    
    def process_facets(self) -> List[Facet]:
        """Process raw facets into Facet objects"""
        self.processed_facets = []
        
        for idx, raw_name in enumerate(self.raw_facets, 1):
            clean_name = self.clean_facet_name(raw_name)
            if not clean_name:
                continue
            
            category = self.categorize_facet(clean_name)
            subcategories = self.extract_subcategories(clean_name)
            
            facet = Facet(
                id=idx,
                name=clean_name,
                category=category,
                subcategories=subcategories if subcategories else [],
                description=f"Evaluation facet for assessing conversation quality on {category.value}",
                priority=self._determine_priority(category),
                applicable_context="both"
            )
            
            self.processed_facets.append(facet)
        
        print(f"✓ Processed {len(self.processed_facets)} facets")
        return self.processed_facets
    
    def _determine_priority(self, category: FacetCategory) -> str:
        """Determine priority based on category"""
        if category in [FacetCategory.SAFETY, FacetCategory.LINGUISTIC]:
            return "high"
        elif category in [FacetCategory.EMOTION, FacetCategory.PRAGMATIC]:
            return "medium"
        else:
            return "low"
    
    def create_facet_dataframe(self) -> pd.DataFrame:
        """Create DataFrame from processed facets"""
        facet_dicts = [facet.to_dict() for facet in self.processed_facets]
        self.facet_df = pd.DataFrame(facet_dicts)
        
        # Convert enum to string for easier handling
        self.facet_df['category'] = self.facet_df['category'].apply(
            lambda x: x.value if isinstance(x, FacetCategory) else x
        )
        
        # Add additional helper columns
        self.facet_df['subcategory_count'] = self.facet_df['subcategories'].apply(len)
        self.facet_df['is_primary'] = self.facet_df['priority'].apply(lambda x: x == 'high')
        self.facet_df['evaluation_difficulty'] = self.facet_df['category'].apply(
            self._estimate_difficulty
        )
        
        return self.facet_df
    
    def _estimate_difficulty(self, category: str) -> str:
        """Estimate evaluation difficulty for a category"""
        difficulty_map = {
            'safety': 'high',
            'linguistic': 'medium',
            'emotion': 'high',
            'pragmatic': 'medium',
            'cognitive': 'medium',
            'personality': 'high',
            'behavioral': 'low',
            'unknown': 'medium'
        }
        return difficulty_map.get(category, 'medium')
    
    def add_facet_relationships(self) -> pd.DataFrame:
        """Add relationships between related facets"""
        if self.facet_df is None:
            raise ValueError("Must call create_facet_dataframe first")
        
        # Create related facets list based on similar names/categories
        self.facet_df['related_facet_ids'] = self.facet_df.apply(
            lambda row: self._find_related_facets(row, self.facet_df),
            axis=1
        )
        
        return self.facet_df
    
    def _find_related_facets(self, current: pd.Series, df: pd.DataFrame) -> List[int]:
        """Find related facets based on category and name similarity"""
        related = []
        current_id = current['id']
        current_category = current['category']
        current_name = current['name'].lower()
        
        for _, other in df.iterrows():
            if other['id'] == current_id:
                continue
            
            # Same category is a relationship
            if other['category'] == current_category:
                related.append(int(other['id']))
            # Check for name similarity
            elif self._name_similarity(current_name, other['name'].lower()) > 0.6:
                related.append(int(other['id']))
        
        return related[:5]  # Limit to 5 related facets
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Simple jaccard similarity between two names"""
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def save_processed_facets(self, output_path: str):
        """Save processed facets to JSON and CSV"""
        if self.facet_df is None:
            self.create_facet_dataframe()
        
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON (preserves structure)
        json_path = output_dir / "facets_processed.json"
        with open(json_path, 'w') as f:
            json.dump(
                [facet.to_dict() for facet in self.processed_facets],
                f,
                indent=2,
                default=str
            )
        print(f"✓ Saved facets to {json_path}")
        
        # Save as CSV
        csv_path = output_dir / "facets_processed.csv"
        self.facet_df.to_csv(csv_path, index=False)
        print(f"✓ Saved facets to {csv_path}")
        
        # Create facet summary report
        self._create_summary_report(output_dir)
    
    def _create_summary_report(self, output_dir: Path):
        """Create a summary report of facets"""
        summary = {
            'total_facets': len(self.processed_facets),
            'category_distribution': self.facet_df['category'].value_counts().to_dict(),
            'priority_distribution': self.facet_df['priority'].value_counts().to_dict(),
            'difficulty_distribution': self.facet_df['evaluation_difficulty'].value_counts().to_dict(),
            'facets_by_category': {}
        }
        
        for category in self.facet_df['category'].unique():
            cat_facets = self.facet_df[self.facet_df['category'] == category]['name'].tolist()
            summary['facets_by_category'][category] = cat_facets
        
        summary_path = output_dir / "facets_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✓ Created summary report at {summary_path}")
    
    def get_statistics(self) -> Dict:
        """Get statistics about the facet dataset"""
        if self.facet_df is None:
            self.create_facet_dataframe()
        
        return {
            'total_facets': len(self.facet_df),
            'categories': self.facet_df['category'].nunique(),
            'high_priority_count': len(self.facet_df[self.facet_df['priority'] == 'high']),
            'high_difficulty_count': len(self.facet_df[self.facet_df['evaluation_difficulty'] == 'high']),
            'avg_subcategories': self.facet_df['subcategory_count'].mean()
        }

def main():
    """Main execution"""
    import sys
    
    csv_path = "c:/Users/prave/Downloads/OceanAcross/Facets Assignment.csv"
    output_path = "./data"
    
    # Initialize processor
    processor = FacetDataProcessor(csv_path)
    
    # Load and process
    print("Starting facet data preparation...")
    print("-" * 50)
    
    processor.load_facets_from_csv()
    processor.process_facets()
    processor.create_facet_dataframe()
    processor.add_facet_relationships()
    processor.save_processed_facets(output_path)
    
    # Print statistics
    print("\n" + "=" * 50)
    print("Facet Dataset Statistics:")
    print("=" * 50)
    stats = processor.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n✓ Data preparation complete!")

if __name__ == "__main__":
    main()
