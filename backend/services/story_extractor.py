
# from openai import OpenAI
# from flask import current_app
# import json, os
# from dotenv import load_dotenv
# from jinja2 import Environment, FileSystemLoader
# from extensions import db
# from backend.models.Page_Table import Page  
# from backend.models.Plot_Set_Char_Table import Plot_Set_Char_Table
# # Force reload the .env file
# load_dotenv(override=True)

# # Initialize the client with the API key from .env
# client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# def plot_set_char_prompt(content):
#     try:        
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             response_format = {"type": "json_object"},
#             messages=[
#                 {"role": "system", "content":                  
#                  """You are an expert literary analyst trained to extract key narrative elements from a series of journal entries. Your task is to carefully analyze the provided journal entries and identify key details related to setting, characters, and plot to create a structured summary. Focus on significant patterns, emotional undertones, and narrative progression rather than isolated details. You will store all extracted information in JSON format, ensuring that each element (setting, characters, and plot) is organized into key-value pairs.

#                  Instructions for Analysis
#                     Setting:
#                     The setting provides the context and atmosphere of the journal entries, shaping the events and emotions within them. Carefully analyze descriptions of locations, time periods, and environmental details that contribute to the mood of the narrative. Consider both explicit statements (e.g., "It was a cold winter morning in New York") and implied elements (e.g., "The streets were slick with ice, and my breath hung in the air like smoke" suggests winter).
#                     When extracting details about the setting, pay attention to:
#                         "physical_locations": A list of significant places described in the journal (e.g., "coastal town", "bookstore", "fog-covered streets").
#                         "time_period": If specified, include references to historical eras, seasons, or cultural contexts (e.g., "1920s", "autumn 2023", "distant future").
#                         "atmosphere_mood": A list of words or phrases that define the emotional and sensory tone of the setting (e.g., "melancholic", "isolated", "serene yet tense").
#                         "changes_in_setting": Describe any shifts in location, time, or environmental tone that influence the narrative (e.g., "move from city to countryside").
#                         "summary": A concise summary of the setting.
#                        Your goal is to summarize the setting in a way that captures not just the physical space, but the sensory details, emotional weight, and symbolic meaning it holds.

#                     Characters:
#                     Identify and extract key individuals from the journal, detailing their roles, personalities, and development over time. Each character should be stored as a structured entry in JSON format.
#                     Each character should have the following attributes:
#                     "identity_role": Name (if given) and role in the journal (e.g., "Elena - protagonist, reserved artist", "Marco - bartender, unpredictable friend").
#                     "personality_motivations": A list of defining traits and what drives them (e.g., "withdrawn but observant", "seeks distraction through others").
#                     "relationships": How they interact with the narrator or other characters (e.g., "friend and emotional catalyst for protagonist").
#                     "character_arc": Describe how they change over time, if applicable (e.g., "begins as distant but later seeks connection").
#                     "symbolism_meaning": Any deeper thematic significance they might hold (e.g., "represents nostalgia and the struggle between isolation and connection").

#                     Plot:
#                     The plot of the journal is the sequence of events that unfold over time, as well as the conflicts and emotions that drive these events. Unlike a traditional story, journal entries often lack a structured beginning, middle, and end, so it is important to piece together a coherent narrative arc based on recurring events, changes in emotion, and key turning points.

#                     Summarize the major events, conflicts, and themes of the journal entries in a structured manner.

#                     Organize the plot as follows:

#                         "major_events": A list of key moments from the journal (e.g., "Elena moves to coastal town", "first encounter with Marco", "discovers hidden truth about past").
#                         "themes_motifs": A list of recurring ideas that shape the journal's meaning (e.g., "solitude vs. connection", "healing through art").
#                         "conflict_resolution": Identify major conflicts (internal or external) and whether they are resolved or remain open-ended (e.g., "struggles with trust after past betrayal, no clear resolution").
#                         "emotional_highs_lows": Capture moments of joy, grief, realization, or emotional shifts (e.g., "deep loneliness in early entries, growing warmth in later reflections").
#                         "narrative_progression": Describe whether the journal follows a linear change, cyclical repetition, or fragmented introspection (e.g., "progresses from isolation to tentative connection").
#                  <Examples>
#                     User input:
#                         I arrived in town today. The air smelled of salt and damp wood, the kind that seeps into your clothes and lingers for hours. The drive here was long, the city shrinking behind me, replaced by winding roads carved into cliffs and glimpses of an endless gray ocean. I hadn't expected the town to be so quiet. Even the waves seem hesitant, pressing against the shore and retreating, never quite committing. Maybe that's why I came here—because I, too, have been caught between leaving and returning, belonging and disappearing.
#                         The house I rented is small but serviceable. A single bedroom, an old iron stove, a rickety wooden deck that looks out onto the water. The previous tenant left behind a cracked porcelain teacup in the cupboard, and for some reason, it feels like a relic of something important. I should throw it out, but I don't. Instead, I unpacked my sketchbook, arranged my pencils in a row on the table, and tried to draw the coastline. The cliffs were easy. The waves, not so much.
#                         I needed a break. Walking into town felt like stepping into another era—narrow streets lined with buildings that haven't changed in decades. The bookstore caught my eye first. It had no sign, only a window stacked with old, leather-bound novels, their spines faded by years of sunlight. Inside, the scent of aged paper wrapped around me like a familiar memory.
#                         That's where I met Mrs. Patel.
#                         She was behind the counter, reading with the kind of quiet focus that made me hesitant to interrupt. But when I did, she looked up with kind, intelligent eyes and smiled like she'd been expecting me. She didn't ask many questions, just studied me for a moment before saying, “You'll like it here. The town is slow, but it has a way of giving you what you need.”
#                         I didn't tell her I wasn't sure what I needed.
#                         I bought a book—a collection of poems by someone I've never heard of, but the words on the back cover felt like they had been written just for me. Mrs. Patel slipped a pressed flower between the pages before handing it to me. “For good luck,” she said.
#                         I should have gone home after that, but something pulled me further down the street. That's when I found the bar. Or maybe, when I found Marco.
#                         It wasn't particularly crowded, but the low hum of conversation filled the space with warmth. The bartender—Marco, I would later learn—moved behind the counter with a kind of easy confidence, the kind that makes you wonder if he's ever known uncertainty. He caught me staring at the row of liquor bottles behind him and smirked.
#                         “New in town?”
#                         “That obvious?”
#                         He poured a drink I hadn't ordered and slid it toward me. “You don't look like the whiskey type, but trust me, you'll want this tonight.”
#                         I took a sip out of politeness and nearly coughed. Too strong. Too familiar.
#                         Marco laughed, leaning against the counter. “Told you.”
#                         I should have left then. I didn't. Instead, we talked—about nothing and everything. About the way the town slows down in winter, about the bookstore, about how some places feel like they're waiting for you to arrive. Marco didn't press when I dodged questions about why I came here, and I was grateful for that.
#                         I left before midnight. The walk home was colder than before, and I found myself clutching the book from Mrs. Patel's shop like a lifeline. The pressed flower was still there, delicate and whole.
#                         I don't know what I expected from this town. Maybe nothing. But something about today felt like the beginning of a story I didn't know I was writing.
#                         Maybe that's enough.

#                     Output:
#                     {
#                         "plot_set_char":
#                         {
#                             "setting": "physical locations include a coastal town, bookstore, fog-covered streets, and Marco's bar. The time period is autumn 2023. The atmosphere is melancholic, introspective, and serene yet tense. The changes in setting are a move from bustling city to isolated coastal town.",
#                             "characters": "the characters are Elena, Marco, and Mrs. Patel. Elena is the protagonist, a reserved artist who moves to a coastal town and forms a complicated friendship with Marco. Marco is a bartender who is unpredictable and emotionally evasive. Mrs. Patel is a wise bookstore owner who serves as a mentor figure to Elena.",
#                             "plot": "the plot is about Elena moving to a coastal town and forming a complicated friendship with Marco. Marco is a bartender who is unpredictable and emotionally evasive. Mrs. Patel is a wise bookstore owner who serves as a mentor figure to Elena."
#                         }
#                     }
#                 <\end Examples>       
#                     """
#                     },

#                 {"role": "user", "content": f"Extract the setting, character, and plot from the following text: {content}."}
#             ],
#             max_tokens = 4000,
#             temperature = 1
#         )
#         json_response = json.loads(response.choices[0].message.content)
#         plot_set_char_output = json_response.get('plot_set_char', '')
#         return plot_set_char_output
#     except Exception as e:
#         print(f"OpenAI API error: {str(e)}")
#         return None 


# def create_story_components_and_write_to_db(entry_id, content):
#     """Main function to get content and extract plot, setting, and characters"""

#     # Extract story components from processed content
#     psc = plot_set_char_prompt(content)
#     if not psc:
#         return None

#     # Create plot, setting, and character row in database
#     plot_set_char = Plot_Set_Char_Table(
#         entry_id=entry_id, #change this to user_id, once user_id is implemented
#         setting=psc['setting'],
#         characters=psc['characters'],
#         plot=psc['plot']
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
