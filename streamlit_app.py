import tools_agents, datetime, base64
import streamlit as st

# Set up the page configuration
st.set_page_config(
    page_title="Chat App",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

markdown="""
### Overview
This application is designed to provide automated support for users' technical issues by:
- Raising ServiceNow tickets.
- Creating knowledge articles based on resolved queries.
- Using a Language Model (LLM) for intelligent responses.
- Fetching the latest information on technical topics.

### Tech Stack
- **Streamlit**: For building the interactive web application.
- **Langchain**: To extend the capabilities of the LLM with tools.
- **LangGraph**: For managing workflows and integrations.
- **OpenAI**: For natural language processing and responses.
- **ServiceNow Cloud APIs**: For ticketing and knowledge management.
- **Tavily**: For real-time web search and information retrieval.
"""





# Initialize session state to store chat messages
if "user_queries" not in st.session_state:
    st.session_state["user_queries"] = []
    st.session_state["abot"] = tools_agents.getAgent()
    st.session_state["thread"] = {"configurable": {"thread_id": "1"}}

# Function to add a new message to the chat
def add_message(user, text):
    st.session_state["user_queries"].append({
        "user": user,
        "text": text,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    })

# Function to display chat messages
def display_messages():
    for message in st.session_state["user_queries"][::-1]:
        st.write(f"[{message['time']}] {message['user']}: {message['text']}")

# Title of the app
st.title("Service Desk Chat Application")

# Creating 3 columns to display the chat interface
# Column 1 will display the overview of the application
# Column 2 will display the input form for sending a new message
# Column 3 will display the chat history
st.session_state.col1, st.session_state.col2, st.session_state.col3 = st.columns([0.3, 0.2, 0.5])

with st.session_state.col1:
    st.markdown(markdown)

# Input form for sending a new message
with st.session_state.col2:
    with st.form("message_form", clear_on_submit=True):

        user_query = st.text_input("Message", key="user_query", max_chars=500)
        send_image = st.file_uploader("Choose a file")
        send_button = st.form_submit_button("Send")

        # If the send button is clicked, add there is a message or image to send
        if send_button and  ( send_image or user_query):
            content = []
            if send_image:
                file_bytestream = send_image.getvalue()
                base64_encoded = base64.b64encode(file_bytestream).decode("utf-8")

                base64_string_with_prefix = f"data:image/png;base64, {base64_encoded}"
                content.append({"type": "text","text": "This is image uploaded by user who needs support. Get information from image and continue with chat"})
                content.append({
                            "type": "image_url",
                            "image_url": {"url": base64_string_with_prefix},
                        })

            if user_query:
                content.append({"type": "text",
                 "text": user_query})
                #content.append(user_query)
                add_message("user", user_query)

            messages = [tools_agents.HumanMessage(content=content)]
            result = st.session_state.abot.graph.invoke({"messages": messages}, st.session_state.thread)
            add_message("agent", result['messages'][-1].content)

# Display the chat history with latest messages on top
with st.session_state.col3:
    # Display the chat messages
    st.subheader("Chat History")
    display_messages()

# Streamlit application
st.write("---")
st.write("Simple chat application using Streamlit.")