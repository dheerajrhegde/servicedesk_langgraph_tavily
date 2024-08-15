# Service Desk Automation Application

This application automates technical support interactions through a chat interface. It integrates with various APIs and services to facilitate ticket creation, knowledge article management, and intelligent response generation using natural language processing.

## Overview

The Service Desk Automation Application provides automated support for users' technical issues by leveraging the following functionalities:

- **ServiceNow Integration:** Allows creating incidents and knowledge articles directly in ServiceNow.
- **Tavily Integration:** Provides real-time web search capabilities to fetch the latest information on technical topics.
- **OpenAI Integration:** Uses a language model (LLM) from OpenAI for intelligent responses and conversation management.
- **Streamlit Interface:** Offers an interactive web application interface for users to interact with the service desk.

## Features

- **Ticket Creation:** Users can create incidents in ServiceNow by providing a short description and detailed steps.
- **Knowledge Article Creation:** Allows users to draft knowledge articles in ServiceNow based on resolved queries.
- **Real-time Help Search:** Provides detailed instructions and help based on user queries using Tavily.
- **Interactive Chat Interface:** Offers a user-friendly chat interface to communicate with the service desk.

## Cigna API Integration

The application integrates with the Cigna API to authenticate users and access patient information, enhancing user-specific interactions.

## Tech Stack

- **Streamlit**: For building the interactive web application.
- **Langchain**: Extends the capabilities of the language model with tools.
- **LangGraph**: Manages workflows and integrations.
- **OpenAI**: Provides natural language processing and responses.
- **ServiceNow APIs**: Manages ticketing and knowledge management.
- **Tavily**: Provides real-time web search and information retrieval.

## ServiceNow
Get your instance at https://developer.servicenow.com/dev.do#!/home. Get user name, apssword and base url.

## Installation

1. Clone the repository:

   ```bash
   git clone <repository_url>
   cd service-desk-automation

2. Install dependencies:

    ```bash
    pip install -r requirements.txt


3. Set up environment variables:
Create a .env file in the root directory. Define the following variables in the .env file:

    ```bash
    CIGNA_CLIENT_ID=<your_cigna_client_id>
    CIGNA_CLIENT_SECRET=<your_cigna_client_secret>
    TAVILY_API_KEY=<your_tavily_api_key>
    OPENAI_API_KEY=<your_openai_api_key>
    SERVICENOW_BASE_URL=<your_servicenow_base_url>
    SERVICENOW_USER=<your_servicenow_user>
    SERVICENOW_PASSWORD=<your_servicenow_password>

4. Run the application:

    ```bash
    streamlit run streamlit_app.py

5. Access the application:
Open a web browser and go to http://localhost:8501 to interact with the Service Desk Automation Application.

## Usage
- **Login with Cigna**: Users can authenticate using Cigna credentials to access personalized support.
- **Chat Interface**: Use the chat interface to communicate with the service desk, ask questions, and receive automated responses.
- **File Upload**: Upload images for assistance; the system will attempt to interpret and provide relevant support.
- **Interaction Completion**: Upon resolving a user query, the system automatically creates a ServiceNow ticket and knowledge article, providing the user with reference information.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Sample
<img width="1551" alt="image" src="https://github.com/dheerajrhegde/servicedesk_langgraph_tavily/assets/90691324/fbfdf1c6-fe1c-402e-9b34-1ebf0412aaf5">

