from pymongo import MongoClient
import streamlit as st

if "client" not in st.session_state:
    st.session_state["client"]=MongoClient("mongodb+srv://rohith_palyam:rohith_palyam@cluster0.9q8c1if.mongodb.net/?appName=cluster0")
    st.session_state["db"]=st.session_state["client"]["courses_db"]
    st.session_state["collection"]=st.session_state["db"]["course_collection"]
