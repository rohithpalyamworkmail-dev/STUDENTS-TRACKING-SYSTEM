import streamlit as st
from datetime import datetime
import pandas as pd
from mongodb1 import *

def main_layout():
    """
    Main layout for the Save Progress section
    Allows students to view their session info and save progress
    """
    st.subheader("💾 Save My Progress", divider="orange", text_alignment="center")
    
    # Check if user is logged in and has necessary session data
    if "roll_number" not in st.session_state or not st.session_state["roll_number"]:
        st.warning("⚠️ Please log in to view this page")
        return
    
    # Create two columns for better layout
    col1, col2 = st.columns([1, 1], gap="medium")
    
    # Column 1: Student Information
    with col1:
        st.subheader("👤 Student Information", divider="blue")
        
        # Display student details in a nice container
        with st.container(border=True):
            st.write(f"**📛 Name:** {st.session_state.get('student_name', 'N/A')}")
            st.write(f"**🎯 Roll Number:** {st.session_state.get('roll_number', 'N/A')}")
            st.write(f"**📚 Course:** {st.session_state.get('subject', 'N/A')}")
            st.write(f"**🏛️ Department:** {st.session_state.get('department', 'N/A')}")
            st.write(f"**📅 Batch:** {st.session_state.get('year', 'N/A')}")
    
    # Column 2: Session Information
    with col2:
        st.subheader("⏰ Session Information", divider="blue")
        
        # Display session details in a nice container
        with st.container(border=True):
            # Get login time
            login_time = st.session_state.get("start_time")
            if login_time:
                st.write(f"**🕐 Current Session Started At:** {login_time}")
            else:
                st.write("**🕐 Current Session Started At:** Not available")
            
            # Get current time
            current_time = datetime.now().strftime("%H:%M:%S")
            st.write(f"**🕒 Current Time:** {current_time}")
            
            # Calculate session duration
            if login_time:
                try:
                    # Use proper time parsing
                    login_dt = datetime.strptime(login_time, "%H:%M:%S")
                    current_dt = datetime.strptime(current_time, "%H:%M:%S")
                    
                    # Calculate difference in seconds
                    diff_seconds = (current_dt - login_dt).total_seconds()
                    
                    # Handle case where logout time is less than login time (crosses midnight)
                    if diff_seconds < 0:
                        diff_seconds += 86400  # Add 24 hours in seconds
                    
                    # Convert to hours, minutes, seconds
                    hours = int(diff_seconds // 3600)
                    minutes = int((diff_seconds % 3600) // 60)
                    seconds = int(diff_seconds % 60)
                    
                    if hours > 0:
                        time_spent = f"{hours}h {minutes}m {seconds}s"
                    elif minutes > 0:
                        time_spent = f"{minutes}m {seconds}s"
                    else:
                        time_spent = f"{seconds}s"
                    
                    st.write(f"**⏱️ Current Session Duration:** {time_spent}")
                except Exception as e:
                    st.write(f"**⏱️ Current Session Duration:** Could not calculate")
            else:
                st.write("**⏱️ Current Session Duration:** Not available")
    
    # Divider
    st.divider()
    
    # Save Progress Button
    st.subheader("💾 Save Your Progress", divider="green")
    
    # Display current date
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_day = datetime.now().strftime("%A")
    
    st.info(f"📌 Today is **{today_day}**, **{today_date}**")
    st.write("Click the button below to save your current session progress.")
    
    # Save progress button
    if st.button("💾 Save Current Session", type="primary", use_container_width=True):
        save_progress()
    
    # Display progress history
    st.divider()
    show_progress_history()

def show_progress_history():
    """
    Display the student's progress history with accurate time calculations
    """
    try:
        collection = st.session_state.get("collection")
        if collection is None:
            st.error("❌ Database connection failed")
            return
        
        student_roll = st.session_state.get("roll_number")
        
        # Query the database
        course_data = collection.find_one({
            "academicYear": st.session_state.get("year"),
            "department": st.session_state.get("department"),
            "courseName": st.session_state.get("subject"),
            "enrolledStudents.student_roll_number": student_roll
        })
        
        if not course_data:
            st.info("ℹ️ No course data found")
            return
        
        # Find the student
        student_found = None
        for student in course_data.get("enrolledStudents", []):
            if student.get("student_roll_number") == student_roll:
                student_found = student
                break
        
        if not student_found:
            st.info("ℹ️ Student not found")
            return
        
        # Check if track field exists
        if "track" not in student_found or not student_found["track"]:
            st.info("ℹ️ No progress data available yet. Start by saving your first session!")
            return
        
        # Display progress data
        st.subheader("📊 Your Progress History", divider="blue")
        
        # Process track data for display
        track_data = []
        total_study_time_seconds = 0
        
        for entry in student_found["track"]:
            date = entry.get("date", "N/A")
            study_sessions = entry.get("study_time", [])
            
            # Calculate total study time for this date in seconds
            total_seconds_for_date = 0
            session_details = []
            valid_sessions = 0
            
            for session in study_sessions:
                session_details.append(session)
                # Parse session times to calculate duration
                try:
                    # Split the session string by " - " to get start and end times
                    if " - " in session:
                        parts = session.split(" - ")
                        if len(parts) == 2:
                            login_time = parts[0].strip()
                            logout_time = parts[1].strip()
                            
                            # Parse times in HH:MM:SS format
                            login_dt = datetime.strptime(login_time, "%H:%M:%S")
                            logout_dt = datetime.strptime(logout_time, "%H:%M:%S")
                            
                            # Calculate difference in seconds
                            diff_seconds = (logout_dt - login_dt).total_seconds()
                            
                            # Handle case where logout time is less than login time (crosses midnight)
                            if diff_seconds < 0:
                                diff_seconds += 86400  # Add 24 hours in seconds
                            
                            # Only add if duration is positive and reasonable (less than 24 hours)
                            if diff_seconds > 0 and diff_seconds < 86400:
                                total_seconds_for_date += diff_seconds
                                valid_sessions += 1
                except Exception as e:
                    # Skip invalid session strings
                    continue
            
            total_study_time_seconds += total_seconds_for_date
            
            # Format study time for this date
            if total_seconds_for_date > 0:
                hours = int(total_seconds_for_date // 3600)
                minutes = int((total_seconds_for_date % 3600) // 60)
                seconds = int(total_seconds_for_date % 60)
                
                if hours > 0:
                    total_time_str = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    total_time_str = f"{minutes}m {seconds}s"
                else:
                    total_time_str = f"{seconds}s"
            else:
                total_time_str = "0s"
            
            # Count number of sessions
            session_count = len(study_sessions)
            
            # Format sessions for display (show first 3, then +more)
            if session_count > 3:
                display_sessions = study_sessions[:3] + [f"... and {session_count - 3} more"]
            else:
                display_sessions = study_sessions
            
            sessions_display = "\n".join(display_sessions) if display_sessions else "No sessions"
            
            track_data.append({
                "Date": date,
                "Sessions": session_count,
                "Valid Sessions": valid_sessions,
                "Total Study Time": total_time_str,
                "Session Details": sessions_display
            })
        
        if track_data:
            # Display as dataframe
            df = pd.DataFrame(track_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Summary statistics
            st.divider()
            st.subheader("📈 Summary Statistics", divider="blue")
            
            col1, col2, col3, col4 = st.columns(4)
            total_days = len(track_data)
            total_sessions = sum(row["Sessions"] for row in track_data)
            total_valid_sessions = sum(row["Valid Sessions"] for row in track_data)
            
            # Calculate average study time in seconds
            if total_days > 0:
                avg_seconds = total_study_time_seconds / total_days
                avg_hours = int(avg_seconds // 3600)
                avg_mins = int((avg_seconds % 3600) // 60)
                avg_secs = int(avg_seconds % 60)
                
                if avg_hours > 0:
                    avg_time_str = f"{avg_hours}h {avg_mins}m {avg_secs}s"
                elif avg_mins > 0:
                    avg_time_str = f"{avg_mins}m {avg_secs}s"
                else:
                    avg_time_str = f"{avg_secs}s"
            else:
                avg_time_str = "0s"
            
            # Format total study time
            total_hours = int(total_study_time_seconds // 3600)
            total_mins = int((total_study_time_seconds % 3600) // 60)
            total_secs = int(total_study_time_seconds % 60)
            
            if total_hours > 0:
                total_time_str = f"{total_hours}h {total_mins}m {total_secs}s"
            elif total_mins > 0:
                total_time_str = f"{total_mins}m {total_secs}s"
            else:
                total_time_str = f"{total_secs}s"
            
            col1.metric("📅 Total Days", total_days)
            col2.metric("🔄 Total Sessions", total_sessions)
            col3.metric("⏱️ Total Study Time", total_time_str)
            col4.metric("📊 Avg/Day", avg_time_str)
            
            # Additional stats
            st.write(f"**✅ Valid Sessions:** {total_valid_sessions} out of {total_sessions} total sessions")
        else:
            st.info("ℹ️ No progress data available")
            
    except Exception as e:
        st.error(f"❌ Error loading progress: {str(e)}")

def save_progress():
    """
    Save the student's current session to the database and logout
    """
    try:
        collection = st.session_state.get("collection")
        if collection is None:
            st.error("❌ Database connection failed")
            return
        
        # Get current time and date
        current_time = datetime.now()
        current_date = current_time.strftime("%Y-%m-%d")
        current_time_str = current_time.strftime("%H:%M:%S")
        
        # Get login time from session
        login_time = st.session_state.get("start_time")
        if not login_time:
            login_time = current_time_str
            st.warning("⚠️ No login time recorded. Using current time as start time.")
        
        # Create session string
        session_string = f"{login_time} - {current_time_str}"
        
        student_roll = st.session_state.get("roll_number")
        
        # First, check if student already has a track field for today
        course_data = collection.find_one({
            "academicYear": st.session_state.get("year"),
            "department": st.session_state.get("department"),
            "courseName": st.session_state.get("subject")
        })
        
        if not course_data:
            st.error("❌ Course data not found")
            return
        
        # Find the student in the enrolledStudents array
        student_found = False
        student_index = -1
        
        for idx, student in enumerate(course_data.get("enrolledStudents", [])):
            if student.get("student_roll_number") == student_roll:
                student_found = True
                student_index = idx
                break
        
        if not student_found:
            st.error("❌ Student not found in course")
            return
        
        student_path = f"enrolledStudents.{student_index}"
        existing_student = course_data["enrolledStudents"][student_index]
        
        # Calculate session duration for display
        try:
            login_dt = datetime.strptime(login_time, "%H:%M:%S")
            current_dt = datetime.strptime(current_time_str, "%H:%M:%S")
            diff_seconds = (current_dt - login_dt).total_seconds()
            if diff_seconds < 0:
                diff_seconds += 86400
            
            hours = int(diff_seconds // 3600)
            minutes = int((diff_seconds % 3600) // 60)
            seconds = int(diff_seconds % 60)
            
            if hours > 0:
                duration_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                duration_str = f"{minutes}m {seconds}s"
            else:
                duration_str = f"{seconds}s"
        except:
            duration_str = "Unknown"
        
        # Check if track field exists
        if "track" not in existing_student:
            # Create track field with today's entry
            track_entry = {
                "date": current_date,
                "study_time": [session_string]
            }
            
            result = collection.update_one(
                {
                    "academicYear": st.session_state.get("year"),
                    "department": st.session_state.get("department"),
                    "courseName": st.session_state.get("subject"),
                    f"{student_path}.student_roll_number": student_roll
                },
                {
                    "$set": {
                        f"{student_path}.track": [track_entry]
                    }
                }
            )
            
            if result.modified_count > 0:
                st.toast("✅ Progress saved successfully!")
                st.success(f"✅ Your session has been saved!")
                st.info(f"📌 Session: {session_string}")
                st.info(f"⏱️ Duration: {duration_str}")
                # Auto logout after saving
                logout_user()
                return
            else:
                st.error("❌ Failed to save session. Please try again.")
                return
        else:
            # Check if today's date already exists in track
            today_entry_index = -1
            for idx, entry in enumerate(existing_student["track"]):
                if entry.get("date") == current_date:
                    today_entry_index = idx
                    break
            
            if today_entry_index >= 0:
                # Update existing today's entry - append new session
                track_path = f"{student_path}.track.{today_entry_index}.study_time"
                
                result = collection.update_one(
                    {
                        "academicYear": st.session_state.get("year"),
                        "department": st.session_state.get("department"),
                        "courseName": st.session_state.get("subject"),
                        f"{student_path}.student_roll_number": student_roll
                    },
                    {
                        "$push": {
                            track_path: session_string
                        }
                    }
                )
                
                if result.modified_count > 0:
                    st.toast("✅ Progress saved successfully!")
                    st.success(f"✅ Your session has been added to today's progress!")
                    st.info(f"📌 Session: {session_string}")
                    st.info(f"⏱️ Duration: {duration_str}")
                    # Auto logout after saving
                    logout_user()
                    return
                else:
                    st.error("❌ Failed to save session. Please try again.")
                    return
            else:
                # Create new entry for today
                track_entry = {
                    "date": current_date,
                    "study_time": [session_string]
                }
                
                result = collection.update_one(
                    {
                        "academicYear": st.session_state.get("year"),
                        "department": st.session_state.get("department"),
                        "courseName": st.session_state.get("subject"),
                        f"{student_path}.student_roll_number": student_roll
                    },
                    {
                        "$push": {
                            f"{student_path}.track": track_entry
                        }
                    }
                )
                
                if result.modified_count > 0:
                    st.toast("✅ Progress saved successfully!")
                    st.success(f"✅ Your session has been saved!")
                    st.info(f"📌 Session: {session_string}")
                    st.info(f"⏱️ Duration: {duration_str}")
                    # Auto logout after saving
                    logout_user()
                    return
                else:
                    st.error("❌ Failed to save session. Please try again.")
                    return
        
    except Exception as e:
        st.error(f"❌ Error saving progress: {str(e)}")

def logout_user():
    """
    Logout the user and clear session state
    """
    # Keep only database connection
    keep_keys = ["client", "db", "collection"]
    for key in list(st.session_state.keys()):
        if key not in keep_keys:
            del st.session_state[key]
    
    st.rerun()

def main3():
    """
    Wrapper function for the save progress section
    Called from mainFile.py when 'Save My Progress' is selected
    """
    main_layout()

# If you want to test this file independently
if __name__ == "__main__":
    main_layout()