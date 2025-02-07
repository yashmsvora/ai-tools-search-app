from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import pandas as pd
from utils import get_ai_tool_recommendation
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import process

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Load NLP model
model = SentenceTransformer("all-MiniLM-L6-v2")  

# Updated Persona Categories with Overlapping Assignments
PERSONA_CATEGORIES = {
    "Designer": ["3D Generator", "Art", "Avatar Generator", "Cartoon Generators", "Design Generators", 
                 "Fashion Assistant", "Image", "Image Editing", "Image Generators", "Logo Generator", "UX/UI Tools"],
    "Developer & Data Expert": ["Code", "Code Assistant", "Automations", "No Code", "SQL Assistant", 
                                "SQL Query", "Database", "Programming", "Software Development", 
                                "Python", "Machine Learning", "AI Development", "Data Science"],
    "Content Marketer": ["Marketing", "Copywriting Assistant", "Prompt Generators", "Paraphrasing", 
                         "SEO Tools", "Social Media", "Branding", "Storyteller"],
    "Creative Writer": ["Storyteller", "Copywriting Assistant", "Research Assistant", "Students", 
                        "Paraphrasing", "Fiction Writing", "Screenwriting"],
    "Business & Productivity": ["Business", "Finance", "Project Management", "Productivity", 
                                "Spreadsheet Assistant", "Operations", "Data Analytics"],
    "Media Creator (Video & Audio)": ["Audio Editing", "Audio Generators", "Music Generator", 
                                      "Text To Speech", "Text To Video", "Video", "Video Editing", 
                                      "Video Enhancer", "Video Generators", "Podcasting Tools"],
    "Students & Educators": ["Students", "Transcriber", "Translators", "Research Assistant", 
                             "E-Learning", "Academic Writing", "Note-Taking"],
    "Lifestyle & Personal": ["Gift Ideas", "Fitness", "Religion", "Personal Assistant", 
                             "Hobbies & Interests", "Self-Improvement"]
}

# Persona Descriptions for NLP-Based Detection
PERSONA_DESCRIPTIONS = {
    "Designer": "AI tools for digital art, 3D modeling, UX/UI design, and branding.",
    "Developer & Data Expert": "AI tools for coding, automation, AI development, and data science.",
    "Content Marketer": "AI tools for digital marketing, SEO, branding, and copywriting.",
    "Creative Writer": "AI tools for storytelling, fiction writing, and research assistance.",
    "Business & Productivity": "AI tools for finance, project management, and efficiency.",
    "Media Creator (Video & Audio)": "AI tools for video editing, music production, and audio processing.",
    "Students & Educators": "AI tools for research, e-learning, academic writing, and note-taking.",
    "Lifestyle & Personal": "AI tools for fitness, personal assistance, hobbies, and self-improvement."
}

# Reverse mapping: Assign each category to multiple personas
CATEGORY_TO_PERSONA = defaultdict(list)
for persona, categories in PERSONA_CATEGORIES.items():
    for category in categories:
        CATEGORY_TO_PERSONA[category].append(persona)

# Weighting System (Query-Based = 70%, Click-Based = 30%)
QUERY_WEIGHT = 0.7  
CLICK_WEIGHT = 0.3  

# User Data Tracking
user_data = defaultdict(lambda: {"persona_scores": defaultdict(float), "search_history": [], "clicks_per_category": {}})

def get_user_data(user_id):
    return user_data[user_id]

@app.route('/api/filters', methods=['GET'])
def get_filters():
    try:
        df = pd.read_csv("all_ai_tools.csv")
        categories = df["Category"].dropna().unique().tolist()
        pricing = df["Pricing"].dropna().unique().tolist()
        filters = {
            "categories": categories if categories else ["Unknown"],
            "pricing": pricing if pricing else ["Unknown"]
        }
        return jsonify(filters)
    except Exception as e:
        print(f"Error reading filters: {e}")
        return jsonify({"error": "Could not load filters"}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get('query', '')
    categories = data.get("categories", [])
    pricing = data.get("pricing", [])
    user_id = data.get("user_id", "guest")

    try:
        update_user_persona(user_id, query=query)

        updated_persona = get_dominant_persona(user_id)

        response = json.loads(get_ai_tool_recommendation(query, categories, pricing, updated_persona))
        print(response)
        return jsonify({
            "ai_tool_recommendation": response,
            "updated_persona": updated_persona
        })
    except Exception as e:
        print(f"Error generating AI recommendation: {e}")
        return jsonify({'error': 'Error generating AI recommendation'}), 500

@app.route('/api/persona', methods=['GET'])
def get_persona():
    user_id = request.args.get("user_id", "guest")
    return jsonify({"persona": get_dominant_persona(user_id)})

@app.route('/api/click', methods=['POST'])
def click():
    data = request.get_json()
    user_id = data.get("user_id", "guest")
    tool_name = data.get("tool_name", "")
    category_name = data.get("category_name", "")

    if tool_name:
        user_click_tool(user_id, tool_name)
    elif category_name:
        update_user_persona(user_id, category=category_name)

    return jsonify({"message": "Click recorded", "updated_persona": get_dominant_persona(user_id)})

def user_click_tool(user_id, tool_name):
    """Updates persona based on clicks."""
    user = get_user_data(user_id)
    df = pd.read_csv("all_ai_tools.csv")
    tool_data = df[df["Tool Name"] == tool_name]

    if not tool_data.empty:
        category = tool_data.iloc[0].get("Category", None)
        if category:
            update_user_persona(user_id, category=category)

def detect_persona_hybrid(query, threshold=0.6):
    """Hybrid approach combining NLP embeddings & fuzzy matching."""
    
    # Fuzzy Keyword Matching
    best_keyword_match, keyword_score = None, 0
    for category, personas in CATEGORY_TO_PERSONA.items():
        match, score = process.extractOne(query, [category]) or (None, 0)
        if score > keyword_score:
            best_keyword_match, keyword_score = personas[0], score  # Pick first persona match

    if keyword_score > 80:
        return best_keyword_match

    # Sentence Embeddings for Semantic Similarity
    persona_embeddings = {p: model.encode(desc) for p, desc in PERSONA_DESCRIPTIONS.items()}
    query_embedding = model.encode(query).reshape(1, -1)

    similarities = {p: cosine_similarity(query_embedding, persona_embeddings[p].reshape(1, -1))[0][0] for p in persona_embeddings}
    best_embedding_match = max(similarities, key=similarities.get)
    best_embedding_score = similarities[best_embedding_match]

    if best_embedding_score >= threshold:
        return best_embedding_match

    return best_keyword_match if keyword_score > 60 else "General User"

def update_user_persona(user_id, category=None, query=None):
    """Update user persona dynamically based on weighted scores."""
    user = get_user_data(user_id)

    if query:
        detected_persona = detect_persona_hybrid(query)
        if detected_persona:
            user["persona_scores"][detected_persona] += QUERY_WEIGHT

    if category:
        for persona in CATEGORY_TO_PERSONA.get(category, []):
            user["persona_scores"][persona] += CLICK_WEIGHT

def get_dominant_persona(user_id):
    """Determines the dominant persona based on weighted scores."""
    user = get_user_data(user_id)
    return max(user["persona_scores"], key=user["persona_scores"].get, default="General User")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)
