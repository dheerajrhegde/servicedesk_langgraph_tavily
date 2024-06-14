import tools_agents, datetime, os, requests, json
from langchain_core.messages import HumanMessage
import streamlit as st
from streamlit_oauth import OAuth2Component

# Set up the page configuration
st.set_page_config(
    page_title="Chat App",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CLIENT_ID = os.environ.get("CIGNA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CIGNA_CLIENT_SECRET")
AUTHORIZE_ENDPOINT = "https://r-hi2.cigna.com/mga/sps/oauth/oauth20/authorize"
TOKEN_ENDPOINT = "https://r-hi2.cigna.com/mga/sps/oauth/oauth20/token"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, TOKEN_ENDPOINT, TOKEN_ENDPOINT)
REDIRECT_URI = "https://dheeraj-servicedesk.streamlit.app/"
SCOPE = "openid fhirUser patient/*.read"

if 'token' not in st.session_state:
  result = oauth2.authorize_button(
      name="Continue with Cigna",
      icon="https://www.google.com.tw/favicon.ico",
      redirect_uri=REDIRECT_URI,
      scope=SCOPE,
      key="cigna",
      extras_params={"prompt": "consent", "access_type": "offline"},
      use_container_width=True,
      pkce='S256',
  )
  if result:
    st.session_state.token = result.get('token')
    st.rerun()
else:

    url = "https://fhir.cigna.com/PatientAccess/v1-devportal/Patient"
    jsonString = requests.get(url, heaaders={"Authorization": f"Bearer {str(st.session_state.token)}"})
    data = json.loads(jsonString.content)
    st.write(str(st.session_state.token))
    st.write(data)

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
    st.text("Service desk application that can heklp with user's technical queries.")
    st.text("Raises a service now ticket and then creates a knowledge article for the same.")
    st.text("tech stack - streamlit, langchain, langgraph, openai, servicenow cloud APIs")
    st.text("Uses langchain tools to give the LLM additional capability of creating service now tickets and knowledge articles.")
    st.text("Ise Tavily to search the web for latest information on the topic.")

    st.session_state.col1, st.session_state.col2 = st.columns([0.3, 0.7])

    # Input form for sending a new message
    with st.session_state.col1:
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

    with st.session_state.col2:
        # Display the chat messages
        st.subheader("Chat History")
        display_messages()

    # Streamlit application
    st.write("---")
    st.write("Simple chat application using Streamlit.")