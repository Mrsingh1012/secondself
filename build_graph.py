import os
import re
import json
import yaml

def parse_yaml_frontmatter(content):
    """
    Extracts and parses the YAML frontmatter from a markdown file string.
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1))
            return frontmatter if isinstance(frontmatter, dict) else {}
        except Exception:
            return {}
    return {}

def extract_connections(content):
    """
    Extracts all [[uuid]] targets in the Related Connections section.
    """
    connections_header = "## Related Connections"
    if connections_header in content:
        _, connections_part = content.split(connections_header, 1)
        return re.findall(r'\[\[([a-f0-9\-]+)\]\]', connections_part)
    return []

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wiki_dir = os.path.join(base_dir, "wiki")
    output_path = os.path.join(base_dir, "graph.json")
    
    if not os.path.exists(wiki_dir):
        print("Error: wiki/ folder does not exist. Run classify.py first.")
        return
        
    wiki_files = [f for f in os.listdir(wiki_dir) if f.endswith(".md") and f != ".gitkeep"]
    
    nodes = []
    edges = []
    seen_edges = set()
    node_ids = set()
    
    # First pass: Gather nodes
    for filename in wiki_files:
        filepath = os.path.join(wiki_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        metadata = parse_yaml_frontmatter(content)
        uuid_str = metadata.get("id") or os.path.splitext(filename)[0]
        title = metadata.get("title") or uuid_str
        category = metadata.get("category") or "Resources"
        summary = metadata.get("summary") or "No summary available."
        
        node_ids.add(uuid_str)
        
        # Tooltip content (supports basic HTML rendering in vis-network)
        tooltip = (
            f"<b>Title:</b> {title}<br/>"
            f"<b>Category:</b> {category}<br/>"
            f"<b>Summary:</b> {summary}"
        )
        
        nodes.append({
            "id": uuid_str,
            "label": title,
            "group": category,
            "title": tooltip,
            "value": 1  # Default weight
        })
        
    # Second pass: Gather edges and calculate node degrees
    node_degrees = {nid: 0 for nid in node_ids}
    
    for filename in wiki_files:
        filepath = os.path.join(wiki_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        metadata = parse_yaml_frontmatter(content)
        from_id = metadata.get("id") or os.path.splitext(filename)[0]
        
        if from_id not in node_ids:
            continue
            
        connections = extract_connections(content)
        for to_id in connections:
            if to_id not in node_ids or from_id == to_id:
                continue  # Ignore dangling or self-looping links
                
            # Normalize edge to represent undirected connection
            edge_key = tuple(sorted([from_id, to_id]))
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append({
                    "from": edge_key[0],
                    "to": edge_key[1]
                })
                node_degrees[edge_key[0]] += 1
                node_degrees[edge_key[1]] += 1
                
    # Update node values (scaling size by connection degree + 1)
    for node in nodes:
        node["value"] = 5 + (node_degrees.get(node["id"], 0) * 2)
        
    graph_data = {
        "nodes": nodes,
        "edges": edges
    }
    
    # Save graph.json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
    print(f"Success! Generated graph with {len(nodes)} nodes and {len(edges)} edges.")
    print(f"Saved to: {os.path.relpath(output_path)}")

if __name__ == "__main__":
    main()
