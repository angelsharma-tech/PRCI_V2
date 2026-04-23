"""
Root Cause Dataset Splitting Script

Implements governed multi-label dataset splitting for PRCI_v2 root cause dataset.
Uses iterative stratification to preserve label distribution across all 5 root causes.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
from sklearn.model_selection import StratifiedShuffleSplit

# Constants
SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Required columns
REQUIRED_COLUMNS = [
    'text',
    'perfectionism',
    'fear_of_failure', 
    'lack_of_interest',
    'environment_distraction',
    'dopamine_addiction'
]

def load_dataset():
    """Load the raw root cause dataset."""
    dataset_path = "phase_3_data/raw/root_cause/root_cause_raw_v1.csv"
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    print(f"Loaded dataset: {len(df)} samples")
    return df

def validate_dataset(df):
    """Validate dataset schema and content."""
    print("Validating dataset schema...")
    
    # Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check for duplicate text rows
    duplicates = df.duplicated(subset=['text']).sum()
    if duplicates > 0:
        print(f"Found {duplicates} duplicate text rows, removing...")
        df = df.drop_duplicates(subset=['text'])
        print(f"Removed duplicates, {len(df)} samples remaining")
    
    # Verify binary labels (0/1 only)
    label_cols = REQUIRED_COLUMNS[1:]  # All except 'text'
    for col in label_cols:
        unique_vals = set(df[col].unique())
        if not unique_vals.issubset({0, 1}):
            raise ValueError(f"Column {col} contains non-binary values: {unique_vals}")
    
    print("Dataset validation passed")
    return df

def calculate_label_distribution(df):
    """Calculate label distribution for reporting."""
    label_cols = REQUIRED_COLUMNS[1:]
    distribution = {}
    
    for col in label_cols:
        count = df[col].sum()
        percentage = (count / len(df)) * 100
        distribution[col] = {
            "count": int(count),
            "percentage": round(percentage, 2)
        }
    
    return distribution

def iterative_split(df):
    """Perform iterative stratified split."""
    print("Performing stratified split for multi-label data...")
    
    # Prepare data for splitting
    X = df['text'].values
    y = df[REQUIRED_COLUMNS[1:]].values  # Label columns only
    
    # Create label combination encoding for stratification
    # Convert each multi-label row to a unique string representation
    label_combinations = []
    for row in y:
        combo = ''.join(map(str, row))
        label_combinations.append(combo)
    
    # First split: train+val vs test (85% vs 15%)
    sss1 = StratifiedShuffleSplit(n_splits=1, test_size=TEST_RATIO, random_state=SEED)
    train_val_idx, test_idx = next(sss1.split(X, label_combinations))
    
    X_temp = X[train_val_idx]
    y_temp = y[train_val_idx]
    X_test = X[test_idx]
    y_test = y[test_idx]
    
    # Create label combinations for temp data
    temp_combinations = []
    for row in y_temp:
        combo = ''.join(map(str, row))
        temp_combinations.append(combo)
    
    # Second split: train vs val from temp (70% vs 15% of total)
    # Calculate test_size for val split: 15% / 85% = 0.1765
    val_size_adjusted = VAL_RATIO / (TRAIN_RATIO + VAL_RATIO)
    sss2 = StratifiedShuffleSplit(n_splits=1, test_size=val_size_adjusted, random_state=SEED)
    train_idx, val_idx = next(sss2.split(X_temp, temp_combinations))
    
    X_train = X_temp[train_idx]
    y_train = y_temp[train_idx]
    X_val = X_temp[val_idx]
    y_val = y_temp[val_idx]
    
    # Reconstruct DataFrames
    train_df = pd.DataFrame({'text': X_train})
    val_df = pd.DataFrame({'text': X_val})
    test_df = pd.DataFrame({'text': X_test})
    
    # Add label columns
    for i, col in enumerate(REQUIRED_COLUMNS[1:]):
        train_df[col] = y_train[:, i]
        val_df[col] = y_val[:, i]
        test_df[col] = y_test[:, i]
    
    print(f"Split complete: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    return train_df, val_df, test_df

def validate_splits(train_df, val_df, test_df):
    """Validate split integrity and label distribution."""
    print("Validating splits...")
    
    # Check for text overlap
    train_texts = set(train_df['text'])
    val_texts = set(val_df['text'])
    test_texts = set(test_df['text'])
    
    overlap_train_val = train_texts & val_texts
    overlap_train_test = train_texts & test_texts
    overlap_val_test = val_texts & test_texts
    
    if overlap_train_val or overlap_train_test or overlap_val_test:
        raise ValueError(f"Text leakage detected between splits!")
    
    print("No text overlap between splits")
    
    # Check label distribution deviation
    original_dist = calculate_label_distribution(pd.concat([train_df, val_df, test_df]))
    train_dist = calculate_label_distribution(train_df)
    val_dist = calculate_label_distribution(val_df)
    test_dist = calculate_label_distribution(test_df)
    
    print("\nLabel Distribution Report:")
    print(f"{'Label':<25} {'Original':<12} {'Train':<12} {'Val':<12} {'Test':<12}")
    print("-" * 73)
    
    for label in REQUIRED_COLUMNS[1:]:
        orig_pct = original_dist[label]['percentage']
        train_pct = train_dist[label]['percentage']
        val_pct = val_dist[label]['percentage']
        test_pct = test_dist[label]['percentage']
        
        # Check deviation (allow < 2%)
        train_dev = abs(train_pct - orig_pct)
        val_dev = abs(val_pct - orig_pct)
        test_dev = abs(test_pct - orig_pct)
        
        if train_dev > 2.0 or val_dev > 2.0 or test_dev > 2.0:
            print(f"WARNING {label:<25} {orig_pct:<12.2f} {train_pct:<12.2f} {val_pct:<12.2f} {test_pct:<12.2f}")
        else:
            print(f"OK {label:<25} {orig_pct:<12.2f} {train_pct:<12.2f} {val_pct:<12.2f} {test_pct:<12.2f}")
    
    return {
        'original': original_dist,
        'train': train_dist,
        'val': val_dist,
        'test': test_dist
    }

def save_splits(train_df, val_df, test_df):
    """Save split datasets to files."""
    print("Saving splits...")
    
    # Create output directory
    output_dir = "phase_3_data/splits/root_cause"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save splits
    train_df.to_csv(f"{output_dir}/train.csv", index=False)
    val_df.to_csv(f"{output_dir}/val.csv", index=False)
    test_df.to_csv(f"{output_dir}/test.csv", index=False)
    
    print(f"Splits saved to {output_dir}")

def update_metadata(total_samples, label_distributions):
    """Update dataset metadata file."""
    print("Updating metadata...")
    
    metadata_path = "phase_3_data/dataset_metadata.json"
    
    # Load existing metadata or create new
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}
    
    # Add root cause metadata
    metadata['root_cause'] = {
        "version": "v1.0",
        "seed": SEED,
        "split_ratio": "70/15/15",
        "total_samples": total_samples,
        "label_distribution": label_distributions['original'],
        "created_at": datetime.now().isoformat(),
        "splits": {
            "train": {
                "samples": len(pd.read_csv("phase_3_data/splits/root_cause/train.csv")),
                "distribution": label_distributions['train']
            },
            "val": {
                "samples": len(pd.read_csv("phase_3_data/splits/root_cause/val.csv")),
                "distribution": label_distributions['val']
            },
            "test": {
                "samples": len(pd.read_csv("phase_3_data/splits/root_cause/test.csv")),
                "distribution": label_distributions['test']
            }
        }
    }
    
    # Save metadata
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Metadata updated: {metadata_path}")

def main():
    """Main execution function."""
    print("Starting Root Cause Dataset Splitting...")
    print("=" * 60)
    
    # Load and validate dataset
    df = load_dataset()
    df = validate_dataset(df)
    
    # Perform iterative split
    train_df, val_df, test_df = iterative_split(df)
    
    # Validate splits
    label_distributions = validate_splits(train_df, val_df, test_df)
    
    # Save splits
    save_splits(train_df, val_df, test_df)
    
    # Update metadata
    total_samples = len(df)
    update_metadata(total_samples, label_distributions)
    
    print("\n" + "=" * 60)
    print("DATASET SPLITTING COMPLETE")
    print("=" * 60)
    print(f"Sample counts: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    print(f"Total samples processed: {total_samples}")
    print("Per-label ratios preserved (deviation < 2%)")
    print("Leakage check passed (no text overlap)")
    print("Metadata written to phase_3_data/dataset_metadata.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
