"""
Dataset Builder for PRCI v2.0

Transforms raw text inputs into cleaned
datasets ready for model consumption
in later phases.
"""

import json
import csv
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from text_cleaner import TextCleaner


class DatasetBuilder:
    """
    Dataset building and management class.
    
    This class transforms raw user-generated text into structured,
    cleaned datasets suitable for machine learning model development
    in procrastination prediction and intervention systems.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the dataset builder.
        
        Args:
            config: Configuration dictionary for dataset building
        """
        self.config = config or {}
        self.cleaner = TextCleaner(self.config.get('cleaning_config', {}))
        self.metadata_fields = self.config.get('metadata_fields', [
            'timestamp', 'user_id', 'context', 'source'
        ])
        self.quality_threshold = self.config.get('quality_threshold', 0.3)
        
        # Dataset statistics
        self.stats = {
            'total_processed': 0,
            'passed_quality': 0,
            'failed_quality': 0,
            'average_length': 0,
            'processing_errors': 0
        }
    
    def build_single(self, raw_text: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Build a single processed dataset entry.
        
        Args:
            raw_text: Raw user text input
            metadata: Additional metadata about the text
            
        Returns:
            Dict or None: Processed dataset entry or None if quality too low
            
        TODO (Phase-3):
        - Add more sophisticated quality assessment
        - Implement content validation checks
        - Add metadata enrichment
        """
        try:
            # Clean the text
            cleaned_text = self.cleaner.clean(raw_text)
            
            # Get cleaning statistics
            cleaning_stats = self.cleaner.get_cleaning_stats(raw_text, cleaned_text)
            
            # Quality assessment
            quality_score = self._assess_quality(cleaned_text, cleaning_stats)
            
            # Check if quality meets threshold
            if quality_score < self.quality_threshold:
                self.stats['failed_quality'] += 1
                return None
            
            # Build dataset entry
            entry = {
                'raw_text': raw_text,
                'cleaned_text': cleaned_text,
                'quality_score': quality_score,
                'cleaning_stats': cleaning_stats,
                'processing_timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Add metadata fields
            for field in self.metadata_fields:
                if field in (metadata or {}):
                    entry[field] = metadata[field]
            
            self.stats['passed_quality'] += 1
            return entry
            
        except Exception as e:
            self.stats['processing_errors'] += 1
            print(f"Error processing text: {e}")
            return None
    
    def build(self, texts: List[str], metadata_list: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Apply cleaning pipeline to a list of raw text samples.
        
        Args:
            texts: List of raw text strings
            metadata_list: List of metadata dictionaries (optional)
            
        Returns:
            List[Dict]: List of processed dataset entries
            
        TODO (Phase-3):
        - Add parallel processing for large datasets
        - Implement progress tracking and logging
        - Add batch quality reporting
        """
        processed_entries = []
        
        # Ensure metadata list matches texts length
        if metadata_list is None:
            metadata_list = [{}] * len(texts)
        elif len(metadata_list) != len(texts):
            # Pad or truncate metadata list
            if len(metadata_list) < len(texts):
                metadata_list.extend([{}] * (len(texts) - len(metadata_list)))
            else:
                metadata_list = metadata_list[:len(texts)]
        
        for i, text in enumerate(texts):
            metadata = metadata_list[i] if i < len(metadata_list) else {}
            entry = self.build_single(text, metadata)
            
            if entry:
                processed_entries.append(entry)
            
            self.stats['total_processed'] += 1
        
        # Update average length
        if processed_entries:
            total_length = sum(len(entry['cleaned_text']) for entry in processed_entries)
            self.stats['average_length'] = total_length / len(processed_entries)
        
        return processed_entries
    
    def _assess_quality(self, cleaned_text: str, cleaning_stats: Dict[str, Any]) -> float:
        """
        Assess the quality of cleaned text.
        
        Args:
            cleaned_text: The cleaned text
            cleaning_stats: Statistics from the cleaning process
            
        Returns:
            float: Quality score between 0 and 1
            
        TODO (Phase-3):
        - Implement more sophisticated quality metrics
        - Add content relevance scoring
        - Consider academic context quality factors
        """
        if not cleaned_text:
            return 0.0
        
        quality_score = 0.0
        
        # Length component (prefer reasonable length)
        word_count = len(cleaned_text.split())
        if 5 <= word_count <= 100:
            length_score = 1.0
        elif word_count < 5:
            length_score = word_count / 5.0
        else:
            length_score = max(0.5, 100.0 / word_count)
        
        # Preservation component (not too much content lost)
        preservation_rate = cleaning_stats.get('preservation_rate', 0)
        preservation_score = min(1.0, preservation_rate * 1.2)  # Allow some loss
        
        # Content diversity component
        unique_words = len(set(cleaned_text.split()))
        diversity_score = min(1.0, unique_words / max(word_count, 1))
        
        # Combine scores with weights
        quality_score = (
            length_score * 0.4 +
            preservation_score * 0.4 +
            diversity_score * 0.2
        )
        
        return min(1.0, quality_score)
    
    def filter_by_quality(self, dataset: List[Dict[str, Any]], 
                         min_quality: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Filter dataset entries by quality score.
        
        Args:
            dataset: List of dataset entries
            min_quality: Minimum quality score (uses instance threshold if None)
            
        Returns:
            List[Dict]: Filtered dataset entries
            
        TODO (Phase-3):
        - Add more sophisticated filtering criteria
        - Implement content-based filtering
        - Add metadata-based filtering options
        """
        threshold = min_quality if min_quality is not None else self.quality_threshold
        return [entry for entry in dataset if entry.get('quality_score', 0) >= threshold]
    
    def add_labels(self, dataset: List[Dict[str, Any]], 
                   labels: List[Any], label_name: str = 'label') -> List[Dict[str, Any]]:
        """
        Add labels to dataset entries.
        
        Args:
            dataset: List of dataset entries
            labels: List of labels corresponding to entries
            label_name: Name for the label field
            
        Returns:
            List[Dict]: Dataset entries with labels added
            
        TODO (Phase-3):
        - Add label validation
        - Implement multi-label support
        - Add label encoding options
        """
        if len(labels) != len(dataset):
            raise ValueError("Number of labels must match number of dataset entries")
        
        labeled_dataset = []
        for entry, label in zip(dataset, labels):
            labeled_entry = entry.copy()
            labeled_entry[label_name] = label
            labeled_dataset.append(labeled_entry)
        
        return labeled_dataset
    
    def split_by_context(self, dataset: List[Dict[str, Any]], 
                        context_field: str = 'context') -> Dict[str, List[Dict[str, Any]]]:
        """
        Split dataset by context field.
        
        Args:
            dataset: List of dataset entries
            context_field: Field name to split by
            
        Returns:
            Dict: Dataset entries grouped by context
            
        TODO (Phase-3):
        - Add more flexible grouping options
        - Implement hierarchical splitting
        - Add context validation
        """
        grouped = {}
        
        for entry in dataset:
            context = entry.get('metadata', {}).get(context_field, 'unknown')
            if context not in grouped:
                grouped[context] = []
            grouped[context].append(entry)
        
        return grouped
    
    def export_to_json(self, dataset: List[Dict[str, Any]], filepath: str) -> bool:
        """
        Export dataset to JSON file.
        
        Args:
            dataset: Dataset to export
            filepath: Output file path
            
        Returns:
            bool: True if export successful
            
        TODO (Phase-3):
        - Add compression options
        - Implement incremental export
        - Add export validation
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def export_to_csv(self, dataset: List[Dict[str, Any]], filepath: str) -> bool:
        """
        Export dataset to CSV file.
        
        Args:
            dataset: Dataset to export
            filepath: Output file path
            
        Returns:
            bool: True if export successful
            
        TODO (Phase-3):
        - Add custom delimiter options
        - Implement header customization
        - Add data type handling
        """
        if not dataset:
            return False
        
        try:
            # Get all possible fields from all entries
            all_fields = set()
            for entry in dataset:
                all_fields.update(entry.keys())
                if isinstance(entry.get('metadata'), dict):
                    all_fields.update(f"metadata_{k}" for k in entry['metadata'].keys())
            
            fieldnames = sorted(list(all_fields))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for entry in dataset:
                    # Flatten nested structures
                    flat_entry = {}
                    for field in fieldnames:
                        if field.startswith('metadata_'):
                            meta_field = field[9:]  # Remove 'metadata_' prefix
                            flat_entry[field] = entry.get('metadata', {}).get(meta_field, '')
                        else:
                            value = entry.get(field, '')
                            # Handle complex objects
                            if isinstance(value, (dict, list)):
                                flat_entry[field] = json.dumps(value)
                            else:
                                flat_entry[field] = value
                    
                    writer.writerow(flat_entry)
            
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get dataset building statistics.
        
        Returns:
            Dict: Processing statistics
            
        TODO (Phase-3):
        - Add more detailed statistics
        - Implement quality distribution analysis
        - Add processing time tracking
        """
        return {
            'processing_stats': self.stats.copy(),
            'quality_threshold': self.quality_threshold,
            'success_rate': self.stats['passed_quality'] / max(self.stats['total_processed'], 1),
            'average_quality': self.stats.get('average_quality', 0)
        }
    
    def reset_statistics(self) -> None:
        """
        Reset processing statistics.
        
        TODO (Phase-3):
        - Add statistics persistence
        - Implement statistics export
        """
        self.stats = {
            'total_processed': 0,
            'passed_quality': 0,
            'failed_quality': 0,
            'average_length': 0,
            'processing_errors': 0
        }
    
    def validate_dataset(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate dataset integrity and quality.
        
        Args:
            dataset: Dataset to validate
            
        Returns:
            Dict: Validation results
            
        TODO (Phase-3):
        - Add comprehensive validation checks
        - Implement data integrity verification
        - Add quality distribution analysis
        """
        validation_results = {
            'total_entries': len(dataset),
            'valid_entries': 0,
            'issues': [],
            'quality_distribution': {},
            'missing_fields': set()
        }
        
        required_fields = ['raw_text', 'cleaned_text', 'quality_score']
        
        for entry in dataset:
            is_valid = True
            
            # Check required fields
            for field in required_fields:
                if field not in entry:
                    validation_results['missing_fields'].add(field)
                    is_valid = False
            
            # Check quality score range
            if 'quality_score' in entry:
                score = entry['quality_score']
                if not isinstance(score, (int, float)) or score < 0 or score > 1:
                    validation_results['issues'].append(f"Invalid quality score: {score}")
                    is_valid = False
            
            if is_valid:
                validation_results['valid_entries'] += 1
        
        # Calculate quality distribution
        quality_scores = [entry.get('quality_score', 0) for entry in dataset]
        if quality_scores:
            validation_results['quality_distribution'] = {
                'min': min(quality_scores),
                'max': max(quality_scores),
                'mean': sum(quality_scores) / len(quality_scores),
                'median': sorted(quality_scores)[len(quality_scores) // 2]
            }
        
        return validation_results
