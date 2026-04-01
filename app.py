import os
import pandas as pd
import streamlit as st
from components.sidebar import render_sidebar

render_sidebar()

st.set_page_config(page_title="School of Dandori", page_icon="🌘")
st.title("🌘 School of Dandori — Course Finder")
st.write("Find your next whimsical adventure")

# def load_data():
#     if not os.path.exists("courses.csv"):
#         return pd.DataFrame()
#     return pd.read_csv("courses.csv")

# df = load_data()

if "df" not in st.session_state:
    st.session_state.df = pd.read_csv("./data/courses.csv")

df = st.session_state.df 

if "shopping_bag" not in st.session_state:
    st.session_state.shopping_bag = []

def add_to_bag(course_data):
    # Check if already added
    if course_data["class_id"] not in [item['id'] for item in st.session_state.shopping_bag]:
        st.session_state.shopping_bag.append(dict(course_data))
        st.toast(f"✅ Added {course_data["title"]} to your bag!")
    else:
        st.toast("💡 That course is already in your bag.")


# get list of all locations
all_locations = df['location'].dropna().unique()

def get_courses(selected_min, selected_max, search_term="", location="", course_type=""):
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
            filtered["course_type"].str.contains(course_type, case=False, na=False)
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
location = st.sidebar.selectbox("Location", ["All locations"] + sorted(all_locations.tolist()), placeholder="e.g. Oxford")
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
        with st.expander(f"{row['title']} — {row['location']} — £{row['cost']}"):
            st.write(f"**Instructor:** {row['instructor']}")
            st.write(f"**Course Type:** {row['course_type']}")
            skills = row['skills'].strip("[]").replace("'", "").split(", ")
            st.pills("Skills", skills, key=f"skills_{row['class_id']}_{row['title']}")
            # st.write(f"**Skills:** {skills}")
            st.write(f"**Class ID:** {row['class_id']}")
            if row['description']:
                st.write(f"**About:** {row['description']}")
            if st.button("🛒 Add", key=f"btn_{row['class_id']}_{row['title']}"):
                add_to_bag(row)
            