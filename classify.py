import json
import os
import sys
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

def classify_content(content, title_hint=""):
    # Truncate content to avoid exceeding Groq TPM/context limits
    max_chars = 3500
    if len(content) > max_chars:
        content = content[:max_chars] + "\n... [truncated for LLM processing] ..."

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY is not set. Using local fallback classification.", file=sys.stderr)
        # Fallback heuristic classification
        words = content.lower().split()
        category = "Resources"
        if any(w in words for w in ["todo", "goal", "milestone", "plan", "project"]):
            category = "Projects"
        elif any(w in words for w in ["work", "personal", "health", "finance", "standard"]):
            category = "Areas"
        elif any(w in words for w in ["archive", "old", "completed", "done"]):
            category = "Archives"
            
        tags = ["auto-generated"]
        if title_hint:
            tags.append(title_hint.lower().replace(" ", "-"))
        
        return {
            "title": title_hint or (content[:30] + "..." if len(content) > 30 else content),
            "category": category,
            "tags": tags,
            "summary": "Fallback local classification (no LLM API key configured)."
        }
        
    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an expert organizer using the PARA framework (Projects, Areas, Resources, Archives).\n"
        "Categorize the user's content and extract metadata.\n"
        "Rule for Categories:\n"
        "- Projects: Active, goal-oriented efforts with a deadline (e.g. build a website, plan Q3 goals).\n"
        "- Areas: Ongoing responsibilities with standards, no end date (e.g. health, work, finance, standard operating procedures).\n"
        "- Resources: Topics of interest, references, and useful links (e.g. data science notes, coding references, wikipedia articles).\n"
        "- Archives: Inactive items, past projects, or completed goals.\n"
        "\n"
        "Return a valid JSON object only with this schema:\n"
        "{\n"
        "  \"title\": \"A concise, clean title under 60 chars\",\n"
        "  \"category\": \"Projects | Areas | Resources | Archives\",\n"
        "  \"tags\": [\"tag1\", \"tag2\"],\n"
        "  \"summary\": \"One-line summary under 120 chars\"\n"
        "}"
    )
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Content Title: {title_hint}\nContent:\n{content}"}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0.1
        )
        result_json = response.choices[0].message.content
        return json.loads(result_json)
    except Exception as e:
        print(f"Error calling Groq API: {e}. Falling back to default metadata.", file=sys.stderr)
        return {
            "title": title_hint or "Unclassified Note",
            "category": "Resources",
            "tags": ["uncategorized"],
            "summary": "Error during LLM classification."
        }

def run_classification():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, "raw")
    wiki_dir = os.path.join(base_dir, "wiki")
    
    os.makedirs(wiki_dir, exist_ok=True)
    
    if not os.path.exists(raw_dir):
        print("Error: raw/ folder does not exist. Run capture.py first.")
        return
        
    raw_files = [f for f in os.listdir(raw_dir) if f.endswith(".json")]
    
    if not raw_files:
        print("No raw captures found to classify.")
        return
        
    print(f"Found {len(raw_files)} raw files. Processing...")
    
    processed_count = 0
    for filename in raw_files:
        uuid_str = os.path.splitext(filename)[0]
        wiki_path = os.path.join(wiki_dir, f"{uuid_str}.md")
        
        # Incremental processing: skip already classified files
        if os.path.exists(wiki_path):
            continue
            
        raw_path = os.path.join(raw_dir, filename)
        with open(raw_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        print(f"\nClassifying [{raw_data['type']}] - {raw_data['title']}...")
        
        # Call classifier
        metadata = classify_content(raw_data["content"], title_hint=raw_data["title"])
        
        # Format markdown with YAML frontmatter
        markdown_content = (
            f"---\n"
            f"id: \"{raw_data['id']}\"\n"
            f"title: \"{metadata.get('title', raw_data['title'])}\"\n"
            f"category: \"{metadata.get('category', 'Resources')}\"\n"
            f"tags: {json.dumps(metadata.get('tags', []))}\n"
            f"summary: \"{metadata.get('summary', '')}\"\n"
            f"source_type: \"{raw_data['type']}\"\n"
            f"captured_at: \"{raw_data['timestamp']}\"\n"
            f"---\n\n"
            f"# {metadata.get('title', raw_data['title'])}\n\n"
            f"{raw_data['content']}\n\n"
            f"## Related Connections\n"
        )
        
        # Write to wiki/
        with open(wiki_path, 'w', encoding='utf-8') as wf:
            wf.write(markdown_content)
            
        print(f"Saved to: wiki/{uuid_str}.md (Category: {metadata.get('category')})")
        processed_count += 1
        
        # Rate limiting delay for Groq Free Tier
        if os.environ.get("GROQ_API_KEY"):
            import time
            time.sleep(2)
        
    print(f"\nClassification complete. Processed {processed_count} new item(s).")

if __name__ == "__main__":
    run_classification()
