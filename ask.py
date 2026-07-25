import argparse
import os
import sys
import re
import numpy as np
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

def parse_wiki_file(filepath):
    """
    Parses a wiki file to extract title and body.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split frontmatter
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    
    title = os.path.basename(filepath)
    if match:
        frontmatter_str = match.group(1)
        body = match.group(2)
        # Try to find title in frontmatter
        title_match = re.search(r'title:\s*"(.*?)"', frontmatter_str)
        if title_match:
            title = title_match.group(1)
    else:
        body = content
        
    # Remove connections section from content context
    connections_header = "## Related Connections"
    if connections_header in body:
        body, _ = body.split(connections_header, 1)
        
    return title, body.strip()

def retrieve_context(query, top_k=3, similarity_threshold=0.30):
    """
    Retrieves the top_k notes most similar to the query.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wiki_dir = os.path.join(base_dir, "wiki")
    
    if not os.path.exists(wiki_dir):
        return []
        
    wiki_files = [f for f in os.listdir(wiki_dir) if f.endswith(".md") and f != ".gitkeep"]
    if not wiki_files:
        return []
        
    # Load embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_emb = model.encode(query, convert_to_numpy=True)
    
    notes_scores = []
    for filename in wiki_files:
        filepath = os.path.join(wiki_dir, filename)
        title, body = parse_wiki_file(filepath)
        
        if not body:
            continue
            
        note_emb = model.encode(body, convert_to_numpy=True)
        
        # Cosine similarity
        similarity = np.dot(query_emb, note_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(note_emb))
        
        notes_scores.append({
            "title": title,
            "filename": filename,
            "content": body,
            "score": float(similarity)
        })
        
    # Sort by score descending
    notes_scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Filter by threshold
    filtered_results = [n for n in notes_scores if n["score"] >= similarity_threshold]
    
    return filtered_results[:top_k]

def ask_brain(query):
    """
    Retrieves relevant notes and queries Groq to synthesize an answer.
    """
    # Retrieve context
    retrieved_notes = retrieve_context(query, top_k=3)
    
    if not retrieved_notes:
        return (
            "I could not find any notes in your Second Brain that are semantically relevant to your query.",
            []
        )
        
    # Build context string
    context_str = ""
    for idx, note in enumerate(retrieved_notes):
        context_str += f"\n---\nSource Note [{idx+1}]: {note['title']}\nContent:\n{note['content']}\n"
        
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Fallback offline synthesis
        answer = (
            "⚠️ **Warning**: GROQ_API_KEY is not set. Showing a search snippet fallback instead:\n\n"
            "Based on your notes, here are the most relevant snippets:\n\n"
        )
        for note in retrieved_notes:
            snippet = note['content'][:250] + "..." if len(note['content']) > 250 else note['content']
            answer += f"- **{note['title']}** (Similarity Score: {note['score']:.2f}):\n  > {snippet}\n\n"
        return answer, retrieved_notes
        
    # Query Groq API
    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are SecondSelf, the user's AI Second Brain.\n"
        "Synthesize a clear, concise, and helpful answer to the user's question using ONLY the provided note contexts.\n"
        "Cite the Source Note titles (e.g. 'According to [Note Title]...') when referencing their information.\n"
        "If the context does not contain enough information to answer the question, state that you cannot find the answer in the current brain notes."
    )
    
    user_prompt = f"Context Notes:\n{context_str}\n\nQuestion: {query}"
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3
        )
        answer = response.choices[0].message.content
        return answer, retrieved_notes
    except Exception as e:
        return f"Error synthesizing answer from Groq API: {e}", retrieved_notes

def main():
    parser = argparse.ArgumentParser(description="Query your SecondSelf AI Brain.")
    parser.add_argument("query", type=str, nargs="+", help="Natural language query to ask")
    
    args = parser.parse_args()
    query_str = " ".join(args.query)
    
    print(f"Querying brain for: '{query_str}'...\n")
    answer, sources = ask_brain(query_str)
    
    print("--- Answer ---")
    print(answer)
    print("\n--- Sources Referenced ---")
    for idx, source in enumerate(sources):
        print(f"[{idx+1}] {source['title']} (File: wiki/{source['filename']} | Similarity: {source['score']:.4f})")

if __name__ == "__main__":
    main()
