"""
Graph generators for event flow visualization.

This module provides a pluggable architecture for generating different types
of event flow graphs. Each generator implements the GraphGenerator interface
and can be easily extended to support new graph types.

Usage:
    from python_pubsub_scanner.graph_generators import get_generator, AVAILABLE_GENERATORS

    # Get a specific generator
    generator = get_generator('complete', colors={...}, shapes={...})

    # Generate DOT content
    dot_content = generator.generate(analyzer)

Available generators:
    - complete: Complete event flow graph with all nodes and edges
    - full-tree: Hierarchical tree representation of the event flow
"""
from __future__ import annotations

from typing import Dict, Optional, Type

from .base import GraphGenerator
from .complete import CompleteGraphGenerator
from .full_tree import FullTreeGraphGenerator

# Registry of available graph generators
_GENERATOR_REGISTRY: Dict[str, Type[GraphGenerator]] = {
    'complete': CompleteGraphGenerator,
    'full-tree': FullTreeGraphGenerator,
}

# Public list of available generator types
AVAILABLE_GENERATORS = list(_GENERATOR_REGISTRY.keys())


def get_generator(
    graph_type: str,
    colors: Optional[Dict[str, str]] = None,
    shapes: Optional[Dict[str, str]] = None,
    fontname: Optional[str] = None
) -> GraphGenerator:
    """
    Get a graph generator instance for the specified type.

    Args:
        graph_type: The type of graph to generate (e.g., 'complete', 'full-tree').
        colors: Optional mapping of namespace names to hex color codes.
        shapes: Optional mapping of namespace names to Graphviz node shapes.
        fontname: Optional font name to use for graph text elements.

    Returns:
        An instance of the appropriate GraphGenerator subclass.

    Raises:
        ValueError: If the graph_type is not recognized.

    Example:
        >>> generator = get_generator('complete', colors={'bot_lifecycle': '#81c784'})
        >>> dot_content = generator.generate(analyzer)
    """
    if graph_type not in _GENERATOR_REGISTRY:
        available = ', '.join(AVAILABLE_GENERATORS)
        raise ValueError(
            f"Unknown graph type '{graph_type}'. "
            f"Available types: {available}"
        )

    generator_class = _GENERATOR_REGISTRY[graph_type]
    return generator_class(colors=colors, shapes=shapes, fontname=fontname)


def register_generator(graph_type: str, generator_class: Type[GraphGenerator]) -> None:
    """
    Register a custom graph generator.

    This function allows users to add their own custom graph generators
    to the registry, making them available via get_generator().

    Args:
        graph_type: The type identifier for the generator.
        generator_class: The GraphGenerator subclass to register.

    Example:
        >>> class MyCustomGenerator(GraphGenerator):
        ...     @property
        ...     def graph_type(self) -> str:
        ...         return "custom"
        ...
        ...     def generate(self, analyzer, output_path=None) -> str:
        ...         return "digraph Custom { ... }"
        ...
        >>> register_generator('custom', MyCustomGenerator)
        >>> generator = get_generator('custom')
    """
    _GENERATOR_REGISTRY[graph_type] = generator_class
    # Update the public list
    global AVAILABLE_GENERATORS
    AVAILABLE_GENERATORS = list(_GENERATOR_REGISTRY.keys())


__all__ = [
    'GraphGenerator',
    'CompleteGraphGenerator',
    'FullTreeGraphGenerator',
    'get_generator',
    'register_generator',
    'AVAILABLE_GENERATORS',
]
