from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")

# Initialize with api_key as a named parameter
client = OpenAI(api_key=api_key)

prompt=""

# Use chat.completions.create with proper message formatting
'''response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {
      "role": "system", 
      "content": "You are assistant for detection of fake news. You get string of text, maybe simple sentence, or news article od just a heading, you then write how likely is it true. Also tell why you think that and why not."
    },
    {
      "role": "user",
      "content": "Trump was re-elected as a president of US." # Replace with actual news text
    }
  ],
  tools=[{ "type": "web_search_preview" }]
)'''

response = client.responses.create(
    model="gpt-4o",
    tools=[{"type": "web_search_preview"}],
    input=[
    {
      "role": "system", 
      "content": "You are assistant for detection of fake news. You get string of text, maybe simple sentence, or news article od just a heading, you then write how likely is it true. Also tell why you think that and why not. Before any conlusion, you can use web search preview tool to get more information and then decide."
    },
    {
      "role": "user",
      "content": '''
        Scientists found life on Mars. They discovered a new speciesof aliens.
      '''
    }
  ]
)

# Print the response content
print(response.output_text)