from pymongo import MongoClient
import streamlit as st

@st.cache_resource
def get_mongo_client():
    """Get MongoDB client with caching for better performance"""
    return MongoClient("mongodb+srv://rohith_palyam:rohith_palyam@cluster0.9q8c1if.mongodb.net/?appName=cluster0")

# Only initialize if not already set
if "collection" not in st.session_state:
    try:
        client = get_mongo_client()
        st.session_state["client"] = client
        st.session_state["db"] = client["courses_db"]
        st.session_state["collection"] = st.session_state["db"]["course_collection"]
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
