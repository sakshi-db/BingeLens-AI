import pandas as pd
import zipfile
import os

# Get the folder where app.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))

def load_zipped_csv(filename):
    path = os.path.join(current_dir, filename)
    with zipfile.ZipFile(path) as z:
        # We assume the CSV inside has the same name minus the .zip
        csv_name = filename.replace('.zip', '')
        return pd.read_csv(z.open(csv_name))

try:
    movies = load_zipped_csv('tmdb_5000_movies.csv.zip')
    credits = load_zipped_csv('tmdb_5000_credits.csv.zip')

    print(f"✅ BingeLens Success! Loaded {len(movies)} movies.")
    print(movies[['title', 'genres']].head())

except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure the .zip files are in the same folder as app.py!")

import ast

def convert_genres(obj):
    L = []
    # ast.literal_eval converts the string '[{"id":...}]' into a real list
    for i in ast.literal_eval(obj):
        L.append(i['name']) 
    return L

# Apply the magic to the movies dataframe
movies['genres'] = movies['genres'].apply(convert_genres)

# Let's see the difference!
print("\n--- ✨ Cleaned Data ✨ ---")
print(movies[['title', 'genres']].head())

def extract_names(obj):
    L = []
    try:
        for i in ast.literal_eval(obj):
            L.append(i['name'])
    except:
        pass # In case of empty or weird data
    return L

# Apply to both columns
movies['genres'] = movies['genres'].apply(extract_names)
movies['keywords'] = movies['keywords'].apply(extract_names)

# One more thing: Let's also grab the 'overview' (the summary)
# and turn it into a list of words so the AI can "read" it.
movies['overview'] = movies['overview'].apply(lambda x: x.split() if isinstance(x, str) else [])

print("✅ Keywords and Summaries cleaned!")
print(movies[['title', 'keywords', 'overview']].head())

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Combine everything into a 'tags' column
# We join genres, keywords, and overview into one big string of words
movies['tags'] = movies['genres'] + movies['keywords'] + movies['overview']
movies['tags'] = movies['tags'].apply(lambda x: " ".join(x).lower())

# 2. Create a simpler DataFrame for the model
new_df = movies[['title', 'tags']].copy()

# 3. Vectorization: Converting words to numbers
# 'max_features=5000' means we take the 5000 most frequent words
# 'stop_words=english' removes common words like 'the', 'is', 'and'
cv = CountVectorizer(max_features=5000, stop_words='english')
vectors = cv.fit_transform(new_df['tags']).toarray()

# 4. The Similarity Logic: Measuring the distance between movies
similarity = cosine_similarity(vectors)

print(f"✅ Brain Built! Similarity Matrix shape: {similarity.shape}")
print("Example: Checking the first movie's similarity scores...")
print(similarity[0])

def recommend(movie_title, mood_name=None): # Added mood_name parameter
    try:
        movie_index = new_df[new_df['title'] == movie_title].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        
        # Logic change: Check if we are recommending based on a Mood or a specific Movie
        if mood_name:
            print(f"\n✨ Since you're feeling {mood_name}, BingeLens suggests starting with '{movie_title}'.")
            print("Here are 5 similar vibes for your binge:")
        else:
            print(f"\n🍿 Because you liked '{movie_title}', BingeLens recommends:")
            
        for i in movies_list:
            print(f"-> {new_df.iloc[i[0]].title}")
            
    except IndexError:
        print(f"❌ Sorry, we couldn't find a match for that.")

# --- THE MOOD PICKER (Loop Version) ---
moods = {
    "Energetic": "The Avengers",
    "Adrenaline": "Mad Max: Fury Road",
    "Deep/Thoughtful": "Inception",
    "Cozy/Funny": "Toy Story",
    "Dark/Mystery": "The Silence of the Lambs"
}

print("\n--- ✨ Welcome to BingeLens ✨ ---")

while True: # This keeps the app open
    print("\n-------------------------------------------")
    user_input = input("How are you feeling? (or type a movie, or 'exit' to quit): ").strip()

    if user_input.lower() == 'exit':
        print("👋 Catch you later! Happy binging!")
        break # This stops the loop

    # 1. Check if the input is a MOOD
    if user_input.title() in moods:
        selected_mood = user_input.title()
        print(f"\n✨ Got it! Since you're in an '{selected_mood}' mood, BingeLens suggests starting with '{moods[selected_mood]}'.")
        recommend(moods[selected_mood], mood_name=selected_mood)

    # 2. Check if the input is a MOVIE
    elif user_input.title() in new_df['title'].values:
        print(f"\n🍿 Oh, '{user_input.title()}' is a classic! Check these out:")
        recommend(user_input.title())

    # 3. If we don't recognize it
    else:
        print(f"\n🤔 '{user_input}' is a cool vibe, but I don't have that in my lens yet!")
        print("Try: Energetic, Adrenaline, Deep/Thoughtful, Cozy/Funny, or Dark/Mystery.")