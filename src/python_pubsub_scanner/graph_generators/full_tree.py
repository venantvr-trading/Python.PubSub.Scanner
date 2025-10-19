"""
Full tree graph generator.

Generates a hierarchical tree representation of the event flow.
"""
from __future__ import annotations

import tempfile
from typing import Optional, TYPE_CHECKING

from .base import GraphGenerator
from ..generate_hierarchical_tree import generate_hierarchical_tree

if TYPE_CHECKING:
    from ..analyze_event_flow import EventFlowAnalyzer


class FullTreeGraphGenerator(GraphGenerator):
    """
    Generates a hierarchical tree representation of the event flow.

    This generator creates a structured tree view of events and agents,
    useful for understanding the overall architecture hierarchy.
    """

    @property
    def graph_type(self) -> str:
        return "full-tree"

    def generate(self, analyzer: EventFlowAnalyzer, output_path: Optional[str] = None) -> str:
        """
        Generate DOT content for the full-tree graph.

        Args:
            analyzer: The EventFlowAnalyzer containing the parsed event flow data.
            output_path: Optional path to write the DOT file to.

        Returns:
            The generated DOT content as a string.
        """
        # If output_path is provided, use it directly
        if output_path:
            generate_hierarchical_tree(analyzer, output_path, output_format='dot')
            with open(output_path, 'r', encoding='utf-8') as f:
                return f.read()

        # Otherwise, use a temporary file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.dot', delete=True, encoding='utf-8') as temp_f:
            generate_hierarchical_tree(analyzer, temp_f.name, output_format='dot')
            temp_f.seek(0)
            return temp_f.read()
