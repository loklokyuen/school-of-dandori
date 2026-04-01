import streamlit as st

from components.sidebar import render_sidebar

render_sidebar()
st.set_page_config(page_title="Your Bag", page_icon="🛒")
st.title("🛒 Your Shopping Bag")

if "shopping_bag" not in st.session_state or not st.session_state.shopping_bag:
    st.info("Your bag is empty. Go talk to the Course Advisor to find some classes!")
    if st.button("Go to Advisor"):
        st.switch_page("pages/1_Chatbot.py") 
else:
    sum = 0
    for idx, item in enumerate(st.session_state.shopping_bag):
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(item['title'])
                st.caption(f"Class ID: {item['id']}")
                st.write(f"**Location**: {item['location']} | **Instructor**: {item['instructor']}")

            with col2:
                st.write(f"£{item['cost']} ")

                if st.button("Remove", key=f"remove_{idx}"):
                    st.session_state.shopping_bag.pop(idx)
                    st.rerun()
            skills = item['skills'].strip("[]").replace("'", "").split(", ")
            st.pills("Skills", skills)
            with st.expander("Description"):
                st.write(item['description'])
            with st.expander("More"):
                provided_materials = item['provided_materials'].strip("[]").replace("'", "").split(", ")
                st.pills("Provided Materials", provided_materials)
                learning_objectives = item['learning_objectives'].strip("[]").replace("'", "").split(", ")
                st.pills("Learning Objectives", learning_objectives)
        sum += float(item['cost'])

    st.divider()
    st.success(f"Number of Courses: {len(st.session_state.shopping_bag)} | Total Cost: {sum}")
    
    if st.button("Proceed to Checkout"):
        st.balloons()
        st.write("Redirecting to payment... (Integration coming soon!)")