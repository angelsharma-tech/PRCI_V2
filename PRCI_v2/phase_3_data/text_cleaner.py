"""
Text Cleaning Module for PRCI v2.0

This module handles normalization and cleaning
of user-generated text for downstream analysis.

NOTE:
This phase does NOT perform feature extraction
or model inference.
"""

import re
import string
from typing import List, Optional


class TextCleaner:
    """
    Comprehensive text cleaning and normalization class.
    
    This class provides methods to clean and normalize user-generated
    text data while preserving meaningful content for behavioral
    pattern analysis in academic procrastination contexts.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the text cleaner with configuration.
        
        Args:
            config: Configuration dictionary for cleaning parameters
        """
        self.config = config or {}
        self.preserve_academic_terms = self.config.get('preserve_academic_terms', True)
        self.preserve_emotional_indicators = self.config.get('preserve_emotional_indicators', True)
        self.preserve_temporal_expressions = self.config.get('preserve_temporal_expressions', True)
        
        # Academic terms to preserve during cleaning
        self.academic_terms = {
            'assignment', 'project', 'exam', 'test', 'quiz', 'paper', 'essay',
            'homework', 'study', 'research', 'presentation', 'deadline', 'due',
            'grade', 'credit', 'course', 'class', 'lecture', 'seminar', 'lab',
            'thesis', 'dissertation', 'proposal', 'outline', 'draft', 'revision'
        }
        
        # Emotional indicators to preserve
        self.emotional_indicators = {
            'stress', 'stressed', 'anxious', 'anxiety', 'overwhelm', 'overwhelmed',
            'confident', 'confidence', 'motivated', 'motivation', 'excited', 'exciting',
            'worried', 'worry', 'nervous', 'scared', 'afraid', 'fear', 'panic',
            'happy', 'sad', 'angry', 'frustrated', 'disappointed', 'proud'
        }
        
        # Temporal expressions to preserve
        self.temporal_expressions = {
            'today', 'tomorrow', 'yesterday', 'week', 'month', 'semester', 'quarter',
            'morning', 'afternoon', 'evening', 'night', 'deadline', 'due', 'late',
            'early', 'soon', 'later', 'now', 'immediately', 'quickly', 'slowly'
        }
    
    def normalize(self, text: str) -> str:
        """
        Normalize text by lowercasing and
        removing unnecessary whitespace.
        
        Args:
            text: Raw input text
            
        Returns:
            str: Normalized text
            
        TODO (Phase-3):
        - Implement Unicode normalization for multilingual support
        - Add language detection for appropriate normalization
        - Consider preserving capitalization for emphasis detection
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove leading and trailing whitespace
        text = text.strip()
        
        # Normalize multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize line breaks and tabs
        text = re.sub(r'[\n\t\r]+', ' ', text)
        
        return text
    
    def remove_noise(self, text: str) -> str:
        """
        Remove URLs, special characters,
        and non-informative symbols.
        
        Args:
            text: Normalized text
            
        Returns:
            str: Text with noise removed
            
        TODO (Phase-3):
        - Add more sophisticated URL pattern matching
        - Implement emoji and emoticon handling
        - Add support for academic citation preservation
        """
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # Remove phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', text)
        
        # Handle special characters based on configuration
        if self.preserve_academic_terms or self.preserve_emotional_indicators:
            # Preserve meaningful punctuation for academic and emotional content
            text = self._preserve_meaningful_punctuation(text)
        else:
            # Remove most special characters
            text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove excessive punctuation repetition
        text = re.sub(r'([!?])\1+', r'\1', text)
        
        return text
    
    def _preserve_meaningful_punctuation(self, text: str) -> str:
        """
        Preserve punctuation that carries emotional or academic meaning.
        
        Args:
            text: Text to process
            
        Returns:
            str: Text with meaningful punctuation preserved
            
        TODO (Phase-3):
        - Add more sophisticated emotional punctuation detection
        - Implement academic notation preservation
        - Consider cultural variations in emotional expression
        """
        # Preserve question marks for uncertainty expressions
        # Preserve exclamation marks for emotional intensity
        # Preserve periods for sentence structure
        
        # Remove other special characters but keep spaces, basic punctuation
        text = re.sub(r'[^a-zA-Z0-9\s.!?]', ' ', text)
        
        return text
    
    def remove_redundant_words(self, text: str) -> str:
        """
        Remove redundant words and filler content.
        
        Args:
            text: Cleaned text
            
        Returns:
            str: Text with redundancies removed
            
        TODO (Phase-3):
        - Implement stop word removal specific to academic context
        - Add filler phrase detection and removal
        - Consider preserving certain stop words for emotional context
        """
        if not text:
            return ""
        
        # Common filler words in academic procrastination context
        filler_words = {
            'um', 'uh', 'like', 'you know', 'I mean', 'sort of', 'kind of',
            'actually', 'basically', 'literally', 'really', 'very', 'pretty'
        }
        
        words = text.split()
        filtered_words = []
        
        for word in words:
            if word not in filler_words:
                filtered_words.append(word)
        
        return ' '.join(filtered_words)
    
    def handle_repetitive_patterns(self, text: str) -> str:
        """
        Handle repetitive character patterns and emphasis.
        
        Args:
            text: Text to process
            
        Returns:
            str: Text with repetitive patterns handled
            
        TODO (Phase-3):
        - Add more sophisticated pattern recognition
        - Implement emphasis preservation logic
        - Consider cultural variations in emphasis expression
        """
        if not text:
            return ""
        
        # Collapse repeated characters (soooo -> soo)
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        
        # Handle repeated words for emphasis (very very -> very)
        text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text)
        
        return text
    
    def validate_content(self, text: str) -> tuple[bool, str]:
        """
        Validate that processed content remains appropriate.
        
        Args:
            text: Processed text to validate
            
        Returns:
            tuple: (is_valid, reason)
            
        TODO (Phase-3):
        - Implement content appropriateness checking
        - Add clinical content detection and flagging
        - Consider privacy violation detection
        """
        if not text or len(text.strip()) < 3:
            return False, "Text too short or empty"
        
        # Check for potential clinical content that should be flagged
        clinical_indicators = {
            'depression', 'therapy', 'therapist', 'medication', 'diagnosis',
            'treatment', 'clinical', 'psychiatrist', 'counseling', 'suicide'
        }
        
        words = text.lower().split()
        found_clinical = [word for word in words if word in clinical_indicators]
        
        if found_clinical:
            return False, f"Potential clinical content detected: {found_clinical}"
        
        # Check for personal identifiers
        personal_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd)\b',  # Address pattern
        ]
        
        for pattern in personal_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Potential personal identifier detected"
        
        return True, "Content validated"
    
    def clean(self, text: str) -> str:
        """
        Full cleaning pipeline.
        
        Args:
            text: Raw input text
            
        Returns:
            str: Fully cleaned text
            
        TODO (Phase-3):
        - Add quality metrics calculation
        - Implement logging for cleaning steps
        - Add configuration-based cleaning levels
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Step 1: Normalize
        text = self.normalize(text)
        
        # Step 2: Remove noise
        text = self.remove_noise(text)
        
        # Step 3: Handle repetitive patterns
        text = self.handle_repetitive_patterns(text)
        
        # Step 4: Remove redundant words
        text = self.remove_redundant_words(text)
        
        # Step 5: Final cleanup
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        
        # Step 6: Validate content
        is_valid, reason = self.validate_content(text)
        if not is_valid:
            # Log the validation issue but return cleaned text for review
            print(f"Content validation warning: {reason}")
        
        return text
    
    def batch_clean(self, texts: List[str]) -> List[str]:
        """
        Clean multiple texts in batch.
        
        Args:
            texts: List of raw text strings
            
        Returns:
            List[str]: List of cleaned texts
            
        TODO (Phase-3):
        - Add parallel processing for large batches
        - Implement progress tracking
        - Add batch quality reporting
        """
        return [self.clean(text) for text in texts]
    
    def get_cleaning_stats(self, original: str, cleaned: str) -> dict:
        """
        Get statistics about the cleaning process.
        
        Args:
            original: Original text
            cleaned: Cleaned text
            
        Returns:
            dict: Cleaning statistics
            
        TODO (Phase-3):
        - Add more detailed statistics
        - Implement quality score calculation
        - Add content preservation metrics
        """
        return {
            'original_length': len(original),
            'cleaned_length': len(cleaned),
            'reduction_ratio': 1 - (len(cleaned) / len(original)) if len(original) > 0 else 0,
            'word_count_original': len(original.split()),
            'word_count_cleaned': len(cleaned.split()),
            'preservation_rate': len(cleaned.split()) / len(original.split()) if len(original.split()) > 0 else 0
        }
