from openai import OpenAI
from flask import current_app
import json, os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize the client with the API key from .env
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def process_text(content):
    try:
        # Debug print to see what key is being used
        print("Using API key:", os.environ.get('OPENAI_API_KEY')[:10] + "...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format = {"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a creative story writer."},
                {"role": "user", "content": f"Write a story based on this information: {content}"}
            ],
            max_tokens = 4000,
            temperature = 1
        )
        reply = response.choices[0].message.content
        return(reply)
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None