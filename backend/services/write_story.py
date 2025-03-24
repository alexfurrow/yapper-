# from openai import OpenAI
# from flask import current_app
# import json, os
# from dotenv import load_dotenv
# from jinja2 import Environment, FileSystemLoader
# from extensions import db
# from backend.models.Page_Table import Page_Table
# from backend.models.Story_Table import Story_Table
# # Force reload the .env file
# load_dotenv(override=True)

# # Initialize the client with the API key from .env
# client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# def story_prompt(content):
#     try:        
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             response_format = {"type": "json_object"},
#             messages=[
#                 {"role": "system", "content":                  
#                  """
#                 You are an expert storyteller. You will be given a journal entry. Your job is to write a story that is a cohesive narrative of the events described in the entry.
#                 If the user does not provide enough information (e.g. testing behavior like "testtesttest" or empty entries like "I'm not sure what to write" or typographical error/gibberish like "paoidjfaosidfjaosdifj"), write "no story was available for this entry".
#                 Your output must be in JSON format. Limit your output to 100 words. 

#                 <Examples>
#                     User input:
#                         I arrived in town today. The air smelled of salt and damp wood, the kind that seeps into your clothes and lingers for hours. The drive here was long, the city shrinking behind me, replaced by winding roads carved into cliffs and glimpses of an endless gray ocean. I hadn't expected the town to be so quiet. Even the waves seem hesitant, pressing against the shore and retreating, never quite committing. Maybe that's why I came here—because I, too, have been caught between leaving and returning, belonging and disappearing.
#                     Output:
#                         {
#                             "story": "The town waited, hushed, as if holding its breath. The scent of salt clung to my skin, a reminder that I was here, though I still felt suspended—adrift between past and future. The ocean whispered its uncertainty, waves recoiling before they could claim the shore. I understood that hesitation. I had fled the city, yet I wasn’t sure I had truly arrived. But as I stepped onto the worn wooden pier, the tide surged forward, bold for the first time. Maybe, just maybe, I would find the courage to do the same."
#                         }
#                 </Examples>
#                 """
#                     },

#                 {"role": "user", "content": f"Write a story based on the following content: {content}."}
#             ],
#             max_tokens = 134,
#             temperature = 1
#         )
#         json_response = json.loads(response.choices[0].message.content)
#         story_txt = json_response.get('story', '')
#         return story_txt
#     except Exception as e:
#         print(f"OpenAI API error: {str(e)}")
#         return None 


# def write_story_and_write_to_db(entry_id, content):
#     """Main function to get content and extract plot, setting, and characters"""

#     # Write story based on content
#     story_txt = story_prompt(content)
#     if not story_txt:
#         return None

#     # Write story to Table
#     plot_set_char = Story_Table(
#         entry_id=entry_id, #change this to user_id, once user_id is implemented
#         story=story_txt
#     )

#     # Save to database
#     db.session.add(plot_set_char)
#     db.session.commit()

#     return plot_set_char.to_dict()


# #alright so I need to think this through - on one hand i just want to get a basic story to output. We can refine it later. Moreover, we want to basically design the system to feed in the max amount of input from the past entries.
# #and use the context window as the maximum amt of the story.
# #alternatively, we can build something where the ai debates what should be kept.
# #or we do a rag based solution, which feels like the best way to go, but the complexity of querying that to develop the story will be really challenging and interesting.
# #similarly, there's the graphRAG appraoch, which was published 1 year ago: https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/. ... 

# #for one, getting the story out should be good
# #then doing the graph rag to incorporate deeper stuff. 
# #i'm going to build stuff and then probably have to deconstruct it because i dont' quite have my mind wrapped around what needs to be done.
