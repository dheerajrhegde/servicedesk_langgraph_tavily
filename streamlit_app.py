import tools_agents, datetime, os, requests, json, base64
from io import StringIO
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
    token = st.session_state.token["access_token"]
    headers = {"Authorization":
                   f"Bearer {token}"
               }
    #url = "https://fhir.cigna.com/PatientAccess/v1/$userinfo"
    url = "https://fhir.cigna.com/PatientAccess/v1-devportal/$userinfo"
    jsonString = requests.get(url, headers=headers)
    data = json.loads(jsonString.content)
    user_id = data["parameter"][0]["valueString"]

    headers = {"Authorization":
                   f"Bearer {token}"
               }
    url = f"https://fhir.cigna.com/PatientAccess/v1-devportal/Patient?_id={user_id}"
    jsonString = requests.get(url, headers=headers)
    data = json.loads(jsonString.content)
    #st.write(data)

    st.write(data["entry"][0]["resource"]["name"][0]["given"][0])

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
            user = st.text_input("Your name", key="name", max_chars=50, value=data["entry"][0]["resource"]["name"][0]["given"][0])
            user_query = st.text_input("Message", key="user_query", max_chars=500)
            send_button = st.form_submit_button("Send")
            send_image = st.file_uploader("Choose a file")

            if send_button and  ( send_image or user_query):
                if send_image:
                    #bytes_data = StringIO(send_image.getvalue().decode("utf-8"))
                    file_bytestream = send_image.getvalue()
                    base64_encoded = base64.b64encode(file_bytestream).decode("utf-8")

                    base64_string_with_prefix = f"data:image/png;base64, {base64_encoded}"

                    messages = [HumanMessage(
                        content=[
                            {"type": "text",
                             "text": "This is image uploaded by user who needs support. Get information from image and continue with chat"},
                            {
                                "type": "image_url",
                                "image_url": {"url": base64_string_with_prefix},
                            },
                        ],
                    )]
                else:
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