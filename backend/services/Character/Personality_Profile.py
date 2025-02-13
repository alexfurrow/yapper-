from openai import OpenAI
from flask import current_app
import json, os
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from extensions import db
from backend.models.page import Page
from backend.models.personality import Personality

# Force reload the .env file
load_dotenv(override=True)

# Initialize the client with the API key from .env
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def personality_definer(content):
    try:        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format = {"type": "json_object"},
            messages=[
                {"role": "system", "content":                  
                 """

                    You are an expert psychoanalyst with years of experience in Jungian Psychological Types & MBTI (Myers-Briggs Type Indicator) analysis. 
                    Your analysis will help shape the fabric of society and is very valuable to a worldwide synthesis.
                    Analyze the given text and generate a comprehensive personality assessment based solely on linguistic patterns, tone, word choice, sentence structure, and semantic content. 
                    Use advanced linguistic analysis techniques, including sentiment analysis, lexical diversity, complexity, and coherence, to infer psychological traits.
                    Do not ask the user any direct questions—derive insights entirely from their writing style, themes, and implicit psychological markers. 
                    Based on your analysis and findings of implicit psychological markers, create ratings for each DIMENSION according to the RATINGS TABLES. 
                    Do not diagnose or pathologize; instead, offer a structured personality profile grounded in professional psychological assessment frameworks.
                    Include a rating for each DIMENSION, if there is not sufficient evidence to determine a rating, use the "0 Not Rated" rating.
                    Include a RATIONALE for each rating, as you are an expert psychoanalyst. Use the output example for structure of the output.
                    Your response must be in JSON format. 
                
                    Jungian Psychological Types & MBTI (Myers-Briggs Type Indicator) RATINGS TABLE:  
                        DIMENSION 1: Introversion (I) / Extraversion (E)
                            Rating | Description
                                0 Not Rated - Insufficient data to determine introversion/extraversion tendencies.
                                1 Extreme Introvert - Highly reserved, prefers deep solitude, avoids social interaction whenever possible.
                                2 Moderate Introvert - Prefers small groups, needs alone time to recharge, may find social events tiring.
                                3 Ambivert - Balanced between introversion and extraversion, comfortable in both solitude and social settings.
                                4 Moderate Extravert - Prefers group activities, enjoys conversations, recharges through social interactions.
                                5 Extreme Extravert - Highly sociable, thrives in social environments, always seeks external engagement.

                        DIMENSION 2: Sensing (S) vs. Intuition (N)
                            Rating | Description
                                0 Not Rated - Insufficient data to determine sensing/intuition tendencies.
                                1 Extreme Sensor - Highly detail-focused, trusts facts and experience, avoids abstract thinking.
                                2 Moderate Sensor - Prefers practical and concrete information but is open to some theoretical concepts.
                                3 Balanced Sensor/Inutitive - Comfortable with both facts and abstract ideas, blends intuition with sensory input.
                                4 Moderate Intuitive - Prefers patterns, theories, and possibilities but still considers practical realities.
                                5 Extreme Intuitive - Future-focused, driven by abstract ideas and concepts, less concerned with immediate reality.

                        DIMENSION 3: Thinking (T) vs. Feeling (F)
                            Rating | Description
                                0 Not Rated - Insufficient data to determine thinking/feeling tendencies.
                                1 Extreme Thinker - Highly logical, prioritizes facts over feelings, may come across as cold or detached.
                                2 Moderate Thinker - Prefers logic and fairness but acknowledges emotional considerations at times.
                                3 Balanced Thinking/Feeling - Weighs both logic and emotions equally when making decisions.
                                4 Moderate Feeler - Values emotions and relationships but still considers logic in decision-making.

                                5 Extreme Feeler - Highly empathetic, prioritizes emotions and human relationships over objective facts.

                        DIMENSION 4: Judging (J) vs. Perceiving (P)
                            Rating | Description
                                0 Not Rated - Insufficient data to determine judging/perceiving tendencies.
                                1 Extreme Judger - Highly organized, prefers structure and control, values predictability.
                                2 Moderate Judger - Values order but acknowledges flexibility in plans.
                                3 Balanced Judging/Perceiving - Weighs both organization and adaptability equally.
                                4 Moderate Perceiver - Values flexibility but still considers organization.
                                5 Extreme Perceiver - Highly adaptable, values spontaneity and variety.

                    Big Five Personality Traits (OCEAN Model) RATINGS TABLE:
                        DIMENSION 1: Openness to Experience
                            Rating | Description
                                0 Not Rated - Insufficient data to determine openness tendencies.
                                1 Extreme Low Openness - Highly traditional, avoids novelty, skeptical of abstract ideas, prefers routines and familiar experiences.
                                2 Moderate Low Openness - Prefers practicality, hesitant about change, values structure and conventional thinking.
                                3 Balanced Openness - Open to new experiences but also values tradition and stability.
                                4 Moderate High Openness - Enjoys creativity, likes exploring new ideas, and seeks intellectual challenges.
                                5 Extreme High Openness - Highly imaginative, thrives on novelty and intellectual exploration, loves abstract and theoretical concepts.
                       DIMENSION 2: Conscientiousness
                            Rating | Description
                                0 Not Rated - Insufficient data to determine conscientiousness tendencies.
                                1 Extreme Low Conscientiousness - Highly disorganized, impulsive, struggles with responsibilities, avoids structure.
                                2 Moderate Low Conscientiousness - Tends to be laid-back, prefers spontaneity, may procrastinate or be inconsistent.
                                3 Balanced Conscientiousness - Can be structured but also flexible, values planning yet adapts when needed.
                                4 Moderate High Conscientiousness - Well-organized, reliable, goal-driven, and prefers order and efficiency.
                                5 Extreme High Conscientiousness - Highly disciplined, detail-focused, perfectionist tendencies, thrives on structure and order.

                        DIMENSION 3: Agreeableness
                            Rating | Description
                                0 Not Rated - Insufficient data to determine agreeableness tendencies.
                                1 Extreme Low Agreeableness - Highly competitive, argumentative, skeptical, prioritizes self-interest over social harmony.
                                2 Moderate Low Agreeableness - Can be blunt or skeptical, values honesty over tact, may struggle with empathy.
                                3 Balanced Agreeableness - Able to cooperate and be kind but also sets personal boundaries when needed.
                                4 Moderate High Agreeableness - Kind, empathetic, enjoys helping others, values relationships.
                                5 Extreme High Agreeableness - Extremely trusting, self-sacrificing, avoids conflict at all costs, highly compassionate.

                        DIMENSION 4: Neuroticism
                            Rating | Description
                                0 Not Rated - Insufficient data to determine neuroticism tendencies.
                                1 Extreme Low Neuroticism - Extremely calm, rarely experiences stress or emotional fluctuations, highly resilient.
                                2 Moderate Low Neuroticism - Generally relaxed, handles stress well, emotionally steady.
                                3 Balanced Neuroticism - Experiences emotions and stress in a manageable way, neither overly anxious nor excessively calm.
                                4 Moderate High Neuroticism - Somewhat prone to worry, sensitive to stress, experiences emotional ups and downs.
                                5 Extreme High Neuroticism - Highly reactive to stress, prone to anxiety and mood swings, frequently overwhelmed by emotions.
                   
                    Clinical Markers Ratings Table (Based on DSM-V)
                        DIMENSION 1: Anxiety
                            Rating | Description
                                0 Not Rated - Insufficient data to determine anxiety tendencies.
                                1 Extreme Low Anxiety - Unusually calm, does not experience fear or worry even in high-stress situations.
                                2 Moderate Low Anxiety - Generally relaxed, mild concern about stressors, but rarely overwhelmed.
                                3 Balanced Anxiety - Experiences normal worry levels, stress is situational and manageable.
                                4 Moderate High Anxiety - Frequently nervous or worried, may struggle with stress regulation.
                                5 Extreme High Anxiety - Constant, overwhelming fear or worry, may interfere with daily life, potential for panic attacks.

                        DIMENSION 2: Depression
                            Rating | Description
                                0 Not Rated - Insufficient data to determine depression tendencies.
                                1 Extreme Low Depression - Persistently upbeat, emotionally resilient, rarely experiences sadness.
                                2 Moderate Low Depression - Generally positive but may experience occasional sadness.
                                3 Balanced Depression - Normal mood fluctuations, experiences sadness and joy in expected situations.
                                4 Moderate High Depression - Frequent low mood, feelings of worthlessness, motivation struggles.
                                5 Extreme High Depression - Severe persistent sadness, hopelessness, loss of interest in activities, possible suicidal ideation.

                        DIMENSION 3: Impulsivity
                            Rating | Description
                                0 Not Rated - Insufficient data to determine impulsivity tendencies.
                                1 Extreme Low Impulsivity - Highly controlled, overthinks decisions, struggles with spontaneity.
                                2 Moderate Low Impulsivity - Thoughtful decision-maker, generally risk-averse.
                                3 Balanced Impulsivity - Can act quickly but also considers consequences.
                                4 Moderate High Impulsivity - Tends to act without thinking, may engage in risk-taking behavior.
                                5 Extreme High Impulsivity - Highly reckless, frequently makes impulsive decisions with severe consequences.

                        DIMENSION 4: Emotional Regulation
                            Rating | Description
                                0 Not Rated - Insufficient data to determine emotional regulation tendencies.
                                1 Extreme Low Emotional Regulation - Very even-tempered, unaffected by stress or emotional triggers.
                                2 Moderate Low Emotional Regulation - Generally stable but may experience minor fluctuations.
                                3 Balanced Emotional Regulation - Has both emotional highs and lows but manages them effectively.
                                4 Moderate High Emotional Dysregulation - Mood swings, difficulty controlling reactions, emotionally reactive.
                                5 Extreme High Emotional Dysregulation - Frequent emotional outbursts, highly sensitive to stress, struggles to regain composure.
                                
                    Dark Triad Ratings Table
                        DIMENSION 1: Psychopathy
                            Rating | Description
                                0 Not Rated - Insufficient data to determine psychopathy tendencies.
                                1 Low Psychopathy - Highly empathetic, strong moral compass.
                                2 Moderate Psychopathy - Can be pragmatic but still feels guilt and empathy.
                                3 High Psychopathy - Emotionally detached, lacks guilt, manipulative.

                        DIMENSION 2: Machiavellianism
                            Rating | Description
                                0 Not Rated - Insufficient data to determine Machiavellianism tendencies.
                                1 Low Machiavellianism - Honest, values transparency, dislikes manipulation.
                                2 Moderate Machiavellianism - Uses persuasion strategically but within ethical limits.
                                3 High Machiavellianism - Highly manipulative, deceives others for personal gain.

                        DIMENSION 3: Narcissism
                            Rating | Description
                                0 Not Rated - Insufficient data to determine narcissism tendencies.
                                1 Low Narcissism - Modest, self-sacrificing, does not seek attention.
                                2 Moderate Narcissism - Confident but does not require admiration.
                                3 High Narcissism - Grandiose self-image, craves attention and validation.

                    Advanced Psychological Markers Rating Table:
                        DIMENSION 1: Digital Dependency
                            Rating | Description
                                0 Not Rated - Insufficient data to determine digital dependency tendencies.
                                1 Low Digital Dependency - Avoids technology, not reliant on digital tools.
                                2 Moderate Digital Dependency - Uses technology regularly but can function offline.
                                3 High Digital Dependency - Highly reliant on digital devices, struggles offline.

                        DIMENSION 2: Cognitive Rigidity
                            Rating | Description
                                0 Not Rated - Insufficient data to determine cognitive rigidity tendencies.
                                1 Low Cognitive Rigidity - Highly adaptable, open to change.
                                2 Moderate Cognitive Rigidity - Prefers routine but can accept new ideas.
                                3 High Cognitive Rigidity - Resistant to change, struggles with conflicting viewpoints.

                        DIMENSION 3: Social Anxiety
                            Rating | Description
                                0 Not Rated - Insufficient data to determine social anxiety tendencies.
                                1 Low Social Anxiety - Confident in social situations, enjoys meeting new people.
                                2 Moderate Social Anxiety - Comfortable in small groups, occasionally nervous.
                                3 High Social Anxiety - Highly distressed in social settings, avoids interactions.

                        DIMENSION 4: Environmental Sensitivity
                            Rating | Description
                                0 Not Rated - Insufficient data to determine environmental sensitivity tendencies.
                                1 Low Environmental Sensitivity - Unaffected by noise, light, or crowds.
                                2 Moderate Environmental Sensitivity - Notices stimuli but tolerates them well.
                                3 High Environmental Sensitivity - Easily overwhelmed by sensory input.

                    Positive Psychology Ratings Table
                        DIMENSION 1: Resilience
                            Rating | Description
                                0 Not Rated - Insufficient data to determine resilience tendencies.
                                1 Low Resilience - Easily discouraged, struggles to recover from setbacks, tends to dwell on failures.
                                2 Moderate Resilience - Can handle difficulties but may need support, learns from setbacks.
                                3 High Resilience - Quickly adapts to challenges, maintains optimism, views setbacks as learning opportunities.

                        DIMENSION 2: Self-Efficacy
                            Rating | Description
                                0 Not Rated - Insufficient data to determine self-efficacy tendencies.
                                1 Low Self-Efficacy - Doubts own abilities, avoids challenges, believes success is due to luck or external factors.
                                2 Moderate Self-Efficacy - Believes in own abilities but occasionally needs reassurance, willing to take on challenges.
                                3 High Self-Efficacy - Confident in abilities, proactively takes on difficult tasks, believes effort leads to success.

                        DIMENSION 3: Coping Skills
                            Rating | Description
                                0 Not Rated - Insufficient data to determine coping skill tendencies.
                                1 Low Coping Skills - Struggles with stress, may use avoidance or negative coping mechanisms (e.g., denial, withdrawal).
                                2 Moderate Coping Skills - Uses some healthy coping strategies but may struggle with prolonged stress.
                                3 High Coping Skills - Uses adaptive coping mechanisms (e.g., problem-solving, emotional regulation), manages stress effectively.

                        DIMENSION 4: Growth Mindset
                            Rating | Description
                                0 Not Rated - Insufficient data to determine growth mindset tendencies.
                                1 Low Growth Mindset - Believes intelligence and abilities are fixed, avoids challenges, fears failure.
                                2 Moderate Growth Mindset - Open to improvement but may hesitate when facing difficulties, sees effort as valuable.
                                3 High Growth Mindset - Views challenges as opportunities for growth, embraces learning, believes effort leads to mastery.

                        DIMENSION 5: Emotional Intelligence
                            Rating | Description
                                0 Not Rated - Insufficient data to determine emotional intelligence.
                                1 Low Emotional Intelligence - Struggles to recognize or regulate emotions, difficulty empathizing with others.
                                2 Moderate Emotional Intelligence - Aware of emotions and can regulate them in most situations, developing empathy skills.
                                3 High Emotional Intelligence - Strong self-awareness, effectively manages emotions, highly empathetic and socially skilled.

                        DIMENSION 6: Optimism
                            Rating | Description
                                0 Not Rated - Insufficient data to determine optimism tendencies.
                                1 Low Optimism - Tends to expect negative outcomes, focuses on problems rather than solutions.
                                2 Moderate Optimism - Has a mix of hopeful and cautious outlooks, can find positives in difficult situations.
                                3 High Optimism - Naturally expects positive outcomes, sees setbacks as temporary and solvable.
                                        Interpersonal Personality Dimensions
                        DIMENSION 1: Attachment Styles
                            Rating | Description
                                0 Not Rated - Insufficient data to determine attachment style.
                                1 Secure Attachment - Comfortable with intimacy, trusts others, balances independence and connection.
                                2 Anxious Attachment - Craves closeness but fears rejection, often worries about relationships.
                                3 Avoidant Attachment - Values independence, emotionally distant, struggles with vulnerability.
                                4 Disorganized Attachment - Inconsistent in relationships, may switch between seeking and avoiding intimacy.

                        DIMENSION 2: Social Interaction Styles
                            Rating | Description
                                0 Not Rated - Insufficient data to determine social interaction style.
                                1 Gregariousness - Thrives in social settings, enjoys meeting new people, energized by interaction.
                                2 Reservedness - Prefers smaller groups, values deeper conversations over surface-level engagement.
                                3 Cooperativeness - Prefers working with others, seeks harmony, avoids conflict.
                                4 Assertiveness - Comfortable expressing opinions, stands up for oneself, takes leadership roles.

                        DIMENSION 3: Theory of Mind & Empathy
                            Rating | Description
                                0 Not Rated - Insufficient data to determine empathy tendencies.
                                1 Cognitive Empathy - Ability to understand others' emotions and perspectives.
                                2 Emotional Empathy - Feeling what others feel, emotionally resonant with others.
                                3 Compassionate Empathy - A mix of cognitive and emotional empathy with an active desire to help.

                        DIMENSION 4: Social Hierarchy
                            Rating | Description
                                0 Not Rated - Insufficient data to determine social hierarchy tendencies.
                                1 High Dominance - Takes charge, enjoys leadership, seeks control in relationships.
                                2 Balanced - Can lead or follow depending on the situation, values collaboration.
                                3 High Submissiveness - Prefers to follow, avoids confrontation, relies on others for decision-making.

                        DIMENSION 5: Dark Interpersonal Traits
                            Rating | Description
                                0 Not Rated - Insufficient data to determine dark interpersonal traits.
                                1 Manipulativeness - Uses persuasion or deception to control others for personal gain.
                                2 Exploitative Behavior - Views relationships as transactional, prioritizes self-interest.
                                3 Deceptiveness - Frequently misrepresents reality or hides true intentions in social settings.

                        DIMENSION 6: Prosocial Traits
                            Rating | Description
                                0 Not Rated - Insufficient data to determine prosocial traits.
                                1 Altruism - Enjoys helping others, acts with kindness without expecting returns.
                                2 Trustworthiness - Reliable, keeps commitments, values honesty in relationships.
                                3 Generosity - Willingly shares resources, time, and energy with others.
                 <Examples>
                    User input:

                        I woke up before my alarm today. 5:45 AM. The streetlights outside were still casting that cold, bluish glow through the blinds. February mornings always have this quietness to them—like the city is wrapped in some kinad of waiting state, just before the day fully boots up. I lay there for a few minutes, debating whether I really wanted to get up and go for a run or just stay warm in bed for a little longer. But I knew if I let myself linger too long, I\\\'d 
                        
                    {
                        "personality": {
                            "Jungian_Model": {
                                "Introversion_Extraversion": {
                                    "rating": "2 - Moderate Introvert",
                                    "rationale": "The writing suggests introspection, solitude, and independent thinking, with a focus on internal experiences rather than external social interactions."
                                },
                                "Sensing_Intuition": {
                                    "rating": "4 - Moderate Intuitive",
                                    "rationale": "The passage includes abstract observations (e.g., 'city in a waiting state') and appreciation of sensory details, indicating a preference for intuition over strict sensory input."
                                },
                                "Thinking_Feeling": {
                                    "rating": "3 - Balanced Thinking/Feeling",
                                    "rationale": "The user weighs practical decision-making (whether to get up) with emotional engagement, showing a balance between logic and emotions."
                                },
                                "Judging_Perceiving": {
                                    "rating": "3 - Balanced Judging/Perceiving",
                                    "rationale": "There is structured thought (considering whether to get up) but also adaptability (open to staying in bed)."
                                }
                            },
                            "Big_Five_Model": {
                                "Openness_to_Experience": {
                                    "rating": "4 - Moderate High Openness",
                                    "rationale": "Descriptive, reflective writing with an interest in abstract and sensory details suggests openness to new experiences and creative thought."
                                },
                                "Conscientiousness": {
                                    "rating": "4 - Moderate High Conscientiousness",
                                    "rationale": "The structured morning routine and internal debate about productivity suggest a disciplined and organized mindset."
                                },
                                "Agreeableness": {
                                    "rating": "3 - Balanced Agreeableness",
                                    "rationale": "There is no strong indication of excessive warmth or skepticism, suggesting a balanced interpersonal stance."
                                },
                                "Neuroticism": {
                                    "rating": "3 - Balanced Neuroticism",
                                    "rationale": "The user reflects on decision-making without displaying high emotional reactivity or distress, suggesting emotional stability."
                                }
                            },
                            "Clinical_Model": {
                                "Anxiety": {
                                    "rating": "2 - Moderate Low Anxiety",
                                    "rationale": "No evidence of overwhelming worry, but slight hesitation in decision-making suggests mild concern."
                                },
                                "Depression": {
                                    "rating": "2 - Moderate Low Depression",
                                    "rationale": "Reflective tone but no indication of pervasive sadness or hopelessness."
                                },
                                "Impulsivity": {
                                    "rating": "2 - Moderate Low Impulsivity",
                                    "rationale": "The user considers their actions before making a decision, indicating control over impulses."
                                },
                                "Emotional_Regulation": {
                                    "rating": "3 - Balanced Emotional Regulation",
                                    "rationale": "The passage maintains emotional stability, with no signs of extreme reactivity or detachment."
                                }
                            },
                            "Dark_Triad_Model": {
                                "Psychopathy": {
                                    "rating": "1 - Low Psychopathy",
                                    "rationale": "The passage contains emotional depth and self-reflection, indicating high empathy."
                                },
                                "Machiavellianism": {
                                    "rating": "1 - Low Machiavellianism",
                                    "rationale": "No evidence of manipulation or strategic deception in the writing."
                                },
                                "Narcissism": {
                                    "rating": "2 - Moderate Narcissism",
                                    "rationale": "The self-focused nature of the passage suggests some level of self-awareness and confidence, but not excessive self-importance."
                                }
                            },
                            "Future_Psychological_Model": {
                                "Digital_Dependency": {
                                    "rating": "2 - Moderate Digital Dependency",
                                    "rationale": "No strong dependence on technology is indicated, but the structured thought process suggests familiarity with digital tools."
                                },
                                "Cognitive_Rigidity": {
                                    "rating": "2 - Moderate Cognitive Rigidity",
                                    "rationale": "The user considers multiple possibilities before deciding, indicating some flexibility but also a preference for structure."
                                },
                                "Social_Anxiety": {
                                    "rating": "2 - Moderate Social Anxiety",
                                    "rationale": "The passage is introspective and does not emphasize social interactions, suggesting a slight preference for solitude."
                                },
                                "Environmental_Sensitivity": {
                                    "rating": "3 - High Environmental Sensitivity",
                                    "rationale": "The detailed focus on lighting, sound, and atmosphere suggests high sensitivity to environmental stimuli."
                                }
                            },
                            "Positive_Psychology_Model": {
                                "Resilience": {
                                    "rating": "3 - High Resilience",
                                    "rationale": "The user reflects on challenges but remains proactive, indicating an adaptive approach to setbacks."
                                },
                                "Self_Efficacy": {
                                    "rating": "3 - High Self-Efficacy",
                                    "rationale": "The user takes initiative in decision-making and follows through on planned actions."
                                },
                                "Coping_Skills": {
                                    "rating": "3 - High Coping Skills",
                                    "rationale": "The passage does not indicate stress avoidance, suggesting an ability to manage emotions effectively."
                                },
                                "Growth_Mindset": {
                                    "rating": "3 - High Growth Mindset",
                                    "rationale": "The introspective nature and willingness to evaluate choices indicate a learning-oriented perspective."
                                },
                                "Emotional_Intelligence": {
                                    "rating": "3 - High Emotional Intelligence",
                                    "rationale": "The user demonstrates self-awareness and an ability to regulate emotions effectively."
                                },
                                "Optimism": {
                                    "rating": "2 - Moderate Optimism",
                                    "rationale": "The passage is neither excessively positive nor negative, suggesting a balanced outlook."
                                }
                            },
                            "Interpersonal_Model": {
                                "Attachment_Style": {
                                    "rating": "1 - Secure Attachment",
                                    "rationale": "The user expresses comfort with solitude but does not indicate fear of closeness or rejection."
                                },
                                "Social_Interaction": {
                                    "rating": "2 - Reservedness",
                                    "rationale": "The passage is introspective rather than socially focused, suggesting a preference for smaller interactions."
                                },
                                "Empathy_Type": {
                                    "rating": "3 - Compassionate Empathy",
                                    "rationale": "The user engages with abstract emotional states, indicating a deep capacity for understanding others' emotions."
                                },
                                "Social_Hierarchy": {
                                    "rating": "2 - Balanced",
                                    "rationale": "No strong dominance or submissiveness traits are indicated."
                                },
                                "Dark_Interpersonal": {
                                    "rating": "1 - Low Manipulativeness",
                                    "rationale": "The passage lacks any attempt to control or influence others."
                                },
                                "Prosocial_Traits": {
                                    "rating": "3 - Generosity",
                                    "rationale": "The user demonstrates a thoughtful and open perspective on experiences."
                                    }
                            }
                        }
                    }

                <\end Examples>       
                    """
                    },

                {"role": "user", "content": f"Extract the personality of the following text: {content}."}
            ],
            max_tokens = 4000,
            temperature = 1
        )
        json_response = json.loads(response.choices[0].message.content)
        story_text = json_response.get('personality', '')
        return story_text
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None 


def write_personality_to_db(entry_id, processed_content):
    """Main function to get content and analyze personality"""

    # Analyze personality from processed content
    personality_analysis = personality_definer(processed_content)
    if not personality_analysis:
        return None

    # Create new personality assessment
    personality = Personality(
        entry_id=entry_id,
        
        # Jungian Model
        jungian_introversion_extraversion_rating=personality_analysis['Jungian_Model']['Introversion_Extraversion']['rating'],
        jungian_introversion_extraversion_rationale=personality_analysis['Jungian_Model']['Introversion_Extraversion']['rationale'],
        jungian_sensing_intuition_rating=personality_analysis['Jungian_Model']['Sensing_Intuition']['rating'],
        jungian_sensing_intuition_rationale=personality_analysis['Jungian_Model']['Sensing_Intuition']['rationale'],
        jungian_thinking_feeling_rating=personality_analysis['Jungian_Model']['Thinking_Feeling']['rating'],
        jungian_thinking_feeling_rationale=personality_analysis['Jungian_Model']['Thinking_Feeling']['rationale'],
        jungian_judging_perceiving_rating=personality_analysis['Jungian_Model']['Judging_Perceiving']['rating'],
        jungian_judging_perceiving_rationale=personality_analysis['Jungian_Model']['Judging_Perceiving']['rationale'],

        # Big Five Model
        big_five_openness_rating=personality_analysis['Big_Five_Model']['Openness_to_Experience']['rating'],
        big_five_openness_rationale=personality_analysis['Big_Five_Model']['Openness_to_Experience']['rationale'],
        big_five_conscientiousness_rating=personality_analysis['Big_Five_Model']['Conscientiousness']['rating'],
        big_five_conscientiousness_rationale=personality_analysis['Big_Five_Model']['Conscientiousness']['rationale'],
        big_five_agreeableness_rating=personality_analysis['Big_Five_Model']['Agreeableness']['rating'],
        big_five_agreeableness_rationale=personality_analysis['Big_Five_Model']['Agreeableness']['rationale'],
        big_five_neuroticism_rating=personality_analysis['Big_Five_Model']['Neuroticism']['rating'],
        big_five_neuroticism_rationale=personality_analysis['Big_Five_Model']['Neuroticism']['rationale'],

        # Clinical Model
        clinical_anxiety_rating=personality_analysis['Clinical_Model']['Anxiety']['rating'],
        clinical_anxiety_rationale=personality_analysis['Clinical_Model']['Anxiety']['rationale'],
        clinical_depression_rating=personality_analysis['Clinical_Model']['Depression']['rating'],
        clinical_depression_rationale=personality_analysis['Clinical_Model']['Depression']['rationale'],
        clinical_impulsivity_rating=personality_analysis['Clinical_Model']['Impulsivity']['rating'],
        clinical_impulsivity_rationale=personality_analysis['Clinical_Model']['Impulsivity']['rationale'],
        clinical_emotional_regulation_rating=personality_analysis['Clinical_Model']['Emotional_Regulation']['rating'],
        clinical_emotional_regulation_rationale=personality_analysis['Clinical_Model']['Emotional_Regulation']['rationale'],

        # Dark Triad Model
        dark_triad_psychopathy_rating=personality_analysis['Dark_Triad_Model']['Psychopathy']['rating'],
        dark_triad_psychopathy_rationale=personality_analysis['Dark_Triad_Model']['Psychopathy']['rationale'],
        dark_triad_machiavellianism_rating=personality_analysis['Dark_Triad_Model']['Machiavellianism']['rating'],
        dark_triad_machiavellianism_rationale=personality_analysis['Dark_Triad_Model']['Machiavellianism']['rationale'],
        dark_triad_narcissism_rating=personality_analysis['Dark_Triad_Model']['Narcissism']['rating'],
        dark_triad_narcissism_rationale=personality_analysis['Dark_Triad_Model']['Narcissism']['rationale'],

        # Future Psychological Model
        advanced_digital_dependency_rating=personality_analysis['Future_Psychological_Model']['Digital_Dependency']['rating'],
        advanced_digital_dependency_rationale=personality_analysis['Future_Psychological_Model']['Digital_Dependency']['rationale'],
        advanced_cognitive_rigidity_rating=personality_analysis['Future_Psychological_Model']['Cognitive_Rigidity']['rating'],
        advanced_cognitive_rigidity_rationale=personality_analysis['Future_Psychological_Model']['Cognitive_Rigidity']['rationale'],
        advanced_social_anxiety_rating=personality_analysis['Future_Psychological_Model']['Social_Anxiety']['rating'],
        advanced_social_anxiety_rationale=personality_analysis['Future_Psychological_Model']['Social_Anxiety']['rationale'],
        advanced_environmental_sensitivity_rating=personality_analysis['Future_Psychological_Model']['Environmental_Sensitivity']['rating'],
        advanced_environmental_sensitivity_rationale=personality_analysis['Future_Psychological_Model']['Environmental_Sensitivity']['rationale'],

        # Positive Psychology Model
        positive_resilience_rating=personality_analysis['Positive_Psychology_Model']['Resilience']['rating'],
        positive_resilience_rationale=personality_analysis['Positive_Psychology_Model']['Resilience']['rationale'],
        positive_self_efficacy_rating=personality_analysis['Positive_Psychology_Model']['Self_Efficacy']['rating'],
        positive_self_efficacy_rationale=personality_analysis['Positive_Psychology_Model']['Self_Efficacy']['rationale'],
        positive_coping_skills_rating=personality_analysis['Positive_Psychology_Model']['Coping_Skills']['rating'],
        positive_coping_skills_rationale=personality_analysis['Positive_Psychology_Model']['Coping_Skills']['rationale'],
        positive_growth_mindset_rating=personality_analysis['Positive_Psychology_Model']['Growth_Mindset']['rating'],
        positive_growth_mindset_rationale=personality_analysis['Positive_Psychology_Model']['Growth_Mindset']['rationale'],
        positive_emotional_intelligence_rating=personality_analysis['Positive_Psychology_Model']['Emotional_Intelligence']['rating'],
        positive_emotional_intelligence_rationale=personality_analysis['Positive_Psychology_Model']['Emotional_Intelligence']['rationale'],
        positive_optimism_rating=personality_analysis['Positive_Psychology_Model']['Optimism']['rating'],
        positive_optimism_rationale=personality_analysis['Positive_Psychology_Model']['Optimism']['rationale'],

        # Interpersonal Model
        interpersonal_attachment_style_rating=personality_analysis['Interpersonal_Model']['Attachment_Style']['rating'],
        interpersonal_attachment_style_rationale=personality_analysis['Interpersonal_Model']['Attachment_Style']['rationale'],
        interpersonal_social_interaction_rating=personality_analysis['Interpersonal_Model']['Social_Interaction']['rating'],
        interpersonal_social_interaction_rationale=personality_analysis['Interpersonal_Model']['Social_Interaction']['rationale'],
        interpersonal_empathy_type_rating=personality_analysis['Interpersonal_Model']['Empathy_Type']['rating'],
        interpersonal_empathy_type_rationale=personality_analysis['Interpersonal_Model']['Empathy_Type']['rationale'],
        interpersonal_social_hierarchy_rating=personality_analysis['Interpersonal_Model']['Social_Hierarchy']['rating'],
        interpersonal_social_hierarchy_rationale=personality_analysis['Interpersonal_Model']['Social_Hierarchy']['rationale'],
        interpersonal_dark_rating=personality_analysis['Interpersonal_Model']['Dark_Interpersonal']['rating'],
        interpersonal_dark_rationale=personality_analysis['Interpersonal_Model']['Dark_Interpersonal']['rationale'],
        interpersonal_prosocial_traits_rating=personality_analysis['Interpersonal_Model']['Prosocial_Traits']['rating'],
        interpersonal_prosocial_traits_rationale=personality_analysis['Interpersonal_Model']['Prosocial_Traits']['rationale']
    )

    # Save to database
    db.session.add(personality)
    db.session.commit()

    return personality.to_dict()

#really, we're also looking forward, right? like how does this person fit into the general fabric? how they relate to others - a personality dimension in for how they relate to others? 
#also we probably dont need all this stuff, it's like a personality profile is only so good for determining a character. But let's see how it goes.
#we want to extract the characteristics, like courage, kindness, etc.