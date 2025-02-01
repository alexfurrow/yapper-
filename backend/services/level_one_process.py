import openai
from flask import current_app

def process_text(content):
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        print("OpenAI API key not found in configuration")
        return None
        
    openai.api_key = api_key
    
    try:
        print(f"Sending request to OpenAI with content: {content[:50]}...")  # Debug print
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative story writer."},
                {"role": "user", "content": f"Write a story based on this information: {content}"}
            ]
        )
        processed_text = response.choices[0].message.content
        print(f"Received response from OpenAI: {processed_text[:50]}...")  # Debug print
        return processed_text
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None 