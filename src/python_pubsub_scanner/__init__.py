"""
Python PubSub Scanner

Autonomous scanner for event-driven architectures.
Scans codebase and pushes event flow graphs to monitoring API.

Zero external dependencies except requests for HTTP calls.
"""

__version__ = "0.1.0"

from .analyze_event_flow import EventFlowAnalyzer, NamespacedItem
from .generate_hierarchical_tree import generate_hierarchical_tree
from .scanner import EventFlowScanner

__all__ = [
    "EventFlowScanner",
    "EventFlowAnalyzer",
    "NamespacedItem",
    "generate_hierarchical_tree",
    "__version__",
]
