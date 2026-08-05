import streamlit as st
from streamlit_option_menu import option_menu
from pymongo import MongoClient

# Initialize MongoDB connection DIRECTLY before importing other modules
if "collection" not in st.session_state:
    try:
        # Get connection string from secrets
        mongo_uri = "mongodb+srv://rohith_palyam:rohith_palyam@cluster0.9q8c1if.mongodb.net/?appName=cluster0"
        # Initialize MongoDB client
        client = MongoClient(mongo_uri)
        st.session_state["client"] = client
        st.session_state["db"] = client["courses_db"]
        st.session_state["collection"] = st.session_state["db"]["course_collection"]
        # Connection successful - no need to show message
    except Exception as e:
        st.error(f"❌ MongoDB connection failed: {str(e)}")
        st.stop()

# Now import other modules AFTER connection is established
from courses import courses_ui_main
from materials import main1
from tasks import main2

def main():
    # Configure the page layout
    st.set_page_config(page_title="Dashboard", layout="wide")

    # Double-check connection before rendering
    if "collection" not in st.session_state:
        st.error("❌ Database connection not found. Please refresh the page.")
        return

    with st.sidebar:
        # Call the imported library function directly
        selected_option = option_menu(
            menu_title="Choose the option",
            options=["Courses", "Materials", "Tasks", "Ad Profile"],
            icons=["book", "pencil", "star", "google"],
            menu_icon="settings",
            default_index=0
        )

    # Render content based on the selected option
    if selected_option == "Courses":
        courses_ui_main()
    elif selected_option == "Materials":
        main1()
    elif selected_option == "Tasks":
        main2()
    elif selected_option == "Ad Profile":
        st.header("👤 Ad Profile")
        st.write("Here you can manage your profile settings.")

if __name__ == "__main__":
    main()
