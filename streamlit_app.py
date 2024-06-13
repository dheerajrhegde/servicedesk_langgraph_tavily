import tools_agents, datetime
from langchain_core.messages import HumanMessage
import streamlit as st
# Set up the page configuration
st.set_page_config(
    page_title="Chat App",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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
st.title("Chat Application")

# Display the chat messages
st.subheader("Chat History")


# Input form for sending a new message
with st.form("message_form", clear_on_submit=True):
    user = st.text_input("Your name", key="name", max_chars=50, value="User")
    user_query = st.text_input("Message", key="user_query", max_chars=500)
    send_button = st.form_submit_button("Send")

    if send_button and user_query:
        print("inside if")
        add_message(user, user_query)
        valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')
        if user_query.endswith(valid_extensions):
            image_data = tools_agents.image_to_base64(user_query)
            messages = [HumanMessage(
                content=[
                    {"type": "text",
                     "text": "This is image uploaded by user who needs support. Get information from image"},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data},
                    },
                ],
            )]
        else:
            print("inside else block")
            messages = [tools_agents.HumanMessage(content=user_query)]

        result = st.session_state.abot.graph.invoke({"messages": messages}, st.session_state.thread)
        add_message("agent", result['messages'][-1].content)
        print("added message", user, result['messages'][-1].content)

display_messages()
# Streamlit application
st.write("---")
st.write("Simple chat application using Streamlit.")