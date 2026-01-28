#!/usr/bin/env python3
"""
Dynamic Baseline Manager for PFE Exception Detection

Implements adaptive baseline calculation with:
- Context-aware baselines (time of day, day of week)
- Multi-window analysis (short/medium/long term)
- Regime change detection
- Exponential weighted moving average (EWMA)
"""

import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

log = logging.getLogger(__name__)


class BaselineManager:
    """
    Manages dynamic baselines for exception detection
    """
    
    def __init__(
        self,
        short_window_hours: int = 2,
        medium_window_hours: int = 24,
        long_window_hours: int = 168,  # 7 days
        ewma_alpha: float = 0.3,
        regime_change_threshold: float = 2.0
    ):
        """
        Initialize baseline manager
        
        Args:
            short_window_hours: Hours for short-term baseline (default: 2)
            medium_window_hours: Hours for medium-term baseline (default: 24)
            long_window_hours: Hours for long-term baseline (default: 168 = 7 days)
            ewma_alpha: EWMA smoothing factor 0-1 (default: 0.3, higher = more reactive)
            regime_change_threshold: Multiplier to detect regime changes (default: 2.0)
        """
        self.short_window = short_window_hours
        self.medium_window = medium_window_hours
        self.long_window = long_window_hours
        self.ewma_alpha = ewma_alpha
        self.regime_threshold = regime_change_threshold
        
        log.info(f"✅ BaselineManager initialized: short={short_window_hours}h, "
                f"medium={medium_window_hours}h, long={long_window_hours}h")
    
    def calculate_contextual_baseline(
        self,
        time_series: List[Dict],
        current_time: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate baseline considering time-of-day and day-of-week context
        
        Args:
            time_series: List of {"time": datetime, "value": float}
            current_time: Reference time (default: now)
            
        Returns:
            dict with baseline statistics
        """
        if not time_series:
            return self._empty_baseline()
        
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Filter valid values
        valid_series = [x for x in time_series if x.get("value") is not None]
        if not valid_series:
            return self._empty_baseline()
        
        # Get current context
        current_hour = current_time.hour
        current_weekday = current_time.weekday()  # 0=Monday, 6=Sunday
        
        # Filter samples matching current context (±2 hours, same day type)
        contextual_samples = []
        for sample in valid_series:
            sample_time = sample["time"]
            if isinstance(sample_time, str):
                sample_time = datetime.fromisoformat(sample_time.replace('+00:00', ''))
            
            hour_diff = abs(sample_time.hour - current_hour)
            # Handle hour wraparound (23:00 vs 01:00 = 2 hours)
            if hour_diff > 12:
                hour_diff = 24 - hour_diff
            
            # Check if same day type (weekday vs weekend)
            sample_weekday = sample_time.weekday()
            is_same_day_type = (
                (sample_weekday < 5 and current_weekday < 5) or  # Both weekdays
                (sample_weekday >= 5 and current_weekday >= 5)     # Both weekend
            )
            
            if hour_diff <= 2 and is_same_day_type:
                contextual_samples.append(sample["value"])
        
        # If insufficient contextual data, fall back to all data
        if len(contextual_samples) < 10:
            log.debug(f"Insufficient contextual samples ({len(contextual_samples)}), using all data")
            contextual_samples = [x["value"] for x in valid_series]
        
        if not contextual_samples:
            return self._empty_baseline()
        
        return {
            "mean": statistics.mean(contextual_samples),
            "median": statistics.median(contextual_samples),
            "std": statistics.stdev(contextual_samples) if len(contextual_samples) > 1 else 0,
            "min": min(contextual_samples),
            "max": max(contextual_samples),
            "p95": self._percentile(contextual_samples, 0.95),
            "sample_count": len(contextual_samples),
            "context": f"hour={current_hour}±2h, weekday={current_weekday}"
        }
    
    def calculate_multi_window_baseline(
        self,
        all_data: List[Dict],
        current_time: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate baselines across multiple time windows
        
        Args:
            all_data: Complete time series data
            current_time: Reference time (default: now)
            
        Returns:
            dict with short/medium/long baselines and weights
        """
        if not all_data:
            return {
                "short": self._empty_baseline(),
                "medium": self._empty_baseline(),
                "long": self._empty_baseline(),
                "composite": self._empty_baseline(),
                "weights": {"short": 0, "medium": 0, "long": 0}
            }
        
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Sort by time
        sorted_data = sorted(all_data, key=lambda x: x["time"])
        
        # Split into windows
        short_cutoff = current_time - timedelta(hours=self.short_window)
        medium_cutoff = current_time - timedelta(hours=self.medium_window)
        long_cutoff = current_time - timedelta(hours=self.long_window)
        
        short_data = [x for x in sorted_data if self._parse_time(x["time"]) >= short_cutoff]
        medium_data = [x for x in sorted_data if self._parse_time(x["time"]) >= medium_cutoff]
        long_data = [x for x in sorted_data if self._parse_time(x["time"]) >= long_cutoff]
        
        # Calculate baselines for each window
        short_baseline = self._calculate_simple_baseline(short_data)
        medium_baseline = self._calculate_simple_baseline(medium_data)
        long_baseline = self._calculate_simple_baseline(long_data)
        
        # Calculate adaptive weights based on data availability and variance
        weights = self._calculate_adaptive_weights(short_baseline, medium_baseline, long_baseline)
        
        # Composite baseline (weighted average)
        composite = self._weighted_baseline(
            [short_baseline, medium_baseline, long_baseline],
            weights
        )
        
        return {
            "short": short_baseline,
            "medium": medium_baseline,
            "long": long_baseline,
            "composite": composite,
            "weights": weights
        }
    
    def detect_regime_change(
        self,
        recent_data: List[Dict],
        historical_baseline: Dict
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Detect if there's been a permanent regime change (new normal)
        
        Args:
            recent_data: Recent time series samples
            historical_baseline: Historical baseline statistics
            
        Returns:
            (is_regime_change, new_baseline_dict)
        """
        if not recent_data or not historical_baseline:
            return False, None
        
        # Calculate recent baseline
        recent_baseline = self._calculate_simple_baseline(recent_data)
        
        if recent_baseline["sample_count"] < 20:
            return False, None  # Need sufficient data
        
        # Check for sustained deviation
        hist_mean = historical_baseline.get("mean", 0)
        hist_std = historical_baseline.get("std", 0)
        recent_mean = recent_baseline.get("mean", 0)
        
        # Regime change: recent mean significantly different AND sustained
        threshold = hist_mean + (self.regime_threshold * hist_std)
        
        if recent_mean > threshold or recent_mean < hist_mean * 0.5:
            # Check if deviation is sustained (not just spike)
            recent_values = [x["value"] for x in recent_data if x.get("value") is not None]
            sustained_count = sum(1 for v in recent_values if v > threshold or v < hist_mean * 0.5)
            sustained_pct = (sustained_count / len(recent_values)) * 100
            
            if sustained_pct >= 70:  # 70% of samples deviate
                log.info(f"🔄 Regime change detected: {hist_mean:.2f} → {recent_mean:.2f} "
                        f"({sustained_pct:.0f}% sustained)")
                return True, recent_baseline
        
        return False, None
    
    def calculate_ewma_baseline(
        self,
        time_series: List[Dict],
        alpha: Optional[float] = None
    ) -> Dict:
        """
        Calculate Exponentially Weighted Moving Average baseline
        More reactive to recent changes than simple average
        
        Args:
            time_series: Sorted time series data (oldest first)
            alpha: EWMA smoothing factor (default: self.ewma_alpha)
            
        Returns:
            dict with EWMA statistics
        """
        if not time_series:
            return self._empty_baseline()
        
        if alpha is None:
            alpha = self.ewma_alpha
        
        # Filter valid values
        valid_series = [x for x in time_series if x.get("value") is not None]
        if not valid_series:
            return self._empty_baseline()
        
        # Sort by time (oldest first)
        sorted_series = sorted(valid_series, key=lambda x: x["time"])
        values = [x["value"] for x in sorted_series]
        
        # Calculate EWMA
        ewma = values[0]
        for value in values[1:]:
            ewma = alpha * value + (1 - alpha) * ewma
        
        # Calculate EWMA standard deviation
        ewma_var = 0
        for value in values:
            ewma_var = alpha * ((value - ewma) ** 2) + (1 - alpha) * ewma_var
        ewma_std = ewma_var ** 0.5
        
        return {
            "ewma": ewma,
            "ewma_std": ewma_std,
            "upper_bound": ewma + 3 * ewma_std,
            "lower_bound": max(0, ewma - 3 * ewma_std),
            "sample_count": len(values),
            "alpha": alpha
        }
    
    # ========== PRIVATE HELPER METHODS ==========
    
    def _empty_baseline(self) -> Dict:
        """Return empty baseline structure"""
        return {
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "p95": 0.0,
            "sample_count": 0
        }
    
    def _calculate_simple_baseline(self, data: List[Dict]) -> Dict:
        """Calculate basic statistical baseline"""
        valid_values = [x["value"] for x in data if x.get("value") is not None]
        
        if not valid_values:
            return self._empty_baseline()
        
        return {
            "mean": statistics.mean(valid_values),
            "median": statistics.median(valid_values),
            "std": statistics.stdev(valid_values) if len(valid_values) > 1 else 0,
            "min": min(valid_values),
            "max": max(valid_values),
            "p95": self._percentile(valid_values, 0.95),
            "sample_count": len(valid_values)
        }
    
    def _calculate_adaptive_weights(
        self,
        short: Dict,
        medium: Dict,
        long: Dict
    ) -> Dict:
        """
        Calculate adaptive weights based on data quality
        
        Factors:
        - Data availability (sample count)
        - Variance (lower variance = more reliable)
        - Recency (recent data weighted higher)
        """
        # Base weights (recency preference)
        base_weights = {"short": 0.5, "medium": 0.3, "long": 0.2}
        
        # Adjust by data availability
        total_samples = short["sample_count"] + medium["sample_count"] + long["sample_count"]
        if total_samples == 0:
            return {"short": 0, "medium": 0, "long": 0}
        
        availability_weights = {
            "short": short["sample_count"] / total_samples,
            "medium": medium["sample_count"] / total_samples,
            "long": long["sample_count"] / total_samples
        }
        
        # Adjust by variance (inverse weight - lower variance = higher weight)
        max_std = max(short["std"], medium["std"], long["std"], 0.01)
        variance_weights = {
            "short": 1 - (short["std"] / max_std),
            "medium": 1 - (medium["std"] / max_std),
            "long": 1 - (long["std"] / max_std)
        }
        
        # Combine weights
        combined_weights = {}
        for key in ["short", "medium", "long"]:
            combined_weights[key] = (
                base_weights[key] * 0.4 +
                availability_weights[key] * 0.3 +
                variance_weights[key] * 0.3
            )
        
        # Normalize to sum to 1.0
        total_weight = sum(combined_weights.values())
        if total_weight > 0:
            combined_weights = {k: v / total_weight for k, v in combined_weights.items()}
        
        return combined_weights
    
    def _weighted_baseline(
        self,
        baselines: List[Dict],
        weights: Dict
    ) -> Dict:
        """Calculate weighted composite baseline"""
        if not baselines or sum(weights.values()) == 0:
            return self._empty_baseline()
        
        weight_list = [weights["short"], weights["medium"], weights["long"]]
        
        return {
            "mean": sum(b["mean"] * w for b, w in zip(baselines, weight_list)),
            "median": sum(b["median"] * w for b, w in zip(baselines, weight_list)),
            "std": sum(b["std"] * w for b, w in zip(baselines, weight_list)),
            "min": min(b["min"] for b in baselines),
            "max": max(b["max"] for b in baselines),
            "p95": sum(b["p95"] * w for b, w in zip(baselines, weight_list)),
            "sample_count": sum(b["sample_count"] for b in baselines)
        }
    
    def _percentile(self, values: List[float], p: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _parse_time(self, time_obj) -> datetime:
        """Parse time to datetime object (timezone-naive for comparison)"""
        from datetime import timezone as tz
        
        if isinstance(time_obj, str):
            # Parse and convert to naive UTC
            dt = datetime.fromisoformat(time_obj.replace('+00:00', ''))
            # If it has timezone info, convert to UTC and make naive
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        
        # If datetime object, ensure it's naive
        if isinstance(time_obj, datetime):
            if time_obj.tzinfo is not None:
                # Convert to UTC and remove timezone
                return time_obj.replace(tzinfo=None)
            return time_obj
        
        return time_obj
