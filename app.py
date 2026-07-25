import os
import json
import subprocess
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from ask import ask_brain

# Load environment variables
load_dotenv()

# Streamlit Page Config
st.set_page_config(
    page_title="SecondSelf — Your AI Second Brain",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Mode Premium Custom CSS
st.markdown("""
<style>
    /* Main container styling */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155 !important;
    }
    
    /* Chat message card styling */
    .chat-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .chat-user {
        border-left: 4px solid #3b82f6;
    }
    
    .chat-assistant {
        border-left: 4px solid #10b981;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #3b82f6 !important;
        color: white !important;
        border: None !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        background-color: #2563eb !important;
        box-shadow: 0 0 12px rgba(37, 99, 235, 0.4) !important;
        transform: translateY(-1px);
    }
    
    /* Custom divider */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #334155, transparent);
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to run pipeline scripts
def run_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        # Run classifier
        st.write("Sorting raw captures with Groq AI PARA Classifier...")
        subprocess.run([sys_python, os.path.join(base_dir, "classify.py")], check=True)
        # Run linker
        st.write("Computing sentence embeddings and auto-linking notes...")
        subprocess.run([sys_python, os.path.join(base_dir, "link.py")], check=True)
        # Run graph builder
        st.write("Rebuilding knowledge graph structure...")
        subprocess.run([sys_python, os.path.join(base_dir, "build_graph.py")], check=True)
        st.success("Second Brain successfully organized and graph compiled!")
        st.rerun()
    except Exception as e:
        st.error(f"Error running pipeline: {e}")

# Find python executable for subprocess calls
sys_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe")
if not os.path.exists(sys_python):
    sys_python = "python" # fallback

# Sidebar stats & controls
with st.sidebar:
    st.title("🧠 SecondSelf")
    st.subheader("Your AI Second Brain")
    
    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
    
    # Calculate stats
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, "raw")
    wiki_dir = os.path.join(base_dir, "wiki")
    
    num_raw = len([f for f in os.listdir(raw_dir) if f.endswith(".json")]) if os.path.exists(raw_dir) else 0
    num_wiki = len([f for f in os.listdir(wiki_dir) if f.endswith(".md") and f != ".gitkeep"]) if os.path.exists(wiki_dir) else 0
    
    st.metric("Raw Captures Ingested", num_raw)
    st.metric("Organized Wiki Notes", num_wiki)
    
    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
    
    # Run pipeline button
    st.write("### Actions")
    if st.button("Organize Second Brain (Classify + Link)"):
        with st.spinner("Processing..."):
            run_pipeline()
            
    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
    
    # Configs info
    st.write("### Settings")
    api_status = "🟢 Connected" if os.environ.get("GROQ_API_KEY") else "🔴 Offline Fallback"
    st.write(f"LLM Connection: **{api_status}**")
    st.write(f"Similarity Linker Threshold: **{os.environ.get('SIMILARITY_THRESHOLD', '0.50')}**")

# Load graph data
graph_path = os.path.join(base_dir, "graph.json")
graph_data = {"nodes": [], "edges": []}
if os.path.exists(graph_path):
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)

# Main layout split
col_chat, col_graph = st.columns([1, 1])

# Column 1: Q&A Chat Console
with col_chat:
    st.write("## 💬 Query Your Second Brain")
    
    # Session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    # Input box
    user_query = st.chat_input("Ask your brain anything (e.g. 'What are my goals for Q3?')")
    
    if user_query:
        # Add query to history
        st.session_state.chat_history.append({"role": "user", "text": user_query})
        
        # Get answer
        with st.spinner("Retrieving notes and synthesizing answer..."):
            answer, sources = ask_brain(user_query)
            st.session_state.chat_history.append({
                "role": "assistant",
                "text": answer,
                "sources": sources
            })
            
    # Render chat history
    for msg in reversed(st.session_state.chat_history):
        if msg["role"] == "user":
            st.markdown(
                f"<div class='chat-card chat-user'>"
                f"<b>You:</b><br/>{msg['text']}"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            sources_md = ""
            if msg.get("sources"):
                sources_md = "<br/><br/><small><b>Sources:</b> " + ", ".join([f"<i>{s['title']}</i>" for s in msg["sources"]]) + "</small>"
            
            st.markdown(
                f"<div class='chat-card chat-assistant'>"
                f"<b>SecondSelf:</b><br/>{msg['text']}{sources_md}"
                f"</div>",
                unsafe_allow_html=True
            )

# Column 2: Interactive Graph Visualization
with col_graph:
    st.write("## 🕸️ Knowledge Graph")
    
    if not graph_data["nodes"]:
        st.info("No knowledge graph compiled yet. Add notes/links and click 'Organize Second Brain'.")
    else:
        # Custom HTML/JS for vis-network.js rendering
        nodes_json = json.dumps(graph_data["nodes"])
        edges_json = json.dumps(graph_data["edges"])
        
        # Colors matching HSL / Sleek Theme
        group_colors = {
            "Projects": {"background": "#3b82f6", "border": "#2563eb", "highlight": {"background": "#60a5fa", "border": "#3b82f6"}},
            "Areas": {"background": "#10b981", "border": "#059669", "highlight": {"background": "#34d399", "border": "#10b981"}},
            "Resources": {"background": "#f59e0b", "border": "#d97706", "highlight": {"background": "#fbbf24", "border": "#f59e0b"}},
            "Archives": {"background": "#6b7280", "border": "#4b5563", "highlight": {"background": "#9ca3af", "border": "#6b7280"}}
        }
        
        vis_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style type="text/css">
                body {{
                    background-color: #0f172a;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                    font-family: sans-serif;
                }}
                #network {{
                    width: 100%;
                    height: 550px;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 12px;
                    background-color: #1e293b;
                }}
            </style>
        </head>
        <body>
            <div id="network"></div>
            <script type="text/javascript">
                var container = document.getElementById('network');
                var data = {{
                    nodes: new vis.DataSet({nodes_json}),
                    edges: new vis.DataSet({edges_json})
                }};
                var options = {{
                    nodes: {{
                        shape: 'dot',
                        font: {{
                            color: '#f8fafc',
                            size: 14,
                            face: 'Inter, sans-serif'
                        }},
                        borderWidth: 2,
                        shadow: true
                    }},
                    edges: {{
                        color: {{
                            color: '#475569',
                            highlight: '#3b82f6',
                            hover: '#3b82f6'
                        }},
                        width: 1.5,
                        hoverWidth: 3,
                        shadow: false
                    }},
                    groups: {json.dumps(group_colors)},
                    interaction: {{
                        hover: true,
                        tooltipDelay: 200,
                        dragNodes: true,
                        zoomView: true
                    }},
                    physics: {{
                        stabilization: {{
                            enabled: true,
                            iterations: 150
                        }},
                        barnesHut: {{
                            gravitationalConstant: -8000,
                            springConstant: 0.04,
                            springLength: 95
                        }}
                    }}
                }};
                var network = new vis.Network(container, data, options);
            </script>
        </body>
        </html>
        """
        
        components.html(vis_html, height=580)
