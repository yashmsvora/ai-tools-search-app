import openai
import secret  # Securely import API key
import faiss
import numpy as np
import pandas as pd
import json
from sentence_transformers import SentenceTransformer

# Initialize OpenAI client
client = openai.OpenAI(api_key=secret.OPENAI_API_KEY)

# Load AI tools dataset
df = pd.read_csv("all_ai_tools.csv")  # Ensure file name is correct

# Load pre-trained embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Get embedding dimension
embedding_dim = model.get_sentence_embedding_dimension()

# ---
# Build document embeddings for the RAG architecture.
# Here we embed a concatenation of "Tool Name" and "Summary" to provide richer context.
# ---
if "Embedding" not in df.columns:
    df["Embedding"] = df.apply(
        lambda row: model.encode(f"{row['Tool Name']}. {row['Summary']}").astype(np.float32),
        axis=1
    )

# Build a global embedding matrix (this is useful if you want to create a full index).
embedding_matrix = np.vstack(df["Embedding"].values)

# Create a global FAISS index (if needed).
index = faiss.IndexFlatL2(embedding_dim)
index.add(embedding_matrix)

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

def search_ai_tools(query: str, categories: list, pricing: list, persona: str, top_k: int = 3, distance_threshold: float = 1.5) -> pd.DataFrame:
    """
    Searches for AI tools based on a query and filters, and ranks them based on user persona.

    :param query: The user's search query.
    :param categories: List of selected categories.
    :param pricing: List of selected pricing options.
    :param persona: User's detected persona.
    :param top_k: Number of top results to retrieve.
    :param distance_threshold: The maximum acceptable distance for a valid match.
    :return: DataFrame of relevant AI tools.
    """
    filtered_df = df.copy()

    # Apply category & pricing filters
    if categories:
        filtered_df = filtered_df[filtered_df["Category"].isin(categories)]
    if pricing:
        filtered_df = filtered_df[filtered_df["Pricing"].isin(pricing)]

    if filtered_df.empty:
        return pd.DataFrame()

    # Prepare FAISS search
    candidate_indices = filtered_df.index.to_numpy()
    candidate_embeddings = np.vstack(filtered_df["Embedding"].values)
    temp_index = faiss.IndexFlatL2(embedding_dim)
    temp_index.add(candidate_embeddings)

    # Encode query & search
    query_embedding = model.encode([query]).astype(np.float32)
    distances, local_indices = temp_index.search(query_embedding, top_k)
    print("Top distances:", distances)
    # Extract top matches with distance filtering
    top_candidate_indices = [
        candidate_indices[idx] for i, idx in enumerate(local_indices[0]) if distances[0][i] <= distance_threshold
    ]
    print(top_candidate_indices)

    if not top_candidate_indices:
        return pd.DataFrame()  # No strong matches
    
    results = df.iloc[top_candidate_indices].copy()
    results["distance"] = distances[0][: len(top_candidate_indices)]
    # Prioritize persona match
    if persona:
        results["persona_match"] = results["Category"].apply(lambda cat: 1 if cat in PERSONA_CATEGORIES.get(persona, []) else 0)
        results = results.sort_values(by=["persona_match", "distance"], ascending=[False, True])
    print(results)

    return results


def generate_ai_recommendation(query: str, results: pd.DataFrame, categories: list, pricing: list, persona: str) -> dict:
    """
    Generates a structured AI tool recommendation in JSON format.

    :param query: The user's query.
    :param results: DataFrame of search results.
    :param categories: List of selected categories.
    :param pricing: List of selected pricing options.
    :param persona: User's persona.
    :return: JSON-formatted AI recommendation.
    """
    tool_info = [
        {
            "name": row["Tool Name"],
            "summary": row["Summary"],
            "pricing": row["Pricing"]
        }
        for _, row in results.iterrows()
    ]

    prompt = f"""
    A user is searching for an AI tool. Their query: "{query}"

    Filters applied:
    - Categories: {', '.join(categories) if categories else 'None'}
    - Pricing: {', '.join(pricing) if pricing else 'None'}

    Find and rank the most relevant AI tools based on the query and filters. 

    Rules:
    - "summary" should focus only on the query and filters.
    - "best_tool" should highlight the most relevant tool.
    - "tools" should include only relevant tools, **excluding** the "best_tool" to avoid redundancy.
    - Return **only relevant tools** (no fabrications). If none, return an empty list.
    - Use persona history **only as a tie-breaker**.
    - Output **must** be valid JSON with no extra text.

    Return only this JSON format:
    ```json
    {{
    "summary": "A concise summary of the best option and findings.",
    "best_tool": {{
        "name": "Tool Name",
        "reason": "Why this tool is the best choice."
    }} if tool_info else null,
    "tools": {json.dumps(tool_info, indent=2)} if tool_info else []
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI expert helping users find the best AI tools."},
            {"role": "user", "content": prompt}
        ]
    )
    
    print("Raw response:", response.choices[0].message.content)

    # Return the LLM's JSON-formatted response.
    return response.choices[0].message.content

def get_ai_tool_recommendation(query: str, categories: list, pricing: list, persona: str, top_k: int = 3) -> str:
    """
    Wrapper function that integrates the complex RAG pipeline:
      1. Filters the dataset by the user-selected metadata.
      2. Performs a vector search on the filtered results.
      3. Generates an AI tool recommendation via an LLM.
      
    :param query: The user's search query.
    :param categories: List of selected categories.
    :param pricing: List of selected pricing options.
    :param persona: The detected user persona to personalize ranking.
    :param top_k: Number of top results to retrieve.
    :return: AI-generated recommendation in JSON format.
    """
    results = search_ai_tools(query, categories, pricing, persona, top_k)
    return generate_ai_recommendation(query, results, categories, pricing, persona)



