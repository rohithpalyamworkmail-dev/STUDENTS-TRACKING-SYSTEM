from pymongo import MongoClient
import streamlit as st

if "client" not in st.session_state:
    st.session_state["client"]=MongoClient(st.secrets["mongoKey"])
    st.session_state["db"]=st.session_state["client"]["courses_db"]
    st.session_state["collection"]=st.session_state["db"]["course_collection"]
