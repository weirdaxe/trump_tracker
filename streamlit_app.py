import streamlit as st
import pandas as pd
from db import SessionLocal, init_db, Post
from datetime import datetime

# Initialize DB
init_db()

# UI config
st.set_page_config(layout="wide")

# Sidebar: Visualization settings
st.sidebar.header("Visualization Settings")

db_url = st.secrets.get("database", {}).get("url", None)
if db_url:
    os.environ["DATABASE_URL"] = db_url

date_range = st.sidebar.date_input(
    "Date Range", [datetime(2021, 1, 1), datetime.now()]
)
vis_type = st.sidebar.radio("Chart Type", ["Line", "Bar", "Stacked Bar"])
mode = st.sidebar.radio("Mode", ["Single Series", "Comparison"])
agg_mode = st.sidebar.selectbox("Aggregate", ["Raw", "Rolling Mean", "Rolling Sum"])
agg_sub = st.sidebar.selectbox("Sub-Aggregate", ["None", "Period/Period Change"])
period = st.sidebar.slider("Main Period (days)", 1, 180, 30)
period2 = None
if agg_sub == "Period/Period Change":
    period2 = st.sidebar.slider("Comparison Period (days)", 1, 180, period)

if st.sidebar.button("Update Chart"):
    st.session_state.update = True

# Main layout
col1, col2 = st.columns([3, 1])
with col1:
    words = st.multiselect(
        "Words/Phrases to Track", [], help="Enter words or phrases, press Enter after each."
    )
    if st.button("Compute"):
        st.session_state.compute = True
    plot_area = st.empty()

with col2:
    st.subheader("Live Feed (@realDonaldTrump)")
    feed_area = st.empty()
    # Client auto-refresh can be configured in deployment

# Data fetch & plotting
if st.session_state.get('compute'):
    db = SessionLocal()
    posts = (
        db.query(Post.timestamp, Post.processed_tokens)
        .filter(Post.timestamp.between(date_range[0], date_range[1]))
        .all()
    )
    db.close()
    df = pd.DataFrame([
        {'timestamp': ts, 'tokens': tokens}
        for ts, tokens in posts
    ])
    # Expand and count
    records = []
    for row in df.itertuples():
        day = row.timestamp.date()
        for w in words:
            records.append({'date': day, 'word': w, 'count': row.tokens.count(w.lower())})
    df2 = pd.DataFrame(records)
    pivot = df2.pivot(index='date', columns='word', values='count').fillna(0)
    # Aggregations
    if agg_mode == "Rolling Mean":
        pivot = pivot.rolling(window=period).mean()
    elif agg_mode == "Rolling Sum":
        pivot = pivot.rolling(window=period).sum()
    if agg_sub == "Period/Period Change":
        pivot = pivot.pct_change(periods=period2)
    # Plot
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    if vis_type == "Line":
        pivot.plot(ax=ax)
    elif vis_type == "Bar":
        pivot.plot.bar(ax=ax)
    else:
        pivot.plot.bar(ax=ax, stacked=True)
    st.pyplot(fig)

# Live feed display
with col2:
    db = SessionLocal()
    latest_posts = db.query(Post).order_by(Post.timestamp.desc()).limit(5).all()
    db.close()
    for p in latest_posts:
        st.markdown(f"**{p.timestamp.strftime('%Y-%m-%d %H:%M')}**: {p.text}")