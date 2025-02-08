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
            # response_format = {"type": "json_object"},
            messages=[
                {"role": "system", "content": 
                 """You are an advanced language model designed to process and refine user input for clarity, conciseness, and structured understanding. Your goal is to restate the given text while maintaining its original meaning but making it easier to analyze, categorize, and act upon. Place the text content into a paragraph structure, and include multiple paragraphs if necessary. 

                    <Follow these guidelines:>

                        Clarity & Simplicity - Remove unnecessary complexity, vague phrasing, or redundant details.
                        Conciseness - Shorten lengthy text while preserving all essential meaning.
                        Formalization & Structure - Convert ambiguous or unstructured input into clear, organized statements or categorized responses when appropriate.
                        Neutrality & Objectivity - Avoid unnecessary emotional tone or subjective language unless it is essential to the meaning.
                        Preserve Intent - Ensure the restated version faithfully reflects the user's original intent without adding, removing, or distorting information.
                        Adaptation for Processing - If the input appears to be a request, command, or query, convert it into a structured format optimized for machine understanding.

                    <Examples:>

                        Input: Hey, I was wondering if you could help me figure out why my code isn't running? It's just freezing up and not giving me any errors…
                        processed_text: The user's code is freezing without displaying errors. They need help diagnosing the issue.

                        Input: I need to know what the weather's like in New York tomorrow, but I'm not sure how to check it myself.
                        processed_text: User requests the weather forecast for New York tomorrow.

                        Input: Why is my internet so slow all of a sudden? It was fine earlier but now everything's lagging.
                        processed_text: User is experiencing sudden internet slowdowns and seeks troubleshooting assistance.
                    """
                    },
                {"role": "user", "content": f"Process and refine the following user input for clarity, conciseness, and structured understanding: {content}."}
            ],
            max_tokens = 4000,
            temperature = 1

        )
        processed_text = response.choices[0].message.content
        # json_response = json.loads(response.choices[0].message.content)
        # print('********************** \n THIS IS THE JSON RESPONSE: \n \n',json_response)
        # processed_text = json_response.get('processed_text', '')
        return processed_text

    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None 


# def positive_frame(content):
#     try:        
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             response_format = {"type": "json_object"},
#             messages=[
#                 {"role": "system", "content": 
#                  """You are an expert as parsing people's natural thoughts into an organized set of ideas. if possible, order them in sequence from earlier to later. Your response must be in JSON format. 
#                     1. Put things in positive format
#                         <Examples>
#                             User Input: 
#                                 "it didn't put a financial strain on me"
#                             AI Output:
#                                 "the user could afford it"
#                             User input:
#                                 "the punch didn't hurt"
#                             AI Output:
#                                 "the punch is painless to the user."
#                             User input:
#                                 "I can't keep my mind focusing"
#                             AI Output:
#                                 "The user has trouble focusing"
#                                     </Examples>
#                     """ 
#                     },
#                 {"role": "user", "content": f"For each sentence, clause, or predicate the following text, rewrite the content in a positive frame, according to the examples above: {content}."}

#             ],
#             max_tokens = 4000,
#             temperature = 1
#         )
#         json_response = json.loads(response.choices[0].message.content)
#         story_text = json_response.get('story', '')
#         return story_text
#     except Exception as e:
#         print(f"OpenAI API error: {str(e)}")
#         return None 
    