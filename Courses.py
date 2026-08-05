import streamlit as st
import pandas as pd

def main_layout():
    st.subheader("You Currently Decided To Learn".upper(),divider="orange",text_alignment="center")
    col1,col2=st.columns([1,2],border=True,gap="small")
    options=col1.radio("Select The Unit To Learn",["Unit 1","Unit 2","Unit 3","Unit 4","Unit 5"],horizontal=True)
    select_topic=col2.selectbox("Select the topic that you wanted to learn",fetchTopics(options))
    fetch_vedio=col2.video(fetchVideo(options,select_topic))
    col2.text(fetchDescription(options,select_topic))

def fetchTopics(unit):
    unit=unit.lower()
    df=pd.DataFrame(st.session_state[unit])
    return [x for x in df["topic_name"].values]

def fetchVideo(unit,topic_name):
    unit=unit.lower()
    df=pd.DataFrame(st.session_state[unit])
    return df[df["topic_name"]==topic_name]["yt_link"].values[0]

def fetchDescription(unit,topic_name):
    unit=unit.lower()
    df=pd.DataFrame(st.session_state[unit])
    return df[df["topic_name"]==topic_name]["description"].values[0]
