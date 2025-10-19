#!/usr/bin/env python3
"""
Example: Standalone Anomaly Detection

This script demonstrates how to use the AnomalyDetector independently
to analyze your event-driven architecture for potential issues.
"""
from pathlib import Path
from typing import Any, Dict, List

from python_pubsub_scanner.analyze_event_flow import EventFlowAnalyzer
from python_pubsub_scanner.anomaly_detector import AnomalyDetector


def main():
    """Run anomaly detection on your event flow."""
    # Configure paths (update these to match your project)
    agents_dir = Path("./python_pubsub_risk/agents")
    events_dir = Path("./python_pubsub_risk/events")

    if not agents_dir.exists() or not events_dir.exists():
        print("❌ Error: Please update the paths in this script to match your project structure")
        print(f"   agents_dir: {agents_dir.absolute()}")
        print(f"   events_dir: {events_dir.absolute()}")
        return

    print("🔍 Analyzing event flow...")
    print(f"   Agents: {agents_dir}")
    print(f"   Events: {events_dir}")
    print()

    # Step 1: Analyze the event flow
    analyzer = EventFlowAnalyzer(agents_dir, events_dir)
    analyzer.analyze()

    events = analyzer.get_all_events()
    agents = analyzer.get_all_agents()
    print(f"📊 Found {len(events)} events and {len(agents)} agents")
    print()

    # Step 2: Detect anomalies
    print("🔎 Detecting anomalies...")
    detector = AnomalyDetector(analyzer)
    anomalies: Dict[str, List[Dict[str, Any]]] = detector.detect_all()
    summary: Dict[str, int] = detector.get_anomaly_summary()

    # Step 3: Display results
    print()
    print("=" * 60)
    print("ANOMALY DETECTION REPORT")
    print("=" * 60)
    print()

    # Summary
    print(f"📋 Summary:")
    print(f"   • Total anomalies: {summary['total_anomalies']}")
    print(f"   • Orphaned events: {summary['orphaned_events_count']}")
    print(f"   • Circular dependencies: {summary['cycles_count']}")
    print(f"   • Isolated agents: {summary['isolated_agents_count']}")
    print()

    # Orphaned Events
    orphaned_events = anomalies.get('orphaned_events', [])
    if orphaned_events:
        print("🔴 Orphaned Events:")
        print("-" * 60)
        for orphan in orphaned_events:
            severity_icon = "⚠️ " if orphan.get('severity') == 'warning' else "ℹ️ "
            print(f"{severity_icon} {orphan.get('event', 'Unknown')} ({orphan.get('namespace', 'Unknown')})")
            print(f"   Type: {orphan.get('type', 'Unknown')}")
            print(f"   {orphan.get('message', '')}")
            print()
    else:
        print("✅ No orphaned events detected")
        print()

    # Cycles
    cycles = anomalies.get('cycles', [])
    if cycles:
        print("🔄 Circular Dependencies:")
        print("-" * 60)
        for cycle in cycles:
            print(f"⚠️  {cycle.get('message', 'Cycle detected')}")
            print(f"   Cycle path:")
            path = cycle.get('path', [])
            for step in path:
                print(f"      → {step.get('agent', 'Unknown')} ({step.get('namespace', 'Unknown')})")
                publishes = step.get('publishes', [])
                if publishes:
                    print(f"        publishes: {', '.join(publishes)}")
            print()
    else:
        print("✅ No circular dependencies detected")
        print()

    # Isolated Agents
    isolated_agents = anomalies.get('isolated_agents', [])
    if isolated_agents:
        print("🔌 Isolated Agents:")
        print("-" * 60)
        for isolated in isolated_agents:
            print(f"ℹ️  {isolated.get('agent', 'Unknown')} ({isolated.get('namespace', 'Unknown')})")
            print(f"   {isolated.get('message', '')}")
            print()
    else:
        print("✅ No isolated agents detected")
        print()

    # Recommendations
    if summary['total_anomalies'] > 0:
        print("=" * 60)
        print("💡 RECOMMENDATIONS")
        print("=" * 60)
        print()

        if summary['orphaned_events_count'] > 0:
            print("📝 Orphaned Events:")
            print("   1. Review events marked as 'never_published' - they may be dead code")
            print("   2. Check if 'never_subscribed' events are intentional")
            print("   3. Consider removing unused event definitions")
            print()

        if summary['cycles_count'] > 0:
            print("📝 Circular Dependencies:")
            print("   1. Review if the cycles are intentional")
            print("   2. Ensure proper termination conditions exist")
            print("   3. Consider breaking cycles with queue-based decoupling")
            print("   4. Add circuit breakers if needed")
            print()

        if summary['isolated_agents_count'] > 0:
            print("📝 Isolated Agents:")
            print("   1. Verify if these agents are still needed")
            print("   2. Check for configuration issues")
            print("   3. Consider removing or relocating unused agents")
            print()

    print("=" * 60)
    print("✅ Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
