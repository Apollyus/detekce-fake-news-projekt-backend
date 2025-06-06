from openai import OpenAI
from source.modules.config import config  # Import the config instance, not the module

api_key = config.OPENAI_API_KEY  # Use the API key from the config

# Initialize with api_key as a named parameter
client = OpenAI(api_key=api_key)

def get_response(prompt):
    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search_preview"}],
        input=[
        {
        "role": "system", 
        "content": '''
            You are an AI assistant specialized in fact-checking news articles. For each news claim provided, perform a web search to gather the most recent and relevant information. 
            Assess the claim's veracity based on the search results, and categorize it as 'True', 'False', or 'Uncertain'. 
            
            Provide a concise explanation supporting your assessment, including references to the sources consulted.            
                '''
        },
        {
        "role": "user",
        "content": f"{prompt}"
        }
    ]
    )
    return response

# print(response.output_text)