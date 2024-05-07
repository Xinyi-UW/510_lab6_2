import os
import streamlit as st
import psycopg2
from dotenv import load_dotenv
from supabase import create_client, Client
from pyvis.network import Network
import networkx as nx

# Load environment variables
load_dotenv()

# Database URL from your provided environment
supabase_url = os.getenv("supabase_url")
supabase_key = os.getenv("supabase_key")

class Prompt:
    """Class to hold prompt details."""
    def __init__(self, title, prompt, is_favorite):
        self.title = title
        self.prompt = prompt
        self.is_favorite = is_favorite

def setup_database():
    """Setup database connection and initialize prompts table."""
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            is_favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    return con, cur

def prompt_form(prompt=None):
    """Create form to submit new prompts or edit existing ones."""
    default = Prompt("", "", False) if prompt is None else prompt
    with st.form(key="prompt_form", clear_on_submit=True):
        title = st.text_input("Title", value=default.title)
        prompt_content = st.text_area("Prompt", height=200, value=default.prompt)
        is_favorite = st.checkbox("Favorite", value=default.is_favorite)
        submitted = st.form_submit_button("Submit")
        if submitted and title and prompt_content:
            return Prompt(title, prompt_content, is_favorite)
        elif submitted:
            st.error('Please fill in both the title and prompt fields.')

def display_prompts(cur, con):
    """Display, search, and manage prompts."""
    search_query = st.text_input("Search prompts")
    sort_order = st.selectbox("Sort by", options=[
        "Created date (newest first)", "Created date (oldest first)",
        "Updated date (newest first)", "Updated date (oldest first)"
    ])
    order_query = {
        "Created date (newest first)": "ORDER BY created_at DESC",
        "Created date (oldest first)": "ORDER BY created_at ASC",
        "Updated date (newest first)": "ORDER BY updated_at DESC",
        "Updated date (oldest first)": "ORDER BY updated_at ASC"
    }[sort_order]
    cur.execute(f"SELECT * FROM prompts WHERE title LIKE %s {order_query}", ('%' + search_query + '%',))
    prompts = cur.fetchall()
    for p in prompts:
        with st.expander(f"{p[1]} (created at: {p[4]})"):
            title = st.text_input("Title", value=p[1], key=f"title{p[0]}")
            content = st.text_area("Content", value=p[2], height=200, key=f"content{p[0]}")
            is_favorite = st.checkbox("Favorite", value=p[3], key=f"fav{p[0]}")
            if st.button("Save Changes", key=f"save{p[0]}"):
                cur.execute("UPDATE prompts SET title = %s, prompt = %s, is_favorite = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s", 
                            (title, content, is_favorite, p[0]))
                con.commit()
                st.success("Updated successfully!")
            if st.button("Delete", key=f"delete{p[0]}"):
                cur.execute("DELETE FROM prompts WHERE id = %s", (p[0],))
                con.commit()
                st.experimental_rerun()

def generate_content(user_input):
    """Generate content using the Generative AI model (stub function)."""
    return f"Generated response for: {user_input}"

def store_in_supabase(user_input, ai_response):
    """Store user and AI conversation in Supabase."""
    data = {
        "prompt": user_input,
        "response": ai_response
    }
    try:
        response = supabase.table("architect_inspirations").insert(data).execute()
        if response.status_code != 201:
            st.error(f"Supabase insertion error: {response}")
    except Exception as e:
        st.error(f"Supabase API error: {str(e)}")

# Function to build a knowledge graph using data from Supabase
def create_knowledge_graph(output_file="knowledge_graph.html"):
    G = nx.Graph()
    root_node = "Architect Inspiration Playground"
    G.add_node(root_node)

    # Fetch data from Supabase
    supabase = create_client(supabase_url, supabase_key)
    try:
        records = supabase.table("architect_inspirations").select("*").execute().data
        for idx, record in enumerate(records):
            prompt = record["prompt"]
            response = record["response"]
            prompt_node = f"Prompt {idx + 1}: {prompt}"
            response_node = f"Response {idx + 1}: {response}"

            G.add_node(prompt_node)
            G.add_node(response_node)
            G.add_edge(root_node, prompt_node)
            G.add_edge(prompt_node, response_node)
    except Exception as e:
        st.error(f"Error retrieving data from Supabase: {str(e)}")

    # Create and visualize the graph
    net = Network(height="600px", width="100%", directed=True)
    net.from_nx(G)
    try:
        net.show(output_file)
    except Exception as e:
        st.error(f"Error generating graph HTML file: {str(e)}")

# Streamlit UI setup
st.set_page_config(page_title="Architect Inspiration Playground", page_icon=":speech_balloon:")
st.markdown("""
    <style>
        .chat-message {
            max-width: 60%;
            margin: 5px;
            padding: 10px;
            border-radius: 25px;
        }
        .user-message {
            background-color: #6E30EF;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .ai-message {
            background-color: #EDDE07;
            color: black;
            margin-right: auto;
            text-align: left.
        }
        .chat-container {
            background-color: #FFFFFF;
            border-radius: 5px;
            overflow-y: auto;
            padding: 10px;
            margin-bottom: 25px;
            max-height: 500px;
        }
        .stTextInput>div>div>input {
            color: white;
            background-color: #6E30EF;
        }
        h1 {
            color: #6E30EF;
            font-family: 'Comic Sans MS', 'Comic Neue', cursive;
        }
        body {
            background-color: white;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Architect Inspiration Playground")

# Initialize chat history if not already done
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_messages:
        # User messages on the right
        if message.startswith("You:"):
            st.markdown(f"<div class='chat-message user-message'>{message[4:]}</div>", unsafe_allow_html=True)
        # AI responses on the left
        else:
            st.markdown(f"<div class='chat-message ai-message'>{message[3:]}</div>", unsafe_allow_html=True)

# Chat input form
with st.form("chat_form"):
    user_input = st.text_input("Get your architectural inspirations!!", key="input_text", placeholder="Type a message...")
    submit_button = st.form_submit_button("Send")

if submit_button and user_input:
    st.session_state.chat_messages.append(f"You: {user_input}")
    ai_response = generate_content(user_input)
    st.session_state.chat_messages.append(f"AI: {ai_response}")

    # Store the conversation in Supabase
    store_in_supabase(user_input, ai_response)

    # Re-generate the knowledge graph
    create_knowledge_graph()

    # Re-run the Streamlit app
    st.experimental_rerun()

# Embed the graph in Streamlit
html_file_path = "knowledge_graph.html"
if os.path.exists(html_file_path):
    with open(html_file_path, "r") as f:
        st.components.v1.html(f.read(), height=650)
