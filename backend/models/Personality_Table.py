from extensions import db
from datetime import datetime

class Personality_Table(db.Model):
    __tablename__ = 'personality_assessments'
    
    # Primary Key Fields\
    # id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, primary_key=True)#db.ForeignKey('pages.id'), nullable=False)
    # user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Jungian Model
    jungian_introversion_extraversion_rating = db.Column(db.String(50))
    jungian_introversion_extraversion_rationale = db.Column(db.Text)
    jungian_sensing_intuition_rating = db.Column(db.String(50))
    jungian_sensing_intuition_rationale = db.Column(db.Text)
    jungian_thinking_feeling_rating = db.Column(db.String(50))
    jungian_thinking_feeling_rationale = db.Column(db.Text)
    jungian_judging_perceiving_rating = db.Column(db.String(50))
    jungian_judging_perceiving_rationale = db.Column(db.Text)

    # Big Five Model
    big_five_openness_rating = db.Column(db.String(50))
    big_five_openness_rationale = db.Column(db.Text)
    big_five_conscientiousness_rating = db.Column(db.String(50))
    big_five_conscientiousness_rationale = db.Column(db.Text)
    big_five_agreeableness_rating = db.Column(db.String(50))
    big_five_agreeableness_rationale = db.Column(db.Text)
    big_five_neuroticism_rating = db.Column(db.String(50))
    big_five_neuroticism_rationale = db.Column(db.Text)

    # Clinical Model
    clinical_anxiety_rating = db.Column(db.String(50))
    clinical_anxiety_rationale = db.Column(db.Text)
    clinical_depression_rating = db.Column(db.String(50))
    clinical_depression_rationale = db.Column(db.Text)
    clinical_impulsivity_rating = db.Column(db.String(50))
    clinical_impulsivity_rationale = db.Column(db.Text)
    clinical_emotional_regulation_rating = db.Column(db.String(50))
    clinical_emotional_regulation_rationale = db.Column(db.Text)

    # Dark Triad Model
    dark_triad_psychopathy_rating = db.Column(db.String(50))
    dark_triad_psychopathy_rationale = db.Column(db.Text)
    dark_triad_machiavellianism_rating = db.Column(db.String(50))
    dark_triad_machiavellianism_rationale = db.Column(db.Text)
    dark_triad_narcissism_rating = db.Column(db.String(50))
    dark_triad_narcissism_rationale = db.Column(db.Text)

    # Future Psychological Model
    advanced_digital_dependency_rating = db.Column(db.String(50))
    advanced_digital_dependency_rationale = db.Column(db.Text)
    advanced_cognitive_rigidity_rating = db.Column(db.String(50))
    advanced_cognitive_rigidity_rationale = db.Column(db.Text)
    advanced_social_anxiety_rating = db.Column(db.String(50))
    advanced_social_anxiety_rationale = db.Column(db.Text)
    advanced_environmental_sensitivity_rating = db.Column(db.String(50))
    advanced_environmental_sensitivity_rationale = db.Column(db.Text)

    # Positive Psychology Model
    positive_resilience_rating = db.Column(db.String(50))
    positive_resilience_rationale = db.Column(db.Text)
    positive_self_efficacy_rating = db.Column(db.String(50))
    positive_self_efficacy_rationale = db.Column(db.Text)
    positive_coping_skills_rating = db.Column(db.String(50))
    positive_coping_skills_rationale = db.Column(db.Text)
    positive_growth_mindset_rating = db.Column(db.String(50))
    positive_growth_mindset_rationale = db.Column(db.Text)
    positive_emotional_intelligence_rating = db.Column(db.String(50))
    positive_emotional_intelligence_rationale = db.Column(db.Text)
    positive_optimism_rating = db.Column(db.String(50))
    positive_optimism_rationale = db.Column(db.Text)

    # Interpersonal Model
    interpersonal_attachment_style_rating = db.Column(db.String(50))
    interpersonal_attachment_style_rationale = db.Column(db.Text)
    interpersonal_social_interaction_rating = db.Column(db.String(50))
    interpersonal_social_interaction_rationale = db.Column(db.Text)
    interpersonal_empathy_type_rating = db.Column(db.String(50))
    interpersonal_empathy_type_rationale = db.Column(db.Text)
    interpersonal_social_hierarchy_rating = db.Column(db.String(50))
    interpersonal_social_hierarchy_rationale = db.Column(db.Text)
    interpersonal_dark_rating = db.Column(db.String(50))
    interpersonal_dark_rationale = db.Column(db.Text)
    interpersonal_prosocial_traits_rating = db.Column(db.String(50))
    interpersonal_prosocial_traits_rationale = db.Column(db.Text)

    def to_dict(self):
        return {
            'entry_id': self.entry_id,
            # 'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'jungian_model': {
                'introversion_extraversion': {
                    'rating': self.jungian_introversion_extraversion_rating,
                    'rationale': self.jungian_introversion_extraversion_rationale
                },
                'sensing_intuition': {
                    'rating': self.jungian_sensing_intuition_rating,
                    'rationale': self.jungian_sensing_intuition_rationale
                },
                'thinking_feeling': {
                    'rating': self.jungian_thinking_feeling_rating,
                    'rationale': self.jungian_thinking_feeling_rationale
                },
                'judging_perceiving': {
                    'rating': self.jungian_judging_perceiving_rating,
                    'rationale': self.jungian_judging_perceiving_rationale
                }
            },
            'big_five_model': {
                'openness': {
                    'rating': self.big_five_openness_rating,
                    'rationale': self.big_five_openness_rationale
                },
                'conscientiousness': {
                    'rating': self.big_five_conscientiousness_rating,
                    'rationale': self.big_five_conscientiousness_rationale
                },
                'agreeableness': {
                    'rating': self.big_five_agreeableness_rating,
                    'rationale': self.big_five_agreeableness_rationale
                },
                'neuroticism': {
                    'rating': self.big_five_neuroticism_rating,
                    'rationale': self.big_five_neuroticism_rationale
                }
            },
            'clinical_model': {
                'anxiety': {
                    'rating': self.clinical_anxiety_rating,
                    'rationale': self.clinical_anxiety_rationale
                },
                'depression': {
                    'rating': self.clinical_depression_rating,
                    'rationale': self.clinical_depression_rationale
                },
                'impulsivity': {
                    'rating': self.clinical_impulsivity_rating,
                    'rationale': self.clinical_impulsivity_rationale
                },
                'emotional_regulation': {
                    'rating': self.clinical_emotional_regulation_rating,
                    'rationale': self.clinical_emotional_regulation_rationale
                }
            },
            'dark_triad_model': {
                'psychopathy': {
                    'rating': self.dark_triad_psychopathy_rating,
                    'rationale': self.dark_triad_psychopathy_rationale
                },
                'machiavellianism': {
                    'rating': self.dark_triad_machiavellianism_rating,
                    'rationale': self.dark_triad_machiavellianism_rationale
                },
                'narcissism': {
                    'rating': self.dark_triad_narcissism_rating,
                    'rationale': self.dark_triad_narcissism_rationale
                }
            },
            'future_psychological_model': {
                'digital_dependency': {
                    'rating': self.advanced_digital_dependency_rating,
                    'rationale': self.advanced_digital_dependency_rationale
                },
                'cognitive_rigidity': {
                    'rating': self.advanced_cognitive_rigidity_rating,
                    'rationale': self.advanced_cognitive_rigidity_rationale
                },
                'social_anxiety': {
                    'rating': self.advanced_social_anxiety_rating,
                    'rationale': self.advanced_social_anxiety_rationale
                },
                'environmental_sensitivity': {
                    'rating': self.advanced_environmental_sensitivity_rating,
                    'rationale': self.advanced_environmental_sensitivity_rationale
                }
            },
            'positive_psychology_model': {
                'resilience': {
                    'rating': self.positive_resilience_rating,
                    'rationale': self.positive_resilience_rationale
                },
                'self_efficacy': {
                    'rating': self.positive_self_efficacy_rating,
                    'rationale': self.positive_self_efficacy_rationale
                },
                'coping_skills': {
                    'rating': self.positive_coping_skills_rating,
                    'rationale': self.positive_coping_skills_rationale
                },
                'growth_mindset': {
                    'rating': self.positive_growth_mindset_rating,
                    'rationale': self.positive_growth_mindset_rationale
                },
                'emotional_intelligence': {
                    'rating': self.positive_emotional_intelligence_rating,
                    'rationale': self.positive_emotional_intelligence_rationale
                },
                'optimism': {
                    'rating': self.positive_optimism_rating,
                    'rationale': self.positive_optimism_rationale
                }
            },
            'interpersonal_model': {
                'attachment_style': {
                    'rating': self.interpersonal_attachment_style_rating,
                    'rationale': self.interpersonal_attachment_style_rationale
                },
                'social_interaction': {
                    'rating': self.interpersonal_social_interaction_rating,
                    'rationale': self.interpersonal_social_interaction_rationale
                },
                'empathy_type': {
                    'rating': self.interpersonal_empathy_type_rating,
                    'rationale': self.interpersonal_empathy_type_rationale
                },
                'social_hierarchy': {
                    'rating': self.interpersonal_social_hierarchy_rating,
                    'rationale': self.interpersonal_social_hierarchy_rationale
                },
                'dark_traits': {
                    'rating': self.interpersonal_dark_rating,
                    'rationale': self.interpersonal_dark_rationale
                },
                'prosocial_traits': {
                    'rating': self.interpersonal_prosocial_traits_rating,
                    'rationale': self.interpersonal_prosocial_traits_rationale
                }
            }
        }
