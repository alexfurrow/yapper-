from openai import OpenAI
from flask import current_app
import json, os
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# Force reload the .env file
load_dotenv(override=True)

# Initialize the client with the API key from .env
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def process_text(content):
    try:        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format = {"type": "json_object"},
            messages=[
                {"role": "system", "content": """You are an expert as parsing people's natural thoughts into an organized set of ideas. if possible, order them in sequence from earlier to later. Your response must be in JSON format. 
                 
                 <Examples>
                 User input:
                    today i woke up and i had slept well but i didn't quite still feel energized. 
                    i was still feeling a little defeated from yesterday and i thought that maybe i should just take it easy to start. i had a few coffees, which was great, and i played some games of dota. 
                    i was playing well in the first game but basically got carried, and then i played 1 or two more where i just wasn't totally with it. 

                    I forgot to eat breakfast and so I ordered door dash. it was totally sinful because it was something that i promised myself i wouldn't do for the new year resolutions. 
                    but i have already forgiven myself, because i had a really hard week and it took a burden off me, plus i can afford it and it made me feel cared for, and like a reward. 
                    moreover, i had a chat with myself, and i am still committed to not ordering doordash as at all, and i recognized in my talk with myself that i was basically improving - 
                    last year i ended the year ordering it multiple times per week, maybe as many as 8 times a month, and this month i only ordered it 3 times. 
                    moreover, i haven't had as hard of a time this year. this was the first time this year i really hit the wall. that's good because it means im stretching myself. 
                    admittedly im stretching myself too far if i get to this point, but i think that's where the opportunity lies, i know next time how it feels and i can navigate it differently. 
                    
                    i knew when i was at the breaking point that i can still stick to my healthy behaviors, and that i will grow because i can stick to them when its hardest. and i know also that they will help me recover faster. 
                    also, i broke down crying, awfter which i felt a lot better, especially because i got my work done. and i will know that crying will come and help me out, so i dont have to look to a particular thing outside of me to get or feel better. 
                    for that it will help to get music
                 Output: 
                    Parsed entry: 
                        'In the morning, the user woke up. 
                        They did not feel energetic, and they were feeling defeated. 
                        They decided to take it easy with a few coffees and games of DOTA. 
                        They played well the first game, but their teammates carried the user to victory, meaning they were not playing as well as their teammates and they needed support of the other users.
                        They forgot to have breakfast, and they felt sinful about it. They had made a promsie to themselves that they wouldn't do so as a new year resolution.
                        The user was forgiving of themselves, though, because 
                        '

                    Insights: 'Music can help with emotional release. They are on a journey towards getting stronger and feeling better.'"""},
                {"role": "user", "content": f"Write a journal entry based on this information: {content}."}
            ],
            max_tokens = 4000,
            temperature = 1

        )
        json_response = json.loads(response.choices[0].message.content)
        story_text = json_response.get('story', '')
        return story_text
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None 