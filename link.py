import os
import sys
import re
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# We try to import sentence-transformers and torch
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers is not installed. Please check environment setup.")
    sys.exit(1)

def parse_wiki_file(filepath):
    """
    Parses a wiki markdown file.
    Returns: frontmatter (dict/str), body (str), connections (list)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split frontmatter and body
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    
    if match:
        frontmatter_str = match.group(1)
        rest = match.group(2)
    else:
        frontmatter_str = ""
        rest = content
        
    # Split body and Related Connections section
    connections_header = "## Related Connections"
    if connections_header in rest:
        body, connections_part = rest.split(connections_header, 1)
        # Find all [[uuid]] links in connections_part
        connections = re.findall(r'\[\[([a-f0-9\-]+)\]\]', connections_part)
    else:
        body = rest
        connections = []
        
    return frontmatter_str, body.strip(), connections

def update_wiki_links(filepath, frontmatter_str, body_str, new_connections):
    """
    Writes back the markdown file with updated Related Connections.
    """
    markdown_content = f"---\n{frontmatter_str}\n---\n\n{body_str}\n\n## Related Connections\n"
    for conn in sorted(list(set(new_connections))):
        markdown_content += f"- [[{conn}]]\n"
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wiki_dir = os.path.join(base_dir, "wiki")
    
    if not os.path.exists(wiki_dir):
        print("Error: wiki/ folder does not exist. Run classify.py first.")
        return
        
    wiki_files = [f for f in os.listdir(wiki_dir) if f.endswith(".md") and f != ".gitkeep"]
    
    if len(wiki_files) < 2:
        print("Not enough wiki pages to link (need at least 2).")
        return
        
    print(f"Loading local SentenceTransformer model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    notes_data = []
    
    print("Reading wiki files and generating embeddings...")
    for filename in wiki_files:
        uuid_str = os.path.splitext(filename)[0]
        filepath = os.path.join(wiki_dir, filename)
        
        frontmatter_str, body_str, existing_connections = parse_wiki_file(filepath)
        
        # We compute embedding of the body text (excluding frontmatter)
        embedding = model.encode(body_str, convert_to_numpy=True)
        
        notes_data.append({
            "uuid": uuid_str,
            "filepath": filepath,
            "frontmatter": frontmatter_str,
            "body": body_str,
            "connections": set(existing_connections),
            "embedding": embedding
        })
        
    # Get similarity threshold from env
    threshold_str = os.environ.get("SIMILARITY_THRESHOLD", "0.50")
    try:
        threshold = float(threshold_str)
    except ValueError:
        threshold = 0.50
        
    print(f"Calculating similarities using threshold: {threshold}")
    
    num_notes = len(notes_data)
    links_added = 0
    
    for i in range(num_notes):
        for j in range(i + 1, num_notes):
            note1 = notes_data[i]
            note2 = notes_data[j]
            
            # Compute cosine similarity
            emb1 = note1["embedding"]
            emb2 = note2["embedding"]
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            if similarity >= threshold:
                # Add bidirectional link
                if note2["uuid"] not in note1["connections"]:
                    note1["connections"].add(note2["uuid"])
                    links_added += 1
                if note1["uuid"] not in note2["connections"]:
                    note2["connections"].add(note1["uuid"])
                    links_added += 1
                    
    # Write updates back to files
    print("Saving updated wiki notes...")
    for note in notes_data:
        update_wiki_links(note["filepath"], note["frontmatter"], note["body"], note["connections"])
        
    print(f"Linking complete. Added {links_added} new bidirectional link connection(s).")

if __name__ == "__main__":
    main()
