"""
Complete graph generator.

Generates a complete event flow graph showing all events, agents, and their connections.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .base import GraphGenerator

if TYPE_CHECKING:
    from ..analyze_event_flow import EventFlowAnalyzer


class CompleteGraphGenerator(GraphGenerator):
    """
    Generates a complete event flow graph with all nodes and edges.

    This generator creates a comprehensive view of the entire event-driven architecture,
    showing all events, agents, subscriptions, and publications.
    """

    @property
    def graph_type(self) -> str:
        return "complete"

    def generate(self, analyzer: EventFlowAnalyzer, output_path: Optional[str] = None) -> str:
        """
        Generate DOT content for the complete graph.

        Args:
            analyzer: The EventFlowAnalyzer containing the parsed event flow data.
            output_path: Optional path to write the DOT file to.

        Returns:
            The generated DOT content as a string.
        """
        dot_content = self._generate_dot_content(analyzer)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(dot_content)

        return dot_content

    def _generate_dot_content(self, analyzer: EventFlowAnalyzer) -> str:
        """
        Generate DOT content for complete graph with homogeneous styles and namespace classes.

        Args:
            analyzer: The EventFlowAnalyzer containing the parsed event flow data.

        Returns:
            The generated DOT content as a string.
        """
        lines = [
            'digraph EventFlow {',
            f'    graph [fontname="{self.fontname}"];',
            '    rankdir=TB;',
            f'    node [shape=box, style="filled,rounded", fontname="{self.fontname}", fontsize=10];',
            f'    edge [arrowsize=0.8, fontname="{self.fontname}"];',
            ''
        ]

        events = analyzer.get_all_events()
        agents = analyzer.get_all_agents()

        # Add event nodes with namespace-based styling
        for event in sorted(events):
            default_color = "#e0e0e0"
            default_shape = "ellipse"

            fillcolor = self.colors.get(event.namespace, default_color)
            shape = self.shapes.get(event.namespace, default_shape)

            lines.append(
                f'    "{event.name}" [fillcolor="{fillcolor}", shape={shape}, '
                f'class="namespace-{event.namespace}"];'
            )

        # Add agent nodes with namespace-based styling
        for agent in sorted(agents):
            default_color = "#ffcc80"
            fillcolor = self.colors.get(agent.namespace, default_color)

            lines.append(
                f'    "{agent.name}" [fillcolor="{fillcolor}", '
                f'class="namespace-{agent.namespace}"];'
            )

        lines.append('')

        # Add edges for subscriptions (event -> subscriber)
        for event, subscribers in sorted(analyzer.event_to_subscribers.items()):
            for subscriber in subscribers:
                lines.append(f'    "{event.name}" -> "{subscriber.name}";')

        # Add edges for publications (agent -> event)
        for agent, publications in sorted(analyzer.publications.items()):
            for event in publications:
                lines.append(f'    "{agent.name}" -> "{event.name}";')

        lines.append('}')
        return '\n'.join(lines)
