# Anomaly Detection

The scanner includes automatic anomaly detection to identify potential issues in your event-driven architecture.

## Overview

Anomalies are automatically detected during each scan and included in the API payload under a new `anomalies` key. This feature is **non-invasive** and will not break existing integrations.

## Detected Anomalies

### 1. Orphaned Events

Events that are either never published or never subscribed to.

**Types:**
- **never_published** (severity: `warning`): Event is defined but no agent publishes it
  - May indicate dead code or incomplete implementation
- **never_subscribed** (severity: `info`): Event is published but no agent consumes it
  - May be intentional (fire-and-forget events) or indicate unused events

**Example:**
```json
{
  "event": "UserDeleted",
  "namespace": "user_service",
  "type": "never_subscribed",
  "severity": "info",
  "message": "Event 'UserDeleted' has no subscribers"
}
```

### 2. Circular Dependencies (Cycles)

Circular event dependencies where Agent A → Event X → Agent B → Event Y → Agent A.

**Severity:** `warning`

Cycles can cause:
- Infinite loops if not handled properly
- Performance issues
- Complex debugging scenarios
- State management challenges

**Example:**
```json
{
  "cycle": ["AgentA", "AgentB", "AgentA"],
  "path": [
    {
      "agent": "AgentA",
      "namespace": "service_a",
      "publishes": ["EventX"]
    },
    {
      "agent": "AgentB",
      "namespace": "service_b",
      "publishes": ["EventY"]
    }
  ],
  "severity": "warning",
  "message": "Circular dependency detected: AgentA -> AgentB -> AgentA"
}
```

### 3. Isolated Agents

Agents that have no connections (neither publish nor subscribe to any events).

**Severity:** `info`

May indicate:
- Dead code that should be removed
- Configuration error
- Agent that only performs internal operations (e.g., scheduled tasks)

**Example:**
```json
{
  "agent": "UnusedAgent",
  "namespace": "legacy",
  "severity": "info",
  "message": "Agent 'UnusedAgent' is isolated (no subscriptions or publications)"
}
```

## Payload Structure

The scanner adds a new `anomalies` key to the existing payload:

```json
{
  "graph_type": "complete",
  "dot_content": "digraph EventFlow { ... }",
  "stats": {
    "events": 45,
    "agents": 23,
    "connections": 87
  },
  "namespaces": ["bot_lifecycle", "market_data", "indicator"],

  "anomalies": {
    "summary": {
      "orphaned_events_count": 3,
      "cycles_count": 1,
      "isolated_agents_count": 2,
      "total_anomalies": 6
    },
    "details": {
      "orphaned_events": [
        {
          "event": "UserDeleted",
          "namespace": "user_service",
          "type": "never_subscribed",
          "severity": "info",
          "message": "Event 'UserDeleted' has no subscribers"
        },
        {
          "event": "OrderCreated",
          "namespace": "order_service",
          "type": "never_published",
          "severity": "warning",
          "message": "Event 'OrderCreated' is never published by any agent"
        }
      ],
      "cycles": [
        {
          "cycle": ["AgentA", "AgentB"],
          "path": [
            {
              "agent": "AgentA",
              "namespace": "service_a",
              "publishes": ["EventX"]
            },
            {
              "agent": "AgentB",
              "namespace": "service_b",
              "publishes": ["EventY"]
            }
          ],
          "severity": "warning",
          "message": "Circular dependency detected: AgentA -> AgentB -> AgentA"
        }
      ],
      "isolated_agents": [
        {
          "agent": "LegacyAgent",
          "namespace": "legacy",
          "severity": "info",
          "message": "Agent 'LegacyAgent' is isolated (no subscriptions or publications)"
        }
      ]
    }
  }
}
```

## Using Anomaly Detection

### Automatic Detection

Anomalies are detected automatically during `scan_once()`:

```python
from python_pubsub_scanner.scanner import EventFlowScanner

scanner = EventFlowScanner(agents_dir=agents_path, events_dir=events_path)
results = scanner.scan_once()

# Anomalies are included in the API payload
# Check console output for: "[SCAN] Detected X anomalies"
```

### Standalone Detection

You can also use the `AnomalyDetector` independently:

```python
from python_pubsub_scanner.analyze_event_flow import EventFlowAnalyzer
from python_pubsub_scanner.anomaly_detector import AnomalyDetector

# Analyze event flow
analyzer = EventFlowAnalyzer(agents_dir, events_dir)
analyzer.analyze()

# Detect anomalies
detector = AnomalyDetector(analyzer)
anomalies = detector.detect_all()

# Get summary
summary = detector.get_anomaly_summary()
print(f"Total anomalies: {summary['total_anomalies']}")

# Inspect details
for orphan in anomalies['orphaned_events']:
    print(f"⚠️  {orphan['message']}")

for cycle in anomalies['cycles']:
    print(f"🔄 {cycle['message']}")

for isolated in anomalies['isolated_agents']:
    print(f"ℹ️  {isolated['message']}")
```

## Filtering by Severity

You can filter anomalies by severity level:

```python
anomalies = detector.detect_all()

# Get only warnings
warnings = [
    a for a in anomalies['orphaned_events']
    if a['severity'] == 'warning'
]

# Get all warnings across all types
all_warnings = []
for anomaly_type, items in anomalies['details'].items():
    all_warnings.extend([a for a in items if a.get('severity') == 'warning'])
```

## Error Handling

Anomaly detection is wrapped in a try-except block to prevent failures from breaking the scan:

```python
# In scanner.py
try:
    detector = AnomalyDetector(analyzer)
    anomalies = detector.detect_all()
    payload['anomalies'] = {
        'summary': detector.get_anomaly_summary(),
        'details': anomalies
    }
except Exception as e:
    print(f"[SCAN] Warning: Failed to detect anomalies: {e}")
    # Continue without anomalies - no regression risk
```

If anomaly detection fails:
- The scan continues normally
- A warning is printed to the console
- The `anomalies` key is omitted from the payload
- No impact on existing functionality

## Best Practices

### Interpreting Results

1. **Orphaned Events - never_published (warning)**
   - Review the event definition
   - Check if it's dead code that should be removed
   - Ensure all publishers are properly registered

2. **Orphaned Events - never_subscribed (info)**
   - Confirm if the event is intentionally fire-and-forget
   - Consider if the event should be removed
   - Check for missing subscribers

3. **Cycles (warning)**
   - Review if the cycle is intentional
   - Ensure proper termination conditions exist
   - Consider breaking the cycle with queue-based decoupling
   - Add circuit breakers if needed

4. **Isolated Agents (info)**
   - Verify if the agent is still needed
   - Check for configuration issues
   - Consider if the agent should be moved or removed

### Monitoring

Set up alerts for anomaly thresholds:

```python
summary = detector.get_anomaly_summary()

# Alert if too many warnings
warning_events = [
    a for a in anomalies['orphaned_events']
    if a['severity'] == 'warning'
]
if len(warning_events) + len(anomalies['cycles']) > 5:
    send_alert("High number of critical anomalies detected")

# Track trends over time
store_metrics(
    timestamp=now(),
    total_anomalies=summary['total_anomalies'],
    cycles=summary['cycles_count']
)
```

## Limitations

1. **Cycle Detection**: Only detects direct cycles through the agent graph. Complex multi-hop cycles may not be detected.

2. **False Positives**:
   - Fire-and-forget events will appear as "never_subscribed"
   - Scheduled agents may appear as "isolated"
   - External event sources may cause "never_published" warnings

3. **Performance**: On very large codebases (1000+ agents), cycle detection may take a few seconds.

## Future Enhancements

Planned improvements (see TODO.md):
- Recommendations for fixing each anomaly type
- Confidence scores for anomalies
- Historical anomaly tracking
- Custom anomaly rules
- Integration with CI/CD for breaking builds on critical anomalies
