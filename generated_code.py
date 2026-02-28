import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Task
from composio import Composio
from composio_crewai import CrewAIProvider

# Load environment variables from a .env file
load_dotenv()

# Retrieve Composio and Slack integration tokens from environment variables
COMPOSIO_API_KEY = os.getenv('COMPOSIO_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CREWAI_PLATFORM_INTEGRATION_TOKEN = os.getenv('CREWAI_PLATFORM_INTEGRATION_TOKEN')

# Validate that all necessary environment variables are set
if not COMPOSIO_API_KEY or not OPENAI_API_KEY or not CREWAI_PLATFORM_INTEGRATION_TOKEN:
    raise EnvironmentError("Required environment variables are not set")

def create_and_execute_slack_agent():
    try:
        # Initialize Composio with CrewAI provider
        composio = Composio(provider=CrewAIProvider())
        
        # Create a new session
        session = composio.create(user_id="user_123")
        tools = session.tools()
        
        # Create a Slack agent
        slack_agent = Agent(
            role="Team Communication Manager",
            goal="Facilitate team communication and coordinate collaboration efficiently",
            backstory="An AI assistant specialized in team communication and workspace coordination.",
            apps=['slack']  # Enable all Slack actions
        )
    
        # Define a task for the agent to send a Slack message
        update_task = Task(
            description="Send a project status update to the #general channel with current progress",
            agent=slack_agent,
            expected_output="Project update message sent successfully to team channel"
        )
    
        # Initialize a crew with the agent and task, then kick off the task
        crew = Crew(
            agents=[slack_agent],
            tasks=[update_task]
        )
        
        # Start executing the task
        crew.kickoff()
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the script if executed directly
if __name__ == '__main__':
    create_and_execute_slack_agent()