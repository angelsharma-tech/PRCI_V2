"""
Temporal Utilities for Risk Aggregation

Handles short-term history windowing
for risk assessment.
"""

from typing import List, Any, Optional
from datetime import datetime, timedelta


def recent_window(data: List[Any], window_size: int = 5) -> List[Any]:
    """
    Return the most recent N items from a list.
    
    Args:
        data: List of data items (detection results, risk assessments, etc.)
        window_size: Number of recent items to return
        
    Returns:
        List[Any]: Most recent N items
        
    TODO (Phase-5):
        - Add timestamp-based filtering
        - Implement configurable window types
        - Add data validation
        - Include edge case handling
    """
    if not data:
        return []
    
    # Take last N items
    return data[-window_size:] if window_size > 0 else []


def time_filtered_window(data: List[Any], max_age_days: int = 7, 
                      timestamp_key: str = 'timestamp') -> List[Any]:
    """
    Filter data to include only recent items within time window.
    
    Args:
        data: List of data items with timestamps
        max_age_days: Maximum age in days for items to include
        timestamp_key: Key name for timestamp field in data items
        
    Returns:
        List[Any]: Filtered recent items
        
    TODO (Phase-5):
        - Add flexible timestamp formats
        - Implement timezone handling
        - Add data quality filtering
        - Include performance optimization
    """
    if not data:
        return []
    
    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    
    filtered_data = []
    for item in data:
        # Handle different data types
        if hasattr(item, timestamp_key):
            timestamp = getattr(item, timestamp_key)
        elif isinstance(item, dict) and timestamp_key in item:
            timestamp = item[timestamp_key]
        else:
            # Skip items without valid timestamps
            continue
        
        if timestamp >= cutoff_time:
            filtered_data.append(item)
    
    return filtered_data


def sliding_window(data: List[Any], window_size: int = 5, 
                 step_size: int = 1) -> List[List[Any]]:
    """
    Create sliding windows over data for temporal analysis.
    
    Args:
        data: List of data items
        window_size: Size of each sliding window
        step_size: Number of items to slide between windows
        
    Returns:
        List[List[Any]]: List of sliding windows
        
    TODO (Phase-5):
        - Add variable window sizes
        - Implement overlapping windows
        - Add window validation
        - Include performance optimization
    """
    if not data or window_size <= 0:
        return []
    
    windows = []
    for i in range(0, len(data) - window_size + 1, step_size):
        window = data[i:i + window_size]
        windows.append(window)
    
    return windows


def temporal_trend(data: List[float], window_size: int = 3) -> str:
    """
    Calculate simple trend direction for numeric time series.
    
    Args:
        data: List of numeric values over time
        window_size: Size of window for trend calculation
        
    Returns:
        str: Trend direction ('increasing', 'decreasing', 'stable')
        
    TODO (Phase-5):
        - Implement statistical trend analysis
        - Add confidence scoring for trends
        - Include seasonal pattern detection
        - Add outlier handling
    """
    if len(data) < window_size:
        return "insufficient_data"
    
    # Get recent window
    recent_data = data[-window_size:]
    
    # Calculate trend
    if len(recent_data) < 2:
        return "stable"
    
    # Simple linear trend
    first_half_avg = sum(recent_data[:len(recent_data)//2]) / max(len(recent_data)//2, 1)
    second_half_avg = sum(recent_data[len(recent_data)//2:]) / max(len(recent_data) - len(recent_data)//2, 1)
    
    # Determine trend direction
    if second_half_avg > first_half_avg * 1.1:
        return "increasing"
    elif second_half_avg < first_half_avg * 0.9:
        return "decreasing"
    else:
        return "stable"


def weighted_recency(data: List[Any], weights: Optional[List[float]] = None, 
                  recency_factor: float = 0.1) -> List[float]:
    """
    Apply recency weighting to data items.
    
    Args:
        data: List of data items
        weights: Optional custom weights for each item
        recency_factor: Factor for recency weighting (higher = more weight on recent items)
        
    Returns:
        List[float]: Recency-weighted values
        
    TODO (Phase-5):
        - Add exponential decay weighting
        - Implement custom weighting functions
        - Add time-based weight calculation
        - Include weight normalization
    """
    if not data:
        return []
    
    n = len(data)
    if weights is None:
        # Default recency weights (more recent = higher weight)
        weights = [(i + 1) / n for i in range(n)]
        # Apply recency factor
        weights = [w * (1 + recency_factor * (n - i - 1) / n) for i, w in enumerate(weights)]
    
    # Normalize weights
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights]
    
    return normalized_weights


def temporal_aggregation(data: List[Any], aggregation_func: callable, 
                     time_window: int = 7) -> float:
    """
    Aggregate data over time window using specified function.
    
    Args:
        data: List of data items with timestamps
        aggregation_func: Function to aggregate values (mean, sum, max, etc.)
        time_window: Time window in days
        
    Returns:
        float: Aggregated value over time window
        
    TODO (Phase-5):
        - Add multiple aggregation functions
        - Implement time-based grouping
        - Add missing data handling
        - Include performance optimization
    """
    # Filter recent data
    recent_data = time_filtered_window(data, time_window)
    
    if not recent_data:
        return 0.0
    
    # Extract numeric values (assuming data items have numeric value or can be converted)
    numeric_values = []
    for item in recent_data:
        if isinstance(item, (int, float)):
            numeric_values.append(item)
        elif hasattr(item, 'value'):
            numeric_values.append(float(item.value))
        elif isinstance(item, dict) and 'value' in item:
            numeric_values.append(float(item['value']))
    
    if not numeric_values:
        return 0.0
    
    # Apply aggregation function
    try:
        return aggregation_func(numeric_values)
    except:
        return 0.0


def burst_detection(data: List[Any], threshold: float = 2.0, 
                 window_size: int = 5) -> List[int]:
    """
    Detect bursts or spikes in temporal data.
    
    Args:
        data: List of numeric values over time
        threshold: Multiplier for burst detection (threshold * average)
        window_size: Window size for local average calculation
        
    Returns:
        List[int]: Indices where bursts are detected
        
    TODO (Phase-5):
        - Implement adaptive thresholding
        - Add statistical burst detection
        - Include burst intensity scoring
        - Add burst duration analysis
    """
    if len(data) < window_size:
        return []
    
    burst_indices = []
    
    for i in range(window_size, len(data)):
        # Calculate local average in window
        window_start = i - window_size
        local_avg = sum(data[window_start:i]) / window_size
        
        # Check if current value exceeds threshold * local average
        if data[i] > threshold * local_avg:
            burst_indices.append(i)
    
    return burst_indices


def periodicity_analysis(data: List[Any], period_length: int = 7) -> Dict[str, Any]:
    """
    Analyze periodic patterns in temporal data.
    
    Args:
        data: List of data items with timestamps
        period_length: Expected period length in days
        
    Returns:
        Dict[str, Any]: Periodicity analysis results
        
    TODO (Phase-5):
        - Implement autocorrelation analysis
        - Add seasonal pattern detection
        - Include period length optimization
        - Add confidence scoring for periodicity
    """
    if len(data) < period_length * 2:
        return {
            "periodic": False,
            "confidence": 0.0,
            "period_length": None
        }
    
    # Simple periodicity check (placeholder implementation)
    # In a real implementation, this would use more sophisticated time series analysis
    
    return {
        "periodic": False,  # Placeholder
        "confidence": 0.0,
        "period_length": period_length
    }


def time_since_last(data: List[Any], timestamp_key: str = 'timestamp', 
                  reference_time: Optional[datetime] = None) -> float:
    """
    Calculate time since last occurrence.
    
    Args:
        data: List of data items with timestamps
        timestamp_key: Key name for timestamp field
        reference_time: Reference time (default: current time)
        
    Returns:
        float: Hours since last occurrence
        
    TODO (Phase-5):
        - Add timezone handling
        - Implement different time units
        - Add missing data handling
        - Include reference time validation
    """
    if not data:
        return float('inf')
    
    if reference_time is None:
        reference_time = datetime.now()
    
    # Find most recent item
    most_recent = None
    most_recent_time = None
    
    for item in data:
        if hasattr(item, timestamp_key):
            timestamp = getattr(item, timestamp_key)
        elif isinstance(item, dict) and timestamp_key in item:
            timestamp = item[timestamp_key]
        else:
            continue
        
        if most_recent_time is None or timestamp > most_recent_time:
            most_recent_time = timestamp
            most_recent = item
    
    if most_recent_time is None:
        return float('inf')
    
    # Calculate time difference
    time_diff = reference_time - most_recent_time
    return time_diff.total_seconds() / 3600.0  # Convert to hours


def temporal_smoothing(data: List[float], smoothing_factor: float = 0.3) -> List[float]:
    """
    Apply exponential smoothing to temporal data.
    
    Args:
        data: List of numeric values over time
        smoothing_factor: Smoothing factor (0.0-1.0, lower = more smoothing)
        
    Returns:
        List[float]: Smoothed values
        
    TODO (Phase-5):
        - Add adaptive smoothing factors
        - Implement different smoothing methods
        - Add trend-preserving smoothing
        - Include parameter optimization
    """
    if not data:
        return []
    
    smoothed = []
    alpha = smoothing_factor
    
    # Initialize with first value
    if len(data) > 0:
        smoothed.append(data[0])
    
    # Apply exponential smoothing
    for i in range(1, len(data)):
        smoothed_value = alpha * data[i] + (1 - alpha) * smoothed[-1]
        smoothed.append(smoothed_value)
    
    return smoothed
