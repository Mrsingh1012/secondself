import argparse
import datetime
import json
import os
import shutil
import uuid
import sys
import requests
from bs4 import BeautifulSoup

def generate_id():
    return str(uuid.uuid4())

def get_timestamp():
    return datetime.datetime.utcnow().isoformat() + "Z"

def extract_webpage_content(url):
    """
    Fetches the content of a URL and extracts the title and body text.
    Handles network errors gracefully.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.title.string.strip() if soup.title else url
        
        # Remove script and style elements
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.decompose()
            
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)
        
        return title, clean_text
    except Exception as e:
        print(f"Warning: Failed to fetch webpage content from {url}. Error: {e}", file=sys.stderr)
        return url, f"Failed to scrape webpage. Source URL: {url}\nError details: {e}"

def extract_file_content(file_path):
    """
    Extracts text content from PDF, DOCX, TXT, or MD files.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    ext = os.path.splitext(file_path)[1].lower()
    content = ""
    
    if ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    elif ext == '.pdf':
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            content = "\n".join(pages_text)
        except ImportError:
            print("Warning: pypdf not installed. Reading PDF as binary (no text extraction).", file=sys.stderr)
            content = "[PDF text extraction failed: pypdf not installed]"
        except Exception as e:
            print(f"Warning: PDF extraction failed: {e}", file=sys.stderr)
            content = f"[PDF text extraction failed: {e}]"
    elif ext == '.docx':
        try:
            import docx
            doc = docx.Document(file_path)
            content = "\n".join([p.text for p in doc.paragraphs])
        except ImportError:
            print("Warning: python-docx not installed. Reading DOCX as binary (no text extraction).", file=sys.stderr)
            content = "[DOCX text extraction failed: python-docx not installed]"
        except Exception as e:
            print(f"Warning: DOCX extraction failed: {e}", file=sys.stderr)
            content = f"[DOCX text extraction failed: {e}]"
    else:
        content = f"[Unsupported file type '{ext}'. Binary file captured without text extraction.]"
        
    return content

def capture_item(note=None, link=None, file_path=None, title=None):
    raw_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    item_id = generate_id()
    timestamp = get_timestamp()
    
    data = {
        "id": item_id,
        "timestamp": timestamp,
        "type": "",
        "title": title or "",
        "content": "",
        "metadata": {}
    }
    
    if note:
        data["type"] = "note"
        data["content"] = note
        if not data["title"]:
            data["title"] = note[:30] + "..." if len(note) > 30 else note
            
    elif link:
        data["type"] = "link"
        print(f"Scraping content from URL: {link}...")
        web_title, web_content = extract_webpage_content(link)
        data["content"] = web_content
        data["metadata"]["url"] = link
        if not data["title"]:
            data["title"] = web_title
            
    elif file_path:
        data["type"] = "file"
        filename = os.path.basename(file_path)
        data["metadata"]["original_filename"] = filename
        
        # Copy to attachments folder
        attachments_dir = os.path.join(raw_dir, "attachments")
        os.makedirs(attachments_dir, exist_ok=True)
        dest_path = os.path.join(attachments_dir, f"{item_id}_{filename}")
        shutil.copy2(file_path, dest_path)
        data["metadata"]["attachment_path"] = os.path.relpath(dest_path, start=os.path.dirname(os.path.abspath(__file__)))
        
        print(f"Parsing content from file: {filename}...")
        try:
            data["content"] = extract_file_content(file_path)
        except Exception as e:
            print(f"Error parsing file: {e}", file=sys.stderr)
            data["content"] = f"[File parsing failed: {e}]"
            
        if not data["title"]:
            data["title"] = filename
            
    else:
        raise ValueError("Must specify either --note, --link, or --file")
        
    # Write JSON capture to raw/
    out_file = os.path.join(raw_dir, f"{item_id}.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Success! Captured {data['type']} as ID: {item_id}")
    print(f"Saved to: {os.path.relpath(out_file)}")
    return data

def main():
    parser = argparse.ArgumentParser(description="Capture notes, links, or files into SecondSelf.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--note", type=str, help="Text note content to capture")
    group.add_argument("--link", type=str, help="URL link content to capture")
    group.add_argument("--file", type=str, help="Path of the file to capture")
    parser.add_argument("--title", type=str, help="Optional custom title for the captured item")
    
    args = parser.parse_args()
    
    try:
        capture_item(note=args.note, link=args.link, file_path=args.file, title=args.title)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
