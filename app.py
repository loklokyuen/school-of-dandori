import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="School of Dandori", page_icon="🌘")
st.title("🌘 School of Dandori — Course Finder")
st.write("Find your next whimsical adventure")

def load_data():
    if not os.path.exists("courses.csv"):
        return pd.DataFrame()
    return pd.read_csv("courses.csv")

df = load_data()

# get list of all locations
all_locations = df['location'].dropna().unique()

def get_courses(search_term="", location="", course_type=""):
    filtered = df.copy()

    if search_term:
        filtered = filtered[
            filtered["title"].str.contains(search_term, case=False, na=False) |
            filtered["description"].str.contains(search_term, case=False, na=False) |
            filtered["skills"].str.contains(search_term, case=False, na=False)
        ]

    if location and location != "All locations":
        filtered = filtered[
            filtered["location"].str.contains(location, case=False, na=False)
        ]

    if course_type:
        filtered = filtered[
            filtered["skills"].str.contains(course_type, case=False, na=False)
        ]

    return filtered


st.sidebar.header("Search & Filter")
search_term = st.sidebar.text_input("Keyword search", placeholder="e.g. pottery, yoga, painting")
location = st.sidebar.selectbox("Location", ["All locations"] + sorted(all_locations.tolist()), placeholder="e.g. Oxford")
course_type = st.sidebar.text_input("Course type", placeholder="e.g. Mindfulness, Fiber Arts")

courses = get_courses(search_term, location, course_type)

st.write(f"**{len(courses)} courses found**")
if courses.empty:
    st.info("No courses match your search — try different keywords.")

else:
    for _, row in courses.iterrows():
        with st.expander(f"{row['title']} — {row['location']} — {row['cost']}"):
            st.write(f"**Instructor:** {row['instructor']}")
            st.write(f"**Course Type:** {row['course_type']}")
            st.write(f"**Skills:** {row['skills']}")
            st.write(f"**Class ID:** {row['class_id']}")
            if row['description']:
                st.write(f"**About:** {row['description']}")