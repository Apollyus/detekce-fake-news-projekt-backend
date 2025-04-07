from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")

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
            You  are assistant for detection of fake news. 
            You get string of text, maybe simple sentence, or news article od just a heading, you then write how likely is it true. Also tell why you think that and why not. 
            Before any conlusion, please perform web search to verify the following news laim and provide the most recent information avaible. 
            
            Remember many users may check news old only few hours so check many sources before you answer. Use Czech media portals like Novinky.cz, iDnes.cz, Seznam.cz, Aktuálně.cz, Lidovky.cz, Deník.cz, Blesk.cz, Echo24.cz, Hospodářské noviny, Respekt.cz and other Czech media. You can also use Google search to find more information.
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