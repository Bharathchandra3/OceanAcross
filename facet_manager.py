#!/usr/bin/env python3
"""
Facet Manager - Manages and provides access to evaluation facets
Designed to be scalable to 5000+ facets without architectural changes
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pickle
import hashlib

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

class PriorityLevel(Enum):
    """Priority levels for facets"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3

@dataclass
class FacetDefinition:
    """Represents a single evaluation facet"""
    id: int
    name: str
    category: str
    description: str = ""
    priority: str = "medium"
    data_type: str = "ordinal"
    applicable_context: str = "both"
    related_facet_ids: List[int] = field(default_factory=list)
    evaluation_difficulty: str = "medium"
    subcategories: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'priority': self.priority,
            'data_type': self.data_type,
            'applicable_context': self.applicable_context,
            'related_facet_ids': self.related_facet_ids,
            'evaluation_difficulty': self.evaluation_difficulty
        }

class FacetManager:
    """
    Manages evaluation facets with scalable architecture
    Supports 5000+ facets through:
    - Lazy loading
    - Indexing by multiple attributes
    - Category-based partitioning
    - Caching strategies
    """
    
    def __init__(self, facets_file: str = None):
        """Initialize facet manager"""
        self.facets: Dict[int, FacetDefinition] = {}
        self.facets_by_name: Dict[str, int] = {}
        self.facets_by_category: Dict[str, List[int]] = {}
        self.facets_by_priority: Dict[str, List[int]] = {}
        self.facets_by_difficulty: Dict[str, List[int]] = {}
        
        # Cache for computed relationships
        self._relationship_cache: Dict[int, Set[int]] = {}
        self._category_cache: Dict[str, List[Dict]] = {}
        
        # Statistics
        self.total_facets = 0
        self.categories = set()
        
        if facets_file:
            self.load_facets(facets_file)
    
    def load_facets(self, facets_file: str) -> int:
        """Load facets from JSON file"""
        try:
            with open(facets_file, 'r') as f:
                facets_data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(facets_data, list):
                for facet_dict in facets_data:
                    self.add_facet(FacetDefinition(**facet_dict))
            elif isinstance(facets_data, dict) and 'facets' in facets_data:
                for facet_dict in facets_data['facets']:
                    self.add_facet(FacetDefinition(**facet_dict))
            
            print(f"✓ Loaded {len(self.facets)} facets")
            return len(self.facets)
        except Exception as e:
            print(f"✗ Error loading facets: {e}")
            raise
    
    def add_facet(self, facet: FacetDefinition):
        """Add a facet to the manager"""
        if facet.id in self.facets:
            print(f"Warning: Facet {facet.id} already exists")
            return
        
        self.facets[facet.id] = facet
        self.facets_by_name[facet.name] = facet.id
        
        # Index by category
        if facet.category not in self.facets_by_category:
            self.facets_by_category[facet.category] = []
        self.facets_by_category[facet.category].append(facet.id)
        
        # Index by priority
        if facet.priority not in self.facets_by_priority:
            self.facets_by_priority[facet.priority] = []
        self.facets_by_priority[facet.priority].append(facet.id)
        
        # Index by difficulty
        if facet.evaluation_difficulty not in self.facets_by_difficulty:
            self.facets_by_difficulty[facet.evaluation_difficulty] = []
        self.facets_by_difficulty[facet.evaluation_difficulty].append(facet.id)
        
        self.categories.add(facet.category)
        self.total_facets += 1
    
    def get_facet(self, facet_id: int) -> Optional[FacetDefinition]:
        """Get a facet by ID"""
        return self.facets.get(facet_id)
    
    def get_facet_by_name(self, name: str) -> Optional[FacetDefinition]:
        """Get a facet by name"""
        if name in self.facets_by_name:
            facet_id = self.facets_by_name[name]
            return self.facets.get(facet_id)
        return None
    
    def get_facets_by_category(self, category: str) -> List[FacetDefinition]:
        """Get all facets in a category"""
        if category not in self._category_cache:
            facet_ids = self.facets_by_category.get(category, [])
            self._category_cache[category] = [self.facets[fid].to_dict() for fid in facet_ids]
        
        return [FacetDefinition(**f) for f in self._category_cache[category]]
    
    def get_facets_by_priority(self, priority: str) -> List[FacetDefinition]:
        """Get all facets with specific priority"""
        facet_ids = self.facets_by_priority.get(priority, [])
        return [self.facets[fid] for fid in facet_ids]
    
    def get_facets_by_difficulty(self, difficulty: str) -> List[FacetDefinition]:
        """Get all facets with specific difficulty"""
        facet_ids = self.facets_by_difficulty.get(difficulty, [])
        return [self.facets[fid] for fid in facet_ids]
    
    def get_primary_facets(self) -> List[FacetDefinition]:
        """Get high-priority facets for core evaluation"""
        return self.get_facets_by_priority('high')
    
    def get_evaluation_subset(self, batch_size: int = 50) -> List[FacetDefinition]:
        """Get a balanced subset of facets for efficient evaluation"""
        selected = []
        
        # Include high-priority facets
        high_priority = self.get_facets_by_priority('high')
        selected.extend(high_priority[:int(batch_size * 0.4)])
        
        # Include diverse categories
        for category in self.categories:
            cat_facets = self.get_facets_by_category(category)
            num_to_select = max(1, int(batch_size * 0.6 / len(self.categories)))
            selected.extend(cat_facets[:num_to_select])
        
        # Limit to batch size
        return selected[:batch_size]
    
    def get_related_facets(self, facet_id: int, depth: int = 1) -> Set[int]:
        """Get related facets with optional depth traversal"""
        if facet_id not in self.facets:
            return set()
        
        if facet_id in self._relationship_cache:
            return self._relationship_cache[facet_id]
        
        related = set()
        facet = self.facets[facet_id]
        
        # Add directly related facets
        related.update(facet.related_facet_ids)
        
        # Add facets from same category
        same_category_facets = self.facets_by_category.get(facet.category, [])
        related.update(same_category_facets)
        
        # Remove self
        related.discard(facet_id)
        
        # Cache result
        self._relationship_cache[facet_id] = related
        
        return related
    
    def get_facets_for_context(self, context: str) -> List[FacetDefinition]:
        """Get facets applicable to a specific context"""
        applicable = []
        for facet in self.facets.values():
            if facet.applicable_context == context or facet.applicable_context == 'both':
                applicable.append(facet)
        return applicable
    
    def get_facet_statistics(self) -> Dict:
        """Get comprehensive statistics about facets"""
        stats = {
            'total_facets': self.total_facets,
            'total_categories': len(self.categories),
            'categories': list(self.categories),
            'priority_distribution': {
                priority: len(facet_ids)
                for priority, facet_ids in self.facets_by_priority.items()
            },
            'difficulty_distribution': {
                difficulty: len(facet_ids)
                for difficulty, facet_ids in self.facets_by_difficulty.items()
            },
            'category_distribution': {
                category: len(facet_ids)
                for category, facet_ids in self.facets_by_category.items()
            }
        }
        return stats
    
    def validate_facet_consistency(self) -> Tuple[bool, List[str]]:
        """Validate facet consistency and relationships"""
        errors = []
        
        # Check for orphaned relationships
        for facet_id, facet in self.facets.items():
            for related_id in facet.related_facet_ids:
                if related_id not in self.facets:
                    errors.append(f"Facet {facet_id} references non-existent facet {related_id}")
        
        # Check for missing indices
        for facet_id, facet in self.facets.items():
            if facet_id not in self.facets_by_name.values():
                errors.append(f"Facet {facet_id} ({facet.name}) not indexed by name")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def export_facets(self, output_path: str, format: str = 'json'):
        """Export facets to file"""
        if format == 'json':
            data = {
                'total_facets': self.total_facets,
                'categories': list(self.categories),
                'facets': [facet.to_dict() for facet in self.facets.values()]
            }
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'pickle':
            with open(output_path, 'wb') as f:
                pickle.dump(self.facets, f)
        
        print(f"✓ Exported {self.total_facets} facets to {output_path}")
    
    def get_hash(self) -> str:
        """Get hash of facet configuration for versioning"""
        facet_names = sorted([f.name for f in self.facets.values()])
        content = json.dumps(facet_names).encode()
        return hashlib.md5(content).hexdigest()
    
    def print_summary(self):
        """Print summary of facet manager state"""
        stats = self.get_facet_statistics()
        print("\n" + "=" * 60)
        print("FACET MANAGER SUMMARY")
        print("=" * 60)
        print(f"Total Facets: {stats['total_facets']}")
        print(f"Total Categories: {stats['total_categories']}")
        print(f"\nCategory Distribution:")
        for cat, count in stats['category_distribution'].items():
            print(f"  - {cat}: {count}")
        print(f"\nPriority Distribution:")
        for pri, count in stats['priority_distribution'].items():
            print(f"  - {pri}: {count}")
        print(f"\nDifficulty Distribution:")
        for diff, count in stats['difficulty_distribution'].items():
            print(f"  - {diff}: {count}")
        print("=" * 60)

if __name__ == "__main__":
    # Test initialization
    manager = FacetManager()
    print("✓ FacetManager initialized successfully")
