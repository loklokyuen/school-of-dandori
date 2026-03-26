import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="School of Dandori", page_icon="🌘")
st.title("🌘 School of Dandori — Course Finder")
st.write("Find your next whimsical adventure")

def load_data():
    if not os.path.exists("XXX.csv"):
        return pd.DataFrame()
    return pd.read_csv("XXX.csv")

df = load_data()

def get_courses(search_term="", location="", date=""):
    filtered = df.copy()

    if search_term:
        filtered = filtered[
            filtered["course_name"].str.contains(search_term, case=False, na=False) |
            filtered["description"].str.contains(search_term, case=False, na=False) |
            filtered["category"].str.contains(search_term, case=False, na=False)
        ]

    if location:
        filtered = filtered[
            filtered["location"].str.contains(location, case=False, na=False)
        ]

    if date:
        filtered = filtered[
            filtered["date"].str.contains(date, case=False, na=False)
        ]

    return filtered


st.sidebar.header("Search & Filter")
search_term = st.sidebar.text_input("Keyword search", placeholder="e.g. pottery, yoga, painting")
location = st.sidebar.text_input("Location", placeholder="e.g. Leeds, Bristol")
date = st.sidebar.text_input("Date", placeholder="e.g. Tuesday, March")

courses = get_courses(search_term, location, date)

st.write(f"**{len(courses)} courses found**")
if courses.empty:
    st.info("No courses match your search — try different keywords.")

else:
    for _, row in courses.iterrows():
        with st.expander(f"{row['course_name']} — {row['location']} — £{row['price_gbp']}"):
            st.write(f"**Instructor:** {row['instructor']}")
            st.write(f"**Date:** {row['date']}")
            st.write(f"**Time:** {row['time']}")
            st.write(f"**Category:** {row['category']}")
            st.write(f"**Class ID:** {row['class_id']}")
            if row['description']:
                st.write(f"**About:** {row['description']}")