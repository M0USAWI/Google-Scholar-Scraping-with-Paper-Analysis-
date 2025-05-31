import pandas as pd
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein
import nltk
from nltk.corpus import stopwords
from collections import Counter
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--task", type=str, default="all")
args = parser.parse_args()

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='hasannet123@',
    database='scholars_data'
)
cursor = conn.cursor()

df = pd.read_sql("SELECT PID, PTitle FROM PAPERS", conn)
titles = df['PTitle'].fillna('').tolist()

def cosine_similarity_analysis():
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(titles)
    cos_sim_matrix = cosine_similarity(tfidf_matrix)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS SIMILAR_PAPERS (
            PID1 INT,
            PID2 INT,
            Similarity FLOAT,
            PRIMARY KEY (PID1, PID2),
            FOREIGN KEY (PID1) REFERENCES PAPERS(PID),
            FOREIGN KEY (PID2) REFERENCES PAPERS(PID)
        )
    """)
    conn.commit()

    batch_data = []
    for i, pid1 in enumerate(df['PID']):
        sim_scores = list(enumerate(cos_sim_matrix[i]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        print(f"\n[PID {pid1}] \"{titles[i]}\"")
        for j, score in sim_scores[1:4]:
            pid2 = df['PID'][j]
            print(f"  → Similar to [PID {pid2}] \"{titles[j]}\" | Score: {score:.4f}")
            batch_data.append((int(pid1), int(pid2), float(score)))

    if batch_data:
        cursor.executemany(
            "REPLACE INTO SIMILAR_PAPERS (PID1, PID2, Similarity) VALUES (%s, %s, %s)",
            batch_data
        )
    conn.commit()
    print("\n[✓] Cosine similarity analysis done and printed.")

def word_frequency_analysis():
    def clean_text(text):
        text = text.lower()
        text = re.sub(r'[^a-z\s]', '', text)
        return ' '.join([word for word in text.split() if word not in stop_words])

    all_tokens = []
    for title in titles:
        cleaned = clean_text(title)
        all_tokens.extend(cleaned.split())

    word_freq = Counter(all_tokens).most_common(20)
    print("\nTop 20 Words in Paper Titles:")
    for word, count in word_freq:
        print(f"{word}: {count}")

def edit_distance_detection():
    print("\nPotential Duplicate Titles (Edit Distance > 0.9):")
    for i in range(len(titles)):
        for j in range(i+1, len(titles)):
            ratio = Levenshtein.ratio(titles[i].lower(), titles[j].lower())
            if ratio > 0.9 and titles[i] != titles[j]:
                print(f"- ({df['PID'][i]}, {df['PID'][j]}): {ratio:.2f}")

if args.task == "cosine":
    cosine_similarity_analysis()
elif args.task == "wordfreq":
    word_frequency_analysis()
elif args.task == "editdistance":
    edit_distance_detection()
elif args.task == "all":
    cosine_similarity_analysis()
    word_frequency_analysis()
    edit_distance_detection()

cursor.close()
conn.close()