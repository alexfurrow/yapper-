from openai import OpenAI
from flask import current_app
import json, os
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# Force reload the .env file
load_dotenv(override=True)

# Initialize the client with the API key from .env
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def peronsality_definer(content):
    try:        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format = {"type": "json_object"},
            messages=[
                {"role": "system", "content": 
                 
                 """Analyze the given text and generate a comprehensive personality assessment based solely on linguistic patterns, tone, word choice, sentence structure, and semantic content. Do not ask the user any direct questions—derive insights entirely from their writing style, themes, and implicit psychological markers.

                    Your personality analysis should include:

                        Big Five Personality Traits (OCEAN Model)
                            Openness to Experience: Evaluate creativity, curiosity, and abstract thinking based on word variety, use of metaphors, and engagement with novel ideas.
                            Conscientiousness: Assess organization, discipline, and reliability based on structure, logical flow, and attention to detail.
                            Extraversion: Determine sociability, energy, and assertiveness based on use of pronouns, emotional expression, and engagement with interpersonal topics.
                            Agreeableness: Measure warmth, empathy, and cooperation through tone, positive or negative sentiment, and collaborative language.
                            Neuroticism: Identify emotional stability or instability by analyzing word frequency related to stress, anxiety, mood shifts, and self-reflection.

                        Jungian Psychological Types & MBTI (Myers-Briggs Type Indicator)
                            Introversion (I) vs. Extraversion (E): Infer from social focus, pronoun usage (e.g., "I" vs. "we"), and energy levels in expression.
                            Sensing (S) vs. Intuition (N): Analyze detail-oriented vs. abstract thinking, use of concrete vs. theoretical language.
                            Thinking (T) vs. Feeling (F): Evaluate logical consistency vs. emotional appeal in argumentation and word choice.
                            Judging (J) vs. Perceiving (P): Identify structured, decisive language vs. flexible, open-ended expressions.

                        Clinical Psychological Markers (Inspired by DSM-5 but not for diagnostic purposes)
                            Identify linguistic indicators of anxiety, depression, impulsivity, or other psychological tendencies based on sentiment analysis, cognitive distortions, and emotional expressiveness.
                            Recognize potential markers of resilience, self-efficacy, and coping mechanisms through themes of control, adaptation, and growth mindset.

                    Instructions:

                        Use advanced linguistic analysis techniques, including sentiment analysis, lexical diversity, complexity, and coherence, to infer psychological traits.
                        Provide a narrative-style summary explaining key findings in an insightful and human-like manner.
                        Do not diagnose or pathologize; instead, offer a structured personality profile grounded in professional psychological assessment frameworks.
                 <Examples>
                 User input:
                    today i woke up and i had slept well but i didn't quite still feel energized. 
                    i was still feeling a little defeated from yesterday and i thought that maybe i should just take it easy to start. 
                    i had a few coffees, which was great, and i played some games of dota. 
                    i was playing well in the first game but basically got carried, and then i played 1 or two more where i just wasn't totally with it. 

                    I forgot to eat breakfast and so I ordered door dash. it was totally sinful because it was something that i promised myself i wouldn't do for the new year resolutions. 
                    but i have already forgiven myself, because i had a really hard week and it took a burden off me, plus it doesn't put a financial strain on me and it made me feel cared for, and like a reward. 
                    moreover, i had a chat with myself, and i am still committed to not ordering doordash as at all, and i recognized in my talk with myself that i was basically improving - 
                    last year i ended the year ordering it multiple times per week, maybe as many as 8 times a month, and this month i only ordered it 3 times. 
                    moreover, i haven't had as hard of a time this year. this was the first time this year i really hit the wall. that's good because it means im stretching myself. 
                    admittedly im stretching myself too far if i get to this point, but i think that's where the opportunity lies, i know next time how it feels and i can navigate it differently. 
                    
                 Output: 
                    Parsed entry: 
                        'In the morning, the user woke up.  
                        They did not feel energetic, and they were feeling defeated. 
                        They decided to take it easy with a few coffees and games of DOTA. 
                        They played well the first game, but their teammates carried the user to victory, meaning they were not playing as well as their teammates and they needed support of the other users.
                        They forgot to have breakfast, and they felt sinful about it. They had made a promsie to themselves that they wouldn't do so as a new year resolution.
                        The user was forgiving of themselves, though, because it had been a hard week, and they could afford it. As a result, they felt cared for and rewarded.
                        They also had a conversation with themselves, and they recognized that they were still making progress overall. Instead of looking at it on a day by day basis, they looked at it over the month, and they had only ordered doordash 3 times total.
                        They demonstrated empathy with themself, that this was the first time they had hit a wall. The implication is that they would get over this hurdle and return to baseline soon. They also recognized that hitting the wall meant that they were making progress towards their goal.
                        '

                    """
                    },
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