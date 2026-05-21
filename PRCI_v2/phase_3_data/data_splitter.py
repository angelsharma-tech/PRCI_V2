"""
Data Splitting Utility

Splits cleaned datasets into
train/validation/test sets.

Actual ratios can be adjusted
in Phase-4 if required.
"""

import random
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class DataSplitter:
    """
    Data splitting utility for creating train/validation/test splits.
    
    This class provides methods to split datasets while maintaining
    data integrity and supporting various splitting strategies
    appropriate for machine learning model development.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the data splitter.
        
        Args:
            config: Configuration dictionary for splitting parameters
        """
        self.config = config or {}
        self.random_seed = self.config.get('random_seed', 42)
        self.stratify_field = self.config.get('stratify_field', None)
        self.temporal_field = self.config.get('temporal_field', 'processing_timestamp')
        
        # Set random seed for reproducibility
        random.seed(self.random_seed)
    
    def split(self, data: List[Any], train_ratio: float = 0.7, 
              val_ratio: float = 0.15, test_ratio: float = 0.15) -> Dict[str, List[Any]]:
        """
        Basic random split of dataset.
        
        Args:
            data: List of data items to split
            train_ratio: Proportion for training set
            val_ratio: Proportion for validation set
            test_ratio: Proportion for test set
            
        Returns:
            Dict: Dictionary with train, validation, and test splits
            
        TODO (Phase-3):
        - Add input validation for ratios
        - Implement stratified splitting
        - Add temporal splitting option
        """
        # Validate ratios
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
            raise ValueError("Split ratios must sum to 1.0")
        
        # Create a copy and shuffle
        shuffled_data = data.copy()
        random.shuffle(shuffled_data)
        
        n = len(shuffled_data)
        
        # Calculate split points
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        # Create splits
        splits = {
            "train": shuffled_data[:train_end],
            "validation": shuffled_data[train_end:val_end],
            "test": shuffled_data[val_end:]
        }
        
        return splits
    
    def stratified_split(self, data: List[Dict[str, Any]], 
                       label_field: str = 'label',
                       train_ratio: float = 0.7,
                       val_ratio: float = 0.15,
                       test_ratio: float = 0.15) -> Dict[str, List[Dict[str, Any]]]:
        """
        Stratified split maintaining label distribution.
        
        Args:
            data: List of dataset entries with labels
            label_field: Field name containing labels
            train_ratio: Proportion for training set
            val_ratio: Proportion for validation set
            test_ratio: Proportion for test set
            
        Returns:
            Dict: Dictionary with stratified splits
            
        TODO (Phase-3):
        - Add support for multi-label stratification
        - Implement custom stratification strategies
        - Add handling for rare labels
        """
        # Group data by labels
        label_groups = {}
        for item in data:
            label = item.get(label_field, 'unknown')
            if label not in label_groups:
                label_groups[label] = []
            label_groups[label].append(item)
        
        # Split each group
        splits = {"train": [], "validation": [], "test": []}
        
        for label, group in label_groups.items():
            group_splits = self.split(group, train_ratio, val_ratio, test_ratio)
            splits["train"].extend(group_splits["train"])
            splits["validation"].extend(group_splits["validation"])
            splits["test"].extend(group_splits["test"])
        
        # Shuffle final splits
        for split_name in splits:
            random.shuffle(splits[split_name])
        
        return splits
    
    def temporal_split(self, data: List[Dict[str, Any]], 
                     time_field: str = 'processing_timestamp',
                     train_ratio: float = 0.7,
                     val_ratio: float = 0.15,
                     test_ratio: float = 0.15) -> Dict[str, List[Dict[str, Any]]]:
        """
        Temporal split based on timestamps.
        
        Args:
            data: List of dataset entries with timestamps
            time_field: Field name containing timestamps
            train_ratio: Proportion for training set
            val_ratio: Proportion for validation set
            test_ratio: Proportion for test set
            
        Returns:
            Dict: Dictionary with temporally ordered splits
            
        TODO (Phase-3):
        - Add support for different timestamp formats
        - Implement sliding window temporal splits
            - Add temporal gap options
        """
        # Sort data by timestamp
        try:
            sorted_data = sorted(data, key=lambda x: self._parse_timestamp(x.get(time_field, '')))
        except Exception as e:
            print(f"Error sorting by timestamp: {e}")
            # Fall back to random split
            return self.split(data, train_ratio, val_ratio, test_ratio)
        
        n = len(sorted_data)
        
        # Calculate split points
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        # Create splits maintaining temporal order
        splits = {
            "train": sorted_data[:train_end],
            "validation": sorted_data[train_end:val_end],
            "test": sorted_data[val_end:]
        }
        
        return splits
    
    def user_based_split(self, data: List[Dict[str, Any]], 
                        user_field: str = 'user_id',
                        train_ratio: float = 0.7,
                        val_ratio: float = 0.15,
                        test_ratio: float = 0.15) -> Dict[str, List[Dict[str, Any]]]:
        """
        Split data by users to prevent data leakage.
        
        Args:
            data: List of dataset entries with user IDs
            user_field: Field name containing user IDs
            train_ratio: Proportion for training set
            val_ratio: Proportion for validation set
            test_ratio: Proportion for test set
            
        Returns:
            Dict: Dictionary with user-based splits
            
        TODO (Phase-3):
        - Add support for user group stratification
        - Implement minimum user count requirements
        - Add user activity level considerations
        """
        # Group data by users
        user_groups = {}
        for item in data:
            user_id = item.get(user_field, 'unknown')
            if user_id not in user_groups:
                user_groups[user_id] = []
            user_groups[user_id].append(item)
        
        # Split users (not individual entries)
        user_ids = list(user_groups.keys())
        random.shuffle(user_ids)
        
        n_users = len(user_ids)
        train_end = int(n_users * train_ratio)
        val_end = int(n_users * (train_ratio + val_ratio))
        
        # Create splits
        splits = {"train": [], "validation": [], "test": []}
        
        for i, user_id in enumerate(user_ids):
            user_data = user_groups[user_id]
            if i < train_end:
                splits["train"].extend(user_data)
            elif i < val_end:
                splits["validation"].extend(user_data)
            else:
                splits["test"].extend(user_data)
        
        # Shuffle final splits
        for split_name in splits:
            random.shuffle(splits[split_name])
        
        return splits
    
    def cross_validation_split(self, data: List[Any], 
                              k_folds: int = 5) -> List[Tuple[List[Any], List[Any]]]:
        """
        Create k-fold cross-validation splits.
        
        Args:
            data: List of data items to split
            k_folds: Number of folds for cross-validation
            
        Returns:
            List of tuples: Each tuple contains (train_data, val_data) for a fold
            
        TODO (Phase-3):
        - Add stratified cross-validation
        - Implement temporal cross-validation
        - Add custom fold size options
        """
        if k_folds < 2:
            raise ValueError("Number of folds must be at least 2")
        
        # Shuffle data
        shuffled_data = data.copy()
        random.shuffle(shuffled_data)
        
        # Calculate fold size
        n = len(shuffled_data)
        fold_size = n // k_folds
        remainder = n % k_folds
        
        # Create folds
        folds = []
        start = 0
        for i in range(k_folds):
            end = start + fold_size + (1 if i < remainder else 0)
            folds.append(shuffled_data[start:end])
            start = end
        
        # Create cross-validation splits
        cv_splits = []
        for i in range(k_folds):
            val_data = folds[i]
            train_data = []
            for j, fold in enumerate(folds):
                if j != i:
                    train_data.extend(fold)
            cv_splits.append((train_data, val_data))
        
        return cv_splits
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse timestamp string to datetime object.
        
        Args:
            timestamp_str: Timestamp string to parse
            
        Returns:
            datetime: Parsed datetime object
            
        TODO (Phase-3):
        - Add support for more timestamp formats
        - Implement timezone handling
        - Add error handling for invalid timestamps
        """
        if not timestamp_str:
            return datetime.min
        
        # Try common timestamp formats
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y%m%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # If all formats fail, return minimum datetime
        return datetime.min
    
    def get_split_statistics(self, splits: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Get statistics about the data splits.
        
        Args:
            splits: Dictionary containing data splits
            
        Returns:
            Dict: Statistics about each split
            
        TODO (Phase-3):
        - Add label distribution statistics
        - Implement temporal range statistics
        - Add user overlap analysis
        """
        stats = {}
        
        for split_name, split_data in splits.items():
            split_stats = {
                'count': len(split_data),
                'percentage': len(split_data) / sum(len(s) for s in splits.values()) * 100
            }
            
            # Add label distribution if available
            if split_data and isinstance(split_data[0], dict) and 'label' in split_data[0]:
                label_counts = {}
                for item in split_data:
                    label = item.get('label', 'unknown')
                    label_counts[label] = label_counts.get(label, 0) + 1
                split_stats['label_distribution'] = label_counts
            
            # Add user count if available
            if split_data and isinstance(split_data[0], dict) and 'user_id' in split_data[0]:
                users = set(item.get('user_id', 'unknown') for item in split_data)
                split_stats['unique_users'] = len(users)
            
            stats[split_name] = split_stats
        
        return stats
    
    def save_splits(self, splits: Dict[str, List[Any]], 
                   base_path: str, format: str = 'json') -> bool:
        """
        Save data splits to files.
        
        Args:
            splits: Dictionary containing data splits
            base_path: Base path for saving files (without extension)
            format: File format ('json' or 'csv')
            
        Returns:
            bool: True if save successful
            
        TODO (Phase-3):
        - Add compression options
        - Implement incremental saving
        - Add save validation
        """
        try:
            for split_name, split_data in splits.items():
                filepath = f"{base_path}_{split_name}.{format}"
                
                if format.lower() == 'json':
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(split_data, f, indent=2, ensure_ascii=False)
                
                elif format.lower() == 'csv':
                    if not split_data:
                        continue
                    
                    # Get all possible fields
                    if isinstance(split_data[0], dict):
                        fieldnames = set()
                        for item in split_data:
                            fieldnames.update(item.keys())
                        fieldnames = sorted(list(fieldnames))
                        
                        with open(filepath, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(split_data)
                    else:
                        # For simple data, save as single column
                        with open(filepath, 'w', encoding='utf-8') as f:
                            for item in split_data:
                                f.write(f"{item}\n")
                
                else:
                    raise ValueError(f"Unsupported format: {format}")
            
            return True
            
        except Exception as e:
            print(f"Error saving splits: {e}")
            return False
    
    def load_splits(self, base_path: str, format: str = 'json') -> Dict[str, List[Any]]:
        """
        Load data splits from files.
        
        Args:
            base_path: Base path for loading files (without extension)
            format: File format ('json' or 'csv')
            
        Returns:
            Dict: Dictionary containing loaded splits
            
        TODO (Phase-3):
        - Add format auto-detection
        - Implement partial loading for large files
        - Add loading validation
        """
        splits = {}
        split_names = ['train', 'validation', 'test']
        
        for split_name in split_names:
            filepath = f"{base_path}_{split_name}.{format}"
            
            try:
                if format.lower() == 'json':
                    with open(filepath, 'r', encoding='utf-8') as f:
                        splits[split_name] = json.load(f)
                
                elif format.lower() == 'csv':
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        splits[split_name] = list(reader)
                
                else:
                    raise ValueError(f"Unsupported format: {format}")
                    
            except FileNotFoundError:
                print(f"Warning: Split file not found: {filepath}")
                splits[split_name] = []
            
        return splits
    
    def validate_splits(self, splits: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Validate data splits for common issues.
        
        Args:
            splits: Dictionary containing data splits
            
        Returns:
            Dict: Validation results
            
        TODO (Phase-3):
        - Add comprehensive validation checks
        - Implement data leakage detection
        - Add statistical significance testing
        """
        validation_results = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'statistics': self.get_split_statistics(splits)
        }
        
        # Check for empty splits
        for split_name, split_data in splits.items():
            if not split_data:
                validation_results['issues'].append(f"Empty split: {split_name}")
                validation_results['valid'] = False
        
        # Check for data leakage (same items in multiple splits)
        all_items = []
        for split_name, split_data in splits.items():
            for item in split_data:
                # Create a hashable representation
                if isinstance(item, dict):
                    item_hash = hash(str(sorted(item.items())))
                else:
                    item_hash = hash(str(item))
                
                if item_hash in all_items:
                    validation_results['issues'].append("Data leakage detected: same item in multiple splits")
                    validation_results['valid'] = False
                    break
                
                all_items.append(item_hash)
        
        # Check split ratios
        total_items = sum(len(split) for split in splits.values())
        if total_items > 0:
            for split_name, split_data in splits.items():
                ratio = len(split_data) / total_items
                if split_name == 'train' and ratio < 0.5:
                    validation_results['warnings'].append(f"Small training set: {ratio:.2%}")
                elif split_name in ['validation', 'test'] and ratio < 0.1:
                    validation_results['warnings'].append(f"Small {split_name} set: {ratio:.2%}")
        
        return validation_results
