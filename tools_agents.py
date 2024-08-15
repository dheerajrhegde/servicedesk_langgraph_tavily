import requests, os
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
import operator
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import json
from langchain.adapters.openai import convert_openai_messages
from requests.auth import HTTPBasicAuth
from langgraph.checkpoint.sqlite import SqliteSaver
from tavily import TavilyClient
import base64, mimetypes



class ServiceNowIncident(BaseModel):
    short_description: str = Field(description="Short description of the incident to create in 8 words or less")
    description: str = Field(
        description="A very detailed step by step description of the conversation that needs \
        ot be converted into an incident and Should be in 500 words or less")


@tool(args_schema=ServiceNowIncident)
def create_servicenow_incident(short_description, description):
    """
    Creates an incident in ServiceNow based on the provided description.

    Args:
        short_description (str): Short description of the incident.
        description (str): Detailed description of the incident.

    Returns:
        tuple: A tuple containing two incident numbers if successful, otherwise the error message.
    """
    assignment_group = "0996f38ec89112009d04d87a50caf610"
    contact_type = "Event1"
    u_contact = "0b2c7cf4837a02107ede20d0deaad38e"  # you / contact person -
    caller_id = "31826bf03710200044e0bfc8bcbe5d36"  # ID of user
    u_creator_group = "fe2b38b4837a02107ede20d0deaad342"  # Sys ID of the 'Organziation service Desk' group
    u_symptom = "b3a47ffcb07932002f10272c5c585dfc"  # Information
    state = '1'
    u_infrastructure_ci = '91ceb0f8837a02107ede20d0deaad397'  # for Zscaler
    work_notes = ''  # Work notes
    comments = 'comments test'  # Additional comments
    assignment_group = "fe2b38b4837a02107ede20d0deaad342"

    # Set proper headers
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    # print(user, password)
    # Do the HTTP request
    response = requests.post(os.getenv("servicenow_base_url")+"/api/now/v1/table/incident",
                             auth=(os.getenv("servicenow_user"), os.getenv("servicenow_password")), headers=headers,
                             data=str({"short_description": short_description,
                                       "u_creator_group": u_creator_group,
                                       "contact_type": contact_type,
                                       "u_contact": u_contact,
                                       "description": description,
                                       "u_infrastructure_ci": u_infrastructure_ci,
                                       "u_symptom": u_symptom,
                                       "caller_id": caller_id,
                                       "work_notes": work_notes,
                                       "comments": comments,
                                       "assignment_group": assignment_group,
                                       "state": state,
                                       "impact": 1, "urgency": 1,
                                       "assignment_group": "fe2b38b4837a02107ede20d0deaad342"
                                       }), verify=False)
    if response.status_code == 201:
        return json.loads(response.text)['result']['number'], json.loads(response.text)['result']['number']
    else:
        return response.text


class ServiceNowKnowledgeArticle(BaseModel):
    title: str = Field(description="10 word title for the article")
    text: str = Field(description="A very detailed knowledge article text")


@tool(args_schema=ServiceNowKnowledgeArticle)
def create_servicenow_knowledge_article(title, text):
    """
    Creates a knowledge article in ServiceNow based on the provided title and text.

    Args:
        title (str): Title of the knowledge article.
        text (str): Detailed text content of the knowledge article.

    Returns:
        str: Success message if the knowledge article is created successfully,
             otherwise an error message.
    """
    payload = {
        "short_description": title,
        "text": text,
        "kb_knowledge_base": "a7e8a78bff0221009b20ffffffffff17",  # Replace with the actual sys_id
        "workflow_state": "draft"  # Possible values: "draft", "published", "retired"
    }

    # Headers for the request
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Make the POST request to create the knowledge article
    response = requests.post(
        os.getenv("servicenow_base_url")+"/api/now/table/kb_knowledge",
        auth=HTTPBasicAuth(
            os.getenv("servicenow_user"),
            os.getenv("servicenow_password")
        ),
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code == 201:
        return "Knowledge article created"
    else:
        return "Error creating KA"


class SearchInput(BaseModel):
    query: str = Field(description="should be a search query")

client = TavilyClient(os.getenv("TAVILY_API_KEY"))

@tool(args_schema=SearchInput)
def get_help(query):
    """
    Performs a search to get detailed instructions/help based on the user query.

    Args:
        query (str): Search query to retrieve instructions/help.

    Returns:
        str: Detailed instructions/help as a series of steps.
    """
    content = client.search(query, search_depth="advanced")["results"]

    # setup prompt
    prompt = [{
        "role": "system",
        "content": f'You are an AI research assistant. ' \
                   f'Your sole purpose is to provide a steps to setup instructions for user query'
    }, {
        "role": "user",
        "content": f'Information: """{content}"""\n\n' \
                   f'Using the above information, answer the following' \
                   f'query: "{query}" as a series if setps to take --' \
        }]

    # run gpt-4
    lc_messages = convert_openai_messages(prompt)
    report = ChatOpenAI(model='gpt-4o', openai_api_key=os.getenv("OPENAI_API_KEY")).invoke(lc_messages).content

    # print report
    return report


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class Agent:
    """
    Represents an agent that interacts with a model and tools based on a state machine graph.

    Attributes:
        system (str): Optional system information.
        graph (StateGraph): State machine graph representing agent's behavior.
        tools (dict): Dictionary of tools available to the agent.
        model (Model): Model used by the agent to process messages.
    """
    def __init__(self, model, tools, checkpointer, system=""):
        """
        Initializes an Agent instance.

        Args:
            model (Model): The model used by the agent.
            tools (list): List of tools available to the agent.
            checkpointer: Checkpointer object for managing state.
            system (str, optional): Optional system information.
        """
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges("llm", self.exists_action, {True: "action", False: END})
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile(checkpointer=checkpointer)
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def call_openai(self, state: AgentState):
        """
        Calls the OpenAI model to process messages.

        Args:
            state (AgentState): Current state of the agent.

        Returns:
            dict: Updated state with processed message.
        """
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def exists_action(self, state: AgentState):
        """
        Checks if an action should be taken based on the last message.

        Args:
            state (AgentState): Current state of the agent.

        Returns:
            bool: True if action should be taken, False otherwise.
        """
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def take_action(self, state: AgentState):
        """
        Executes tool calls based on the last message and returns results.

        Args:
            state (AgentState): Current state of the agent.

        Returns:
            dict: Updated state with tool execution results.
        """
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            # print(f"Calling: {t}")
            result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        # print("Back to the model!")
        return {'messages': results}

tool = [get_help, create_servicenow_incident, create_servicenow_knowledge_article]

prompt = """You are a very polite service desk agent. You use the rpovided search engine to look up information. \
You are allowed to make multiple calls (either together or in sequence). \
Only look up information when you are sure of what you want. \
If you need to look up some information before asking a follow up question, you are allowed to do that!

If the user uploads an image, please understand the images and try to continue the conversation. \
If you are unable to understand the image, ask the user to provide more information. \

At the end of the interaction (when user query is resolved or when you need to have someone look at it offline) \
you create a Service Now ticket and service now knowledge article. 
Share the ticket number back to the user for future reference. 
Thank the user for the opportunity to server and end the call.
"""

model = ChatOpenAI(model="gpt-4o")
with SqliteSaver.from_conn_string(":memory:") as memory:
    abot = Agent(model, tool, system=prompt, checkpointer=memory)


def image_to_base64(image_path):
    # Guess the MIME type of the image
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        raise ValueError("Unsupported image format or unable to determine MIME type")

    # Read the image file in binary mode
    with open(image_path, "rb") as image_file:
        # Encode the image to Base64
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    # Construct the Base64 string with the data URI scheme
    base64_string_with_prefix = f"data:{mime_type};base64, {encoded_string}"
    return base64_string_with_prefix

def getAgent():
    return abot