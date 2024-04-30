# study...
# I would like to build more basing on my previous App, wish to learn more about RAG and fine-tuning

import os
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the API
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Define the model
model = genai.GenerativeModel('gemini-pro')

# Function to generate content
def generate_content(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {str(e)}"

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
            text-align: left;
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
st.image("images/archicollage.jpg") 

# Chat history display area
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# Display chat messages
chat_container = st.container()
with chat_container:
    for idx, message in enumerate(st.session_state.chat_messages):
        # User messages on the right
        if message.startswith("You:"):
            st.markdown(f"<div class='chat-message user-message'>{message[4:]}</div>", unsafe_allow_html=True)
        # AI responses on the left
        else:
            st.markdown(f"<div class='chat-message ai-message'>{message[3:]}</div>", unsafe_allow_html=True)

# Chat input area
with st.form("chat_form"):
    user_input = st.text_input("Get your architectural inspirations!! :", key="input_text", placeholder="Type a message...")
    submit_button = st.form_submit_button("Send")

if submit_button and user_input:
    st.session_state.chat_messages.append(f"You: {user_input}")
    ai_response = generate_content(user_input)
    st.session_state.chat_messages.append(f"AI: {ai_response}")
    # This will re-run the script, thus updating the chat
    st.experimental_rerun()