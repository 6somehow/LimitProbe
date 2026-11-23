"""Auditable, uncalibrated confidence and coverage utilities."""

from .model import score_confidence, reliability_table, wilson_interval

__all__ = ["score_confidence", "reliability_table", "wilson_interval"]
