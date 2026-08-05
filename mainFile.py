import streamlit as st
from streamlit_extras.steps import steps as st_steps
from datetime import datetime
from streamlit_option_menu import option_menu
from Courses import main_layout
from Materials import main1 as study_materials
from Assignments import main2 as assignment_materials
from save_progress import main3 as save_progress
from Performance import main4 as performance_dashboard
from pymongo import MongoClient

# Initialize MongoDB connection
if "client" not in st.session_state:
    st.session_state["client"] = MongoClient("mongodb+srv://rohith_palyam:rohith_palyam@cluster0.9q8c1if.mongodb.net/?appName=cluster0")
    st.session_state["db"] = st.session_state["client"]["courses_db"]
    st.session_state["collection"] = st.session_state["db"]["course_collection"]

# Initialize session states
session_states = [
    "unit 1", "unit 2", "unit 3", "unit 4", "unit 5", 
    "materials", "logged_in", "start_time", "year", 
    "department", "subject", "roll_number", "student_name",
    "course_data", "attempting_task", "assignment_answers", 
    "assignment_marks", "submit_assignment", "assignment_start_time",
    "show_assignment", "progress_saved"
]

for i in session_states:
    if i not in st.session_state:
        if i == "logged_in":
            st.session_state[i] = False
        elif i in ["start_time", "assignment_start_time"]:
            st.session_state[i] = None
        elif i == "assignment_answers":
            st.session_state[i] = {}
        elif i in ["attempting_task", "submit_assignment", "show_assignment"]:
            st.session_state[i] = None
        elif i == "progress_saved":
            st.session_state[i] = False
        else:
            st.session_state[i] = None

@st.dialog("Enter Login Details")
def login():
    st.video("https://youtu.be/fGwPmCk64DA?si=55XzWIYApNWJjKQp", muted=True, autoplay=True)
    
    # Step indicator - horizontal=True for horizontal layout
    steps_indicator = st_steps(
        ["Select Academic Year", "Select Department", "Select Subject", "Select Roll Number", "Enter Password"], 
        icons=range(1, 6), 
        horizontal=True,
        key="login_steps"
    )
    
    # Step 0: Select Academic Year
    with steps_indicator[0]:
        st.subheader("📅 Select Academic Year")
        year = st.pills("Select The Academic Year", ["2025-2029", "2024-2028", "2023-2027"])
        st.session_state["year"] = year
        if st.button("Next ➡️", key="login_next_0", use_container_width=True):
            if year:
                steps_indicator.next()
            else:
                st.warning("⚠️ Please select an academic year")

    # Step 1: Select Department
    with steps_indicator[1]:
        st.subheader("🏛️ Select Department")
        department = st.segmented_control("Select The Department", ["AI&DS", "DS", "AI", "CSE"])
        st.session_state["department"] = department
        with st.container(horizontal=True):
            if st.button("⬅️ Back", key="login_back_1", use_container_width=True):
                steps_indicator.previous()
            if st.button("Next ➡️", key="login_next_1", use_container_width=True):
                if department:
                    steps_indicator.next()
                else:
                    st.warning("⚠️ Please select a department")

    # Step 2: Select Subject
    with steps_indicator[2]:
        st.subheader("📚 Select Subject")
        
        if st.session_state["year"] and st.session_state["department"]:
            collection = st.session_state["collection"]
            if collection is not None:
                subjects_cursor = collection.find(
                    {
                        "academicYear": st.session_state["year"], 
                        "department": st.session_state["department"]
                    },
                    {"_id": 0, "courseName": 1}
                )
                subjects = [x["courseName"] for x in subjects_cursor]
                
                if len(subjects) >= 1:
                    subject = st.pills("Select Subject", subjects)
                    st.session_state["subject"] = subject
                else:
                    st.info("ℹ️ No Subjects Are Present. Kindly Go Back And Modify Your Options")
            else:
                st.error("❌ Database connection failed")
        else:
            st.warning("⚠️ Please complete previous steps")
        
        with st.container(horizontal=True):
            if st.button("⬅️ Back", key="login_back_2", use_container_width=True):
                steps_indicator.previous()
            if st.button("Next ➡️", key="login_next_2", use_container_width=True):
                if st.session_state["subject"]:
                    steps_indicator.next()
                else:
                    st.warning("⚠️ Please select a subject")

    # Step 3: Select Roll Number
    with steps_indicator[3]:
        st.subheader("🎯 Select Roll Number")
        
        if st.session_state["year"] and st.session_state["department"] and st.session_state["subject"]:
            collection = st.session_state.get("collection")
            if collection is not None:
                course_data = collection.find_one(
                    {
                        "academicYear": st.session_state["year"],
                        "department": st.session_state["department"],
                        "courseName": st.session_state["subject"]
                    },
                    {"_id": 0, "enrolledStudents.student_roll_number": 1, "enrolledStudents.student_name": 1}
                )
                
                if course_data and "enrolledStudents" in course_data:
                    roll_numbers = [student["student_roll_number"] for student in course_data["enrolledStudents"]]
                    roll_number = st.selectbox("Select Your Roll Number", roll_numbers)
                    st.session_state["roll_number"] = roll_number
                    
                    # Find student name
                    for student in course_data["enrolledStudents"]:
                        if student["student_roll_number"] == roll_number:
                            st.session_state["student_name"] = student["student_name"]
                else:
                    st.info("ℹ️ No students enrolled in this course")
            else:
                st.error("❌ Database connection failed")
        else:
            st.warning("⚠️ Please complete previous steps")
        
        with st.container(horizontal=True):
            if st.button("⬅️ Back", key="login_back_3", use_container_width=True):
                steps_indicator.previous()
            if st.button("Next ➡️", key="login_next_3", use_container_width=True):
                if st.session_state["roll_number"]:
                    steps_indicator.next()
                else:
                    st.warning("⚠️ Please select your roll number")

    # Step 4: Enter Password
    with steps_indicator[4]:
        st.subheader("🔑 Enter Password")
        password = st.text_input("Enter Your Password", type="password")
        with st.container(horizontal=True):
            if st.button("⬅️ Back", key="login_back_4", use_container_width=True):
                steps_indicator.previous()
            if st.button("🔐 Login", key="login_submit", use_container_width=True):
                if password:
                    # Verify password
                    collection = st.session_state.get("collection")
                    if collection is not None:
                        course_data = collection.find_one(
                            {
                                "academicYear": st.session_state["year"],
                                "department": st.session_state["department"],
                                "courseName": st.session_state["subject"],
                                "enrolledStudents.student_roll_number": st.session_state["roll_number"],
                                "enrolledStudents.student_password": password
                            }
                        )
                        if course_data:
                            st.session_state["logged_in"] = True
                            st.session_state["start_time"] = datetime.now().strftime("%H:%M:%S")
                            st.toast("✅ Login Successful!")
                            
                            # Store all course data in session
                            st.session_state["unit 1"] = course_data["unit 1"]
                            st.session_state["unit 2"] = course_data["unit 2"]
                            st.session_state["unit 3"] = course_data["unit 3"]
                            st.session_state["unit 4"] = course_data["unit 4"]
                            st.session_state["unit 5"] = course_data["unit 5"]
                            st.session_state["materials"] = course_data["materials"]
                            st.session_state["course_data"] = course_data
                            
                            # Initialize assignment related states
                            st.session_state["attempting_task"] = None
                            st.session_state["assignment_answers"] = {}
                            st.session_state["assignment_marks"] = 0
                            st.session_state["submit_assignment"] = False
                            st.session_state["assignment_start_time"] = None
                            st.session_state["show_assignment"] = None
                            st.session_state["progress_saved"] = False

                            st.rerun()
                        else:
                            st.error("❌ Invalid password. Please try again.")
                    else:
                        st.error("❌ Database connection failed")
                else:
                    st.warning("⚠️ Please enter your password")

def show_sidebar():
    """Display sidebar with option menu and student info"""
    with st.sidebar:
        # Display student info
        if st.session_state.get("logged_in", False):
            pass
        
        selected = option_menu(
            "Select What You Wanted To Do",
            options=["Learn", "Study", "Assignment", "My Performance", "Save My Progress"],
            icons=["book", "pencil-square", "clipboard-check", "person-circle", "save"],
            menu_icon="star",
            default_index=0
        )
        return selected

def logout():
    """Logout function to clear session state"""
    # Keep only database connection
    keep_keys = ["client", "db", "collection"]
    for key in list(st.session_state.keys()):
        if key not in keep_keys:
            del st.session_state[key]
    st.rerun()

def display_performance_dashboard():
    """Display the performance dashboard with proper integration"""
    try:
        # Import and use the performance module
        performance_dashboard()
    except ImportError:
        st.error("❌ Performance module not found. Please ensure performance.py exists.")
    except Exception as e:
        st.error(f"❌ Error loading performance dashboard: {str(e)}")

# Main app
def main():
    st.set_page_config(
        page_title="Student Learning Platform", 
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .stApp {
            background-color: #f8f9fa;
        }
        .stMetric {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stButton button {
            width: 100%;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.get("logged_in", False):
        login()
    else:
        # Display sidebar and get selected option
        selected = show_sidebar()
        
        # Display content based on selected option
        if selected == "Learn":
            main_layout()
        elif selected == "Study":
            study_materials()
        elif selected == "Assignment":
            assignment_materials()
        elif selected == "My Performance":
            display_performance_dashboard()
        elif selected == "Save My Progress":
            save_progress()

if __name__ == "__main__":
    main()
