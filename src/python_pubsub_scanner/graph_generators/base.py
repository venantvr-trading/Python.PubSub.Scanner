"""
Base class for graph generators.

This module defines the abstract interface that all graph generators must implement.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..analyze_event_flow import EventFlowAnalyzer


class GraphGenerator(ABC):
    """
    Abstract base class for graph generators.

    Each graph generator is responsible for creating a DOT representation
    of the event flow in a specific format/style.
    """

    def __init__(
            self,
            colors: Optional[Dict[str, str]] = None,
            shapes: Optional[Dict[str, str]] = None,
            fontname: Optional[str] = None
    ):
        """
        Initialize the graph generator with styling options.

        Args:
            colors: Mapping of namespace names to hex color codes.
            shapes: Mapping of namespace names to Graphviz node shapes.
            fontname: Font name to use for graph text elements.
        """
        self.colors = colors or {}
        self.shapes = shapes or {}
        self.fontname = fontname or "Arial"

    @abstractmethod
    def generate(self, analyzer: EventFlowAnalyzer, output_path: Optional[str] = None) -> str:
        """
        Generate DOT content for the graph.

        Args:
            analyzer: The EventFlowAnalyzer containing the parsed event flow data.
            output_path: Optional path to write the DOT file to. If provided, writes to file.

        Returns:
            The generated DOT content as a string.

        Raises:
            Exception: If graph generation fails.
        """
        pass

    @property
    @abstractmethod
    def graph_type(self) -> str:
        """
        Return the type identifier for this graph generator.

        Returns:
            A string identifying the graph type (e.g., "complete", "full-tree").
        """
        pass
