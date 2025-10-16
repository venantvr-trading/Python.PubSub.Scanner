"""
Generate Hierarchical Event Flow Trees

Creates hierarchical visualizations of event flow in DOT format.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .analyze_event_flow import EventFlowAnalyzer


def generate_hierarchical_tree(analyzer: EventFlowAnalyzer, output_path: str, output_format: str = "png") -> None:
    """
    Generate hierarchical tree in DOT format

    Args:
        analyzer: EventFlowAnalyzer instance with analysis results
        output_path: Path to save the output file
        output_format: Output format (only 'dot' is directly supported)
    """
    # Create DOT content
    lines = ['digraph EventFlow {',
             '    rankdir=TB;',
             '    splines=ortho;',
             '    node [shape=box, style="filled,rounded", fontname="Arial", fontsize=10, color="#cccccc"];',
             '    edge [arrowsize=0.8, color="#999999"];',
             '']

    # Separate events and agents
    events = analyzer.get_all_events()
    agents = set(analyzer.subscriptions.keys()) | set(analyzer.publications.keys())

    # Agent color
    agent_color = '#ffcc80'

    # Add event nodes
    lines.append('    // Events')
    for event in sorted(events):
        lines.append(f'    "{event}" [fillcolor="#e0e0e0", shape=ellipse, fontsize=10];')

    lines.append('')
    lines.append('    // Agents')
    for agent in sorted(agents):
        label = agent.replace('_', ' ')
        lines.append(f'    "{agent}" [label="{label}", fillcolor="{agent_color}", shape=box, fontsize=10];')

    lines.append('')
    lines.append('    // Edges')

    # Add edges: event -> agent (subscription)
    for event, subscribers in sorted(analyzer.event_to_subscribers.items()):
        for subscriber in subscribers:
            lines.append(f'    "{event}" -> "{subscriber}";')

    # Add edges: agent -> event (publication)
    for agent, publications in sorted(analyzer.publications.items()):
        for event in publications:
            lines.append(f'    "{agent}" -> "{event}";')

    lines.append('}')

    # Write output
    dot_content = '\n'.join(lines)

    if output_format.lower() == 'dot':
        Path(output_path).write_text(dot_content)
        print(f"✅ DOT file saved to {output_path}")
        print(f"   Generate image with: dot -Tpng {output_path} -o event_tree.png")
    else:
        # For other formats, save as .dot and show conversion command
        dot_path = str(Path(output_path).with_suffix('.dot'))
        Path(dot_path).write_text(dot_content)
        print(f"✅ DOT file saved to {dot_path}")
        print(f"   Convert to {output_format}: dot -T{output_format} {dot_path} -o {output_path}")
