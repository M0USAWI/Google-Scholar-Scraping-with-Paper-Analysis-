
import streamlit as st
import pandas as pd
import mysql.connector
import subprocess

st.set_page_config(page_title="Scholar Research Dashboard", layout="wide")
st.markdown("""
<style>
.stApp {
    background-color: #1e1e2f;
    color: white;
    font-family: 'Segoe UI', sans-serif;
}
.stButton>button {
    width: 100%;
    border-radius: 8px;
    padding: 10px;
    font-weight: bold;
    background-color: #3c3f58;
    color: white;
    border: 2px solid #888;
}
input {
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("📚 Scholar Research Dashboard")

mode = st.radio("Choose Mode", ["Scraping Mode", "Analysis Mode"], horizontal=True)

if mode == "Scraping Mode":
    university_input = st.text_input("Enter University Name (for 'Any University' options):", "")
    st.subheader("Scraping Controls")

    scrape_mode = st.selectbox("Select scraping type:", ["Profiles Only", "Full (Profiles + Articles)"])
    num_choice = st.radio("Do you want to scrape all or a specific number?", ["Scrape All", "Scrape Specific Number"])

    num_profiles = None
    if num_choice == "Scrape Specific Number":
        num_profiles = st.number_input("Enter number of profiles to scrape:", min_value=1, step=1)

    if st.button("Start Scraping (Lebanese University)"):
        if scrape_mode == "Profiles Only":
            subprocess.run(["python", "scraper1.py", "--query", "Lebanese University", "--mode", "profiles", "--limit", str(num_profiles or 0)])
        elif scrape_mode == "Full (Profiles + Articles)":
            subprocess.run(["python", "scraper1.py", "--query", "Lebanese University", "--mode", "full", "--limit", str(num_profiles or 0)])

    if university_input and st.button("Start Scraping (Any University)"):
        if scrape_mode == "Profiles Only":
            subprocess.run(["python", "scraper1.py", "--query", university_input, "--mode", "profiles", "--limit", str(num_profiles or 0)])
        elif scrape_mode == "Full (Profiles + Articles)":
            subprocess.run(["python", "scraper1.py", "--query", university_input, "--mode", "full", "--limit", str(num_profiles or 0)])

elif mode == "Analysis Mode":
    st.subheader("Analysis Tools")
    if st.button("🔍 Cosine Similarity"):
        subprocess.run(["python", "analyze_papers.py", "--task", "cosine"])

    if st.button("📊 Word Frequency Analysis"):
        subprocess.run(["python", "analyze_papers.py", "--task", "wordfreq"])

    if st.button("🧠 Edit Distance Detection"):
        subprocess.run(["python", "analyze_papers.py", "--task", "editdistance"])

    if st.button("📦 All Analysis Combined"):
        subprocess.run(["python", "analyze_papers.py", "--task", "all"])


st.subheader("📂 View Database Tables")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="hasannet123@",
    database="scholars_data"
)

def fetch_data(query):
    return pd.read_sql(query, conn)

if st.checkbox("Show Researchers Table"):
    sort_option = st.selectbox("Sort Researchers By:", ["RName (A-Z)", "RID", "Total Citations"], key="researcher_sort")
    order_by = {
        "RName (A-Z)": "RName",
        "RID": "RID",
        "Total Citations": "TotalCitations DESC"
    }[sort_option]
    df = fetch_data(f"""
        SELECT r.*, COALESCE(SUM(p.PCitations), 0) AS TotalCitations
        FROM RESEARCHERS r
        LEFT JOIN PAPERS p ON r.RID = p.RID
        GROUP BY r.RID
        ORDER BY {order_by}
    """)
    st.dataframe(df)

if st.checkbox("Show Papers Table"):
    sort_option = st.selectbox("Sort Papers By:", ["PTitle (A-Z)", "PCitations DESC"], key="papers_sort")
    order_by = "PTitle" if sort_option == "PTitle (A-Z)" else "PCitations DESC"
    df = fetch_data(f"SELECT * FROM PAPERS ORDER BY {order_by}")
    st.dataframe(df)

if st.checkbox("Show Citations Table"):
    sort_option = st.selectbox("Sort Citations By:", ["CTitle (A-Z)", "CYear (Newest First)", "CPublisher (A-Z)"], key="citations_sort")
    order_by = (
        "CTitle" if sort_option == "CTitle (A-Z)" else
        "CYear DESC" if sort_option == "CYear (Newest First)" else
        "CPublisher"
    )
    df = fetch_data(f"SELECT * FROM CITATIONS ORDER BY {order_by}")
    st.dataframe(df)

conn.close()