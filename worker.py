import os, time, random
# Corrected TruthBrush import (module paths may vary by version)
# try:
#     from truthbrush import TruthBrush
# except ImportError:
#     from truthbrush.brush import TruthBrush
from truthbrush.api import Api
# import truthbrush.cli as tb
from db import SessionLocal, init_db, Post, Comment
import spacy
from textblob import TextBlob
from tqdm import tqdm

# Initialize SpaCy once
nlp = spacy.load("en_core_web_lg")

# Initialize database and show location
init_db()

# Load Truth Social credentials from environment (set via secrets.toml in deployment)
USERNAME = os.getenv("TRUTHBRUSH_USERNAME")
PASSWORD = os.getenv("TRUTHBRUSH_PASSWORD")

brusher = Api(username=USERNAME, password=PASSWORD)

def process_text(text: str):
    doc = nlp(text)
    tokens = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct]
    embedding = doc.vector.tolist()
    sentiment = TextBlob(text).sentiment.polarity
    return tokens, embedding, sentiment


def scrape_and_store():
    db = SessionLocal()
    for truth in brusher.pull_statuses("@realDonaldTrump",True,True):#, full_history=True):
        if not db.query(Post).filter(Post.id == truth.id).first():
            tokens, emb, sent = process_text(truth.text)
            p = Post(
                id=truth.id,
                author=truth.author,
                timestamp=truth.created_at,
                text=truth.text,
                processed_tokens=tokens,
                embedding=emb,
                sentiment=sent,
            )
            db.add(p)
            db.commit()
        for cm in brusher.pull_comments(truth.id, include_all=True):#get_comments(truth.id):
            if not db.query(Comment).filter(Comment.id == cm.id).first():
                tokens, emb, sent = process_text(cm.text)
                c = Comment(
                    id=cm.id,
                    post_id=truth.id,
                    timestamp=cm.created_at,
                    text=cm.text,
                    processed_tokens=tokens,
                    embedding=emb,
                    sentiment=sent,
                )
                db.add(c)
        db.commit()
    db.close()

if __name__ == '__main__':
    # Continuous polling every 90±5 seconds with progress bars
    # while True:
    start_time = time.time()
    try:
        scrape_and_store()
    except Exception as e:
        print("Error during scrape:", e)
    duration = time.time() - start_time
    print(f"Scrape completed in {duration:.1f}s")
    # Calculate delay
    delay = 90 + random.uniform(-5, 5)
    # Countdown progress bar until next scrape
    for _ in tqdm(range(int(delay)), desc="Next scrape in", unit="s"):
        time.sleep(1)