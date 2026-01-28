#!/usr/bin/env python3
"""
Machine Learning-based anomaly detector using Isolation Forest.
Provides Rule 8 for check_suspicious_exceptions.
"""

from sklearn.ensemble import IsolationForest
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

log = logging.getLogger(__name__)


class IsolationForestDetector:
    """
    Isolation Forest for multivariate anomaly detection.
    Fast, unsupervised, no training needed, works with limited data.
    
    Detects anomalies based on:
    - Current value
    - Moving averages (5min, 15min)
    - Standard deviation (volatility)
    - Rate of change
    - Distance from baseline
    """
    
    def __init__(self, contamination: float = 0.1):
        """
        Args:
            contamination: Expected proportion of anomalies (0.1 = 10%)
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            n_jobs=-1  # Use all CPU cores
        )
        self.min_samples = 20  # Minimum samples needed
        
    def _extract_features(self, values: List[float]) -> np.ndarray:
        """
        Extract features for each data point.
        
        Features:
        1. Current value
        2. Moving average (5 samples)
        3. Moving average (15 samples)
        4. Standard deviation (5 samples)
        5. Rate of change (vs previous)
        6. Distance from overall mean
        
        Args:
            values: List of time-series values
            
        Returns:
            numpy array of shape (n_samples, 6 features)
        """
        features = []
        overall_mean = np.mean(values)
        
        for i in range(len(values)):
            # Feature 1: Current value
            current = values[i]
            
            # Feature 2: Moving average (5 samples)
            start_5 = max(0, i - 4)
            ma_5 = np.mean(values[start_5:i+1])
            
            # Feature 3: Moving average (15 samples)
            start_15 = max(0, i - 14)
            ma_15 = np.mean(values[start_15:i+1])
            
            # Feature 4: Standard deviation (5 samples - volatility)
            if i >= 4:
                std_5 = np.std(values[i-4:i+1])
            else:
                std_5 = 0.0
            
            # Feature 5: Rate of change (vs previous)
            if i > 0:
                roc = (current - values[i-1]) / (values[i-1] + 1e-6)
            else:
                roc = 0.0
            
            # Feature 6: Distance from overall mean
            dist_mean = abs(current - overall_mean)
            
            features.append([current, ma_5, ma_15, std_5, roc, dist_mean])
        
        return np.array(features)
    
    def detect_anomalies(
        self,
        time_series: List[Dict],
        device: str,
        exception: str,
        slot: str,
        min_confidence: float = 0.6
    ) -> Optional[Dict]:
        """
        Detect anomalies using Isolation Forest.
        
        Args:
            time_series: List of {"time": datetime, "value": float}
            device: Device name
            exception: Exception type
            slot: FPC slot
            min_confidence: Minimum confidence to report (0-1)
            
        Returns:
            Detection result dict or None if not anomalous
        """
        # Filter out None values and extract data
        valid_samples = [s for s in time_series if s["value"] is not None]
        
        if len(valid_samples) < self.min_samples:
            log.debug(f"Insufficient data for {device}/{exception}/{slot}: {len(valid_samples)}/{self.min_samples}")
            return None
        
        values = [s["value"] for s in valid_samples]
        times = [s["time"] for s in valid_samples]
        
        # Skip if all values are near zero (no activity)
        if max(values) < 0.1:
            return None
        
        try:
            # Extract features
            X = self._extract_features(values)
            
            # Fit model and predict
            predictions = self.model.fit_predict(X)
            anomaly_scores = self.model.score_samples(X)
            
            # Find anomalies (prediction = -1)
            anomaly_indices = np.where(predictions == -1)[0]
            
            if len(anomaly_indices) == 0:
                return None
            
            # Calculate confidence
            # Anomaly score is negative (more negative = more anomalous)
            # Convert to 0-1 scale
            min_score = np.min(anomaly_scores)
            max_score = np.max(anomaly_scores)
            
            if max_score == min_score:
                confidence = 0.5
            else:
                # Normalize anomaly scores
                mean_anomaly_score = np.mean(anomaly_scores[anomaly_indices])
                confidence = (min_score - mean_anomaly_score) / (max_score - min_score)
                confidence = max(0.0, min(1.0, confidence))
            
            # Only report if confidence is high enough
            if confidence < min_confidence:
                return None
            
            # Get statistics
            anomaly_values = [values[i] for i in anomaly_indices]
            normal_values = [values[i] for i in range(len(values)) if i not in anomaly_indices]
            
            max_anomaly_value = max(anomaly_values)
            mean_normal = np.mean(normal_values) if normal_values else 0.0
            
            # Get timestamp of highest anomaly
            max_anomaly_idx = anomaly_indices[np.argmax([values[i] for i in anomaly_indices])]
            detection_time = times[max_anomaly_idx]
            
            # Calculate severity factor
            if mean_normal > 0:
                severity_factor = max_anomaly_value / mean_normal
            else:
                severity_factor = max_anomaly_value
            
            # Build details
            details = (
                f"ML-detected anomaly: {len(anomaly_indices)} anomalous samples "
                f"({len(anomaly_indices)/len(values)*100:.0f}% of data). "
                f"Peak: {max_anomaly_value:.2f} exc/s "
                f"(baseline: {mean_normal:.2f} exc/s, {severity_factor:.1f}x). "
                f"Confidence: {confidence:.1%}"
            )
            
            return {
                "is_anomaly": True,
                "confidence": float(confidence),
                "num_anomalies": len(anomaly_indices),
                "max_value": float(max_anomaly_value),
                "baseline": float(mean_normal),
                "severity_factor": float(severity_factor),
                "detection_time": detection_time,
                "details": details,
                "anomaly_indices": anomaly_indices.tolist(),
                "anomaly_scores": anomaly_scores.tolist()
            }
            
        except Exception as e:
            log.error(f"Error in ML detection for {device}/{exception}/{slot}: {e}")
            return None


def create_isolation_forest_detector() -> IsolationForestDetector:
    """Factory function to create detector with default settings"""
    return IsolationForestDetector(contamination=0.15)  # Expect 15% anomalies
