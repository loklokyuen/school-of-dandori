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

def get_courses(selected_min, selected_max, search_term="", location="", course_type=""):
    filtered = df.copy()

    if search_term:
        filtered = filtered[
            filtered["title"].str.contains(search_term, case=False, na=False) |
            filtered["description"].str.contains(search_term, case=False, na=False) |
            filtered["skills"].str.contains(search_term, case=False, na=False)
        ]

    if location:
        filtered = filtered[
            filtered["location"].str.contains(location, case=False, na=False)
        ]

    if course_type:
        filtered = filtered[
            filtered["skills"].str.contains(course_type, case=False, na=False)
        ]
    
    filtered = filtered[(filtered["cost"] >= selected_min) & (filtered["cost"] <= selected_max)]

    return filtered

def get_min_max_cost(courses):
    cost = {}
    cost[min] = min(courses["cost"])
    cost[max] = max(courses["cost"])
    return cost


st.sidebar.header("Search & Filter")
search_term = st.sidebar.text_input("Keyword search", placeholder="e.g. pottery, yoga, painting")
location = st.sidebar.text_input("Location", placeholder="e.g. Leeds, Bristol, Bath")
course_type = st.sidebar.text_input("Course type", placeholder="e.g. Mindfulness, Fiber Arts")
cost = get_min_max_cost(df)
min_cost = cost[min]
max_cost = cost[max]

slider = st.sidebar.slider("Price Range £", min_value=int(min_cost), max_value=int(max_cost),
                   value=(int(min_cost), int(max_cost)), step=1)
    
selected_min = slider[0]
selected_max = slider[1]
courses = get_courses(selected_min, selected_max, search_term, location, course_type)

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