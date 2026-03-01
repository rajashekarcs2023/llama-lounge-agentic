import os
from dotenv import load_dotenv
from composio_crewai import ComposioProvider
from composio import Composio
from crewai import Agent, Task, Crew

# Load environment variables from a .env file
load_dotenv()

# Retrieve API keys from environment variables
COMPOSIO_API_KEY = os.getenv('COMPOSIO_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CREWAI_PLATFORM_INTEGRATION_TOKEN = os.getenv('CREWAI_PLATFORM_INTEGRATION_TOKEN')

# Ensure all necessary environment variables are present
if not all([COMPOSIO_API_KEY, OPENAI_API_KEY, CREWAI_PLATFORM_INTEGRATION_TOKEN]):
    raise EnvironmentError("API keys or tokens missing. Ensure all environment variables are set properly.")

# Initialize Composio with the provider
composio = Composio(provider=ComposioProvider())

# Create a Composio session with Slack toolkit
try:
    session = composio.create(user_id="your_user_id", toolkits=["slack"])
    # Retrieve tools from the session
    tools = session.tools()
except Exception as e:
    print(f"An error occurred during session creation or tool retrieval: {e}")
    exit(1)

# Configure the Slack Agent within the CrewAI framework
slack_agent = Agent(
    role="Team Communication Manager",
    goal="Facilitate team communication and coordinate collaboration efficiently",
    backstory="An AI assistant specialized in team communication and workspace coordination.",
    apps=['slack'],
    tools=tools
)

# Define the task of sending a Slack message
message_task = Task(
    description="Send a welcome message to the #general channel",
    agent=slack_agent,
    expected_output="Welcome message sent successfully"
)

# Initialize Crew with the agent and task
crew = Crew(
    agents=[slack_agent],
    tasks=[message_task]
)

# Execute the task
try:
    crew.kickoff()
    print("Task executed successfully. Message sent to Slack.")
except Exception as e:
    print(f"An error occurred while executing the task: {e}")

# Entry point for the script execution
if __name__ == '__main__':
    print("Initializing CrewAI Agent with Slack Integration...")