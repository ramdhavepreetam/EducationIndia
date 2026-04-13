#!/bin/bash
# Usage: ./scripts/graphify-switch.sh backend|frontend|docs

GRAPH_DIR="graphify-out"
TARGET=$1

if [ -z "$TARGET" ]; then
  echo "Usage: $0 backend|frontend|docs"
  exit 1
fi

if [ ! -f "$GRAPH_DIR/$TARGET/graph.json" ]; then
  echo "No graph found at $GRAPH_DIR/$TARGET/graph.json"
  exit 1
fi

cp "$GRAPH_DIR/$TARGET/graph.json" "$GRAPH_DIR/graph.json"
echo "Active graph -> $TARGET ($(python3 -c "import json; g=json.load(open('$GRAPH_DIR/graph.json')); print(f'{len(g[\"nodes\"])} nodes, {len(g[\"links\"])} edges')" 2>/dev/null || echo 'graph.json copied'))"
