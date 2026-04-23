"""
Feature Extraction Module for PRCI v2.0

Converts cleaned text into numerical
representations for classical ML models.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import Normalizer
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
import pickle
import os


class FeatureExtractor:
    """
    Feature extraction class for text data processing.
    
    This class provides multiple text representation methods
    suitable for classical machine learning models while
    maintaining interpretability and academic relevance.
    """
    
    def __init__(self, max_features: int = 5000, method: str = "tfidf"):
        """
        Initialize the feature extractor.
        
        Args:
            max_features: Maximum number of features to extract
            method: Feature extraction method ('tfidf', 'bow', 'binary')
        """
        self.max_features = max_features
        self.method = method
        self.is_fitted = False
        
        # Initialize vectorizer based on method
        if method == "tfidf":
            self.vectorizer = TfidfVectorizer(
                max_features=max_features,
                stop_words="english",
                lowercase=True,
                ngram_range=(1, 2),  # Include bigrams for phrases
                min_df=2,  # Minimum document frequency
                max_df=0.8,  # Maximum document frequency
                norm='l2',
                sublinear_tf=True
            )
        elif method == "bow":
            self.vectorizer = CountVectorizer(
                max_features=max_features,
                stop_words="english",
                lowercase=True,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8
            )
        elif method == "binary":
            self.vectorizer = CountVectorizer(
                max_features=max_features,
                stop_words="english",
                lowercase=True,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8,
                binary=True
            )
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Optional normalizer for additional processing
        self.normalizer = Normalizer(norm='l2')
    
    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """
        Fit the vectorizer and transform texts.
        
        Args:
            texts: List of text documents to process
            
        Returns:
            np.ndarray: Feature matrix
            
        TODO (Phase-4):
        - Add validation for input texts
        - Implement vocabulary filtering for academic terms
        - Add feature selection based on variance
        """
        if not texts or not isinstance(texts, list):
            raise ValueError("Input must be a non-empty list of strings")
        
        # Validate input texts
        texts = [str(text) if text is not None else "" for text in texts]
        
        # Fit vectorizer and transform texts
        X = self.vectorizer.fit_transform(texts)
        
        # Convert to dense array if needed
        if hasattr(X, 'toarray'):
            X = X.toarray()
        
        # Apply additional normalization if specified
        if self.method in ["bow", "binary"]:
            X = self.normalizer.fit_transform(X)
        
        self.is_fitted = True
        return X
    
    def transform(self, texts: List[str]) -> np.ndarray:
        """
        Transform texts using fitted vectorizer.
        
        Args:
            texts: List of text documents to transform
            
        Returns:
            np.ndarray: Feature matrix
            
        TODO (Phase-4):
        - Add handling of unknown words
        - Implement feature importance tracking
        - Add confidence scoring for transformations
        """
        if not self.is_fitted:
            raise ValueError("FeatureExtractor must be fitted before transform")
        
        if not texts or not isinstance(texts, list):
            raise ValueError("Input must be a non-empty list of strings")
        
        # Validate input texts
        texts = [str(text) if text is not None else "" for text in texts]
        
        # Transform texts
        X = self.vectorizer.transform(texts)
        
        # Convert to dense array if needed
        if hasattr(X, 'toarray'):
            X = X.toarray()
        
        # Apply normalization if needed
        if self.method in ["bow", "binary"]:
            X = self.normalizer.transform(X)
        
        return X
    
    def get_feature_names(self) -> List[str]:
        """
        Get the feature names (vocabulary).
        
        Returns:
            List[str]: List of feature names
            
        TODO (Phase-4):
        - Add feature importance ranking
        - Implement academic term highlighting
        - Add feature grouping by type
        """
        if not self.is_fitted:
            raise ValueError("FeatureExtractor must be fitted first")
        
        return self.vectorizer.get_feature_names_out().tolist()
    
    def get_vocabulary_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vocabulary.
        
        Returns:
            Dict: Vocabulary statistics
            
        TODO (Phase-4):
        - Add more detailed statistics
        - Implement academic term analysis
        - Add feature frequency distribution
        """
        if not self.is_fitted:
            raise ValueError("FeatureExtractor must be fitted first")
        
        vocab = self.vectorizer.vocabulary_
        feature_names = self.get_feature_names()
        
        return {
            'vocabulary_size': len(vocab),
            'max_features': self.max_features,
            'method': self.method,
            'feature_count': len(feature_names),
            'sample_features': feature_names[:10]  # First 10 features
        }
    
    def analyze_feature_importance(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Analyze feature importance using simple correlation.
        
        Args:
            X: Feature matrix
            y: Target labels
            
        Returns:
            Dict: Feature importance scores
            
        TODO (Phase-4):
        - Implement more sophisticated importance measures
        - Add statistical significance testing
        - Implement feature grouping analysis
        """
        if not self.is_fitted:
            raise ValueError("FeatureExtractor must be fitted first")
        
        feature_names = self.get_feature_names()
        importance_scores = {}
        
        # Simple correlation-based importance for each feature
        for i, feature_name in enumerate(feature_names):
            if i < X.shape[1]:
                correlation = np.corrcoef(X[:, i], y)[0, 1]
                importance_scores[feature_name] = abs(correlation) if not np.isnan(correlation) else 0.0
        
        return importance_scores
    
    def save_vectorizer(self, filepath: str) -> bool:
        """
        Save the fitted vectorizer to disk.
        
        Args:
            filepath: Path to save the vectorizer
            
        Returns:
            bool: True if successful
            
        TODO (Phase-4):
        - Add version control for saved models
        - Implement compression for large vocabularies
        - Add validation for saved files
        """
        if not self.is_fitted:
            raise ValueError("FeatureExtractor must be fitted before saving")
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            return True
        except Exception as e:
            print(f"Error saving vectorizer: {e}")
            return False
    
    def load_vectorizer(self, filepath: str) -> bool:
        """
        Load a fitted vectorizer from disk.
        
        Args:
            filepath: Path to the saved vectorizer
            
        Returns:
            bool: True if successful
            
        TODO (Phase-4):
        - Add compatibility checking
        - Implement version validation
        - Add error recovery mechanisms
        """
        try:
            with open(filepath, 'rb') as f:
                self.vectorizer = pickle.load(f)
            self.is_fitted = True
            return True
        except Exception as e:
            print(f"Error loading vectorizer: {e}")
            return False
    
    def get_top_features(self, n: int = 10) -> List[Tuple[str, int]]:
        """
        Get top features by document frequency.
        
        Args:
            n: Number of top features to return
            
        Returns:
            List of tuples: (feature_name, frequency)
            
        TODO (Phase-4):
        - Add TF-IDF weighting for top features
        - Implement academic term prioritization
        - Add feature category analysis
        """
        if not self.is_fitted:
            raise ValueError("FeatureExtractor must be fitted first")
        
        if hasattr(self.vectorizer, 'idf_'):
            # For TF-IDF, use IDF scores
            idf_scores = self.vectorizer.idf_
            feature_names = self.get_feature_names()
            features_with_scores = list(zip(feature_names, idf_scores))
            # Sort by IDF (lower IDF = more common)
            features_with_scores.sort(key=lambda x: x[1])
        else:
            # For CountVectorizer, use document frequencies
            doc_freq = self.vectorizer.vocabulary_
            features_with_scores = [(name, freq) for name, freq in doc_freq.items()]
            features_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return features_with_scores[:n]
    
    def filter_academic_features(self, academic_terms: List[str]) -> List[str]:
        """
        Filter features to include only academic terms.
        
        Args:
            academic_terms: List of academic terms to preserve
            
        Returns:
            List[str]: Filtered feature names
            
        TODO (Phase-4):
        - Implement fuzzy matching for academic terms
        - Add subject-specific term lists
        - Implement automatic academic term detection
        """
        if not self.is_fitted:
            raise ValueError("FeatureExtractor must be fitted first")
        
        feature_names = self.get_feature_names()
        academic_terms_lower = [term.lower() for term in academic_terms]
        
        academic_features = []
        for feature in feature_names:
            # Check if feature contains any academic term
            if any(term in feature for term in academic_terms_lower):
                academic_features.append(feature)
        
        return academic_features
    
    def get_feature_statistics(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Get statistics about the feature matrix.
        
        Args:
            X: Feature matrix
            
        Returns:
            Dict: Feature matrix statistics
            
        TODO (Phase-4):
        - Add more comprehensive statistics
        - Implement feature distribution analysis
        - Add outlier detection
        """
        return {
            'matrix_shape': X.shape,
            'sparsity': 1.0 - (np.count_nonzero(X) / X.size),
            'mean_feature_value': np.mean(X),
            'std_feature_value': np.std(X),
            'max_feature_value': np.max(X),
            'min_feature_value': np.min(X),
            'zero_features': np.sum(np.sum(X, axis=0) == 0)
        }
