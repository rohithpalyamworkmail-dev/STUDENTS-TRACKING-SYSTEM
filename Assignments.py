import streamlit as st
from datetime import datetime
import pandas as pd
from mongodb1 import *

def main_layout():
    """
    Main layout for the Assignment section
    Allows students to view and attempt assignments
    """
    st.subheader("📝 My Assignments", divider="orange", text_alignment="center")
    
    # Check if user is logged in and has necessary session data
    if "roll_number" not in st.session_state or not st.session_state["roll_number"]:
        st.warning("⚠️ Please log in to view assignments")
        return
    
    # Create two columns with 1:2 ratio
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Selection filters
    with col1:
        st.subheader("🔍 Select Assignment", divider="blue")
        
        # Get current course data
        course_data = st.session_state.get("course_data")
        
        # If course_data not in session, fetch it
        if not course_data:
            collection = st.session_state.get("collection")
            if collection is not None:
                course_data = collection.find_one({
                    "academicYear": st.session_state.get("year"),
                    "department": st.session_state.get("department"),
                    "courseName": st.session_state.get("subject")
                })
                st.session_state["course_data"] = course_data
        
        if not course_data or "tasks" not in course_data or not course_data["tasks"]:
            st.info("ℹ️ No assignments available for this course")
            return
        
        # Get unique task dates
        task_dates = sorted(list(set([task["task_date"] for task in course_data["tasks"]])))
        
        # Date input for selecting task date
        if task_dates:
            selected_date = st.date_input(
                "Select Assignment Date",
                value=datetime.strptime(task_dates[0], "%Y-%m-%d").date() if task_dates else datetime.now().date()
            )
            selected_date_str = selected_date.strftime("%Y-%m-%d")
            
            if selected_date_str:
                # Get tasks for selected date
                tasks_for_date = [task for task in course_data["tasks"] if task["task_date"] == selected_date_str]
                
                if tasks_for_date:
                    task_names = [task["task_name"] for task in tasks_for_date]
                    selected_task_name = st.selectbox(
                        "Select Assignment",
                        task_names,
                        key="assignment_select"
                    )
                    
                    if selected_task_name:
                        # Find the selected task
                        selected_task = next(
                            (task for task in tasks_for_date if task["task_name"] == selected_task_name),
                            None
                        )
                        
                        if selected_task:
                            # Check student status for this task
                            student_roll = st.session_state["roll_number"]
                            student_stats = None
                            
                            if "stats" in selected_task:
                                for stat in selected_task["stats"]:
                                    if stat["student_roll_number"] == student_roll:
                                        student_stats = stat
                                        break
                            
                            if student_stats:
                                status = student_stats.get("status", "incomplete")
                                
                                # Display status
                                if status == "completed":
                                    st.success(f"✅ Already Completed!")
                                    st.write(f"**Marks Obtained:** {student_stats.get('total_marks_obtained', 0)}/{selected_task.get('total_marks', 0)}")
                                    st.write(f"**Completed Date:** {student_stats.get('completed_date', 'N/A')}")
                                    st.info("ℹ️ You have already attempted this assignment. You cannot re-attempt it.")
                                else:
                                    st.warning("⏳ Not Completed")
                                    st.write("**Status:** Incomplete")
                                    st.write(f"**Total Marks:** {selected_task.get('total_marks', 0)}")
                                    
                                    # Attempt test button - only show if status is incomplete
                                    if st.button("📝 Attempt Test", use_container_width=True):
                                        st.session_state["attempting_task"] = {
                                            "task_date": selected_date_str,
                                            "task_name": selected_task_name
                                        }
                                        st.session_state["show_assignment"] = True
                                        st.session_state["assignment_answers"] = {}
                                        st.session_state["assignment_start_time"] = None
                                        st.rerun()
    
    # Column 2: Display assignment content
    with col2:
        # Check if we should show the assignment attempt
        if st.session_state.get("show_assignment", False) and "attempting_task" in st.session_state:
            attempt_data = st.session_state["attempting_task"]
            
            # Find the task
            task = None
            course_data = st.session_state.get("course_data")
            if course_data:
                for t in course_data["tasks"]:
                    if t["task_date"] == attempt_data["task_date"] and t["task_name"] == attempt_data["task_name"]:
                        task = t
                        break
            
            if task:
                # Double check if already completed before showing the test
                student_roll = st.session_state["roll_number"]
                student_stat = None
                for stat in task["stats"]:
                    if stat["student_roll_number"] == student_roll:
                        student_stat = stat
                        break
                
                if student_stat and student_stat.get("status") == "completed":
                    st.warning("⚠️ You have already completed this assignment!")
                    st.write(f"**Marks:** {student_stat.get('total_marks_obtained', 0)}/{task.get('total_marks', 0)}")
                    st.write(f"**Completed Date:** {student_stat.get('completed_date', 'N/A')}")
                    st.info("ℹ️ You cannot re-attempt this assignment as it is already completed.")
                    if st.button("🔄 Go Back", use_container_width=True):
                        st.session_state["show_assignment"] = False
                        if "attempting_task" in st.session_state:
                            del st.session_state["attempting_task"]
                        st.rerun()
                    return
                
                # Record start time if not already set
                if st.session_state.get("assignment_start_time") is None:
                    st.session_state["assignment_start_time"] = datetime.now().strftime("%H:%M:%S")
                
                # Display assignment attempt form
                st.subheader(f"📝 {task['task_name']}", divider="blue")
                st.write(f"**Date:** {task['task_date']}")
                st.write(f"**Total Questions:** {len(task.get('questions', []))}")
                st.write(f"**Total Marks:** {task.get('total_marks', 0)}")
                
                st.divider()
                
                # Initialize answers in session state if not exists
                if "assignment_answers" not in st.session_state:
                    st.session_state["assignment_answers"] = {}
                
                # Display questions with selectboxes
                questions = task.get("questions", [])
                
                for idx, question in enumerate(questions):
                    # Get options
                    options = [
                        question.get("option a", ""),
                        question.get("option b", ""),
                        question.get("option c", ""),
                        question.get("option d", "")
                    ]
                    options = [opt for opt in options if opt]  # Remove empty options
                    
                    # Display question with selectbox
                    st.write(f"**Q{idx+1}.** {question.get('question name', '')}")
                    
                    # Create a unique key for each selectbox
                    select_key = f"q_{idx}_{task['task_date']}_{task['task_name']}"
                    
                    # Get current answer from session state
                    current_answer = st.session_state["assignment_answers"].get(select_key, "")
                    
                    # Find index for selectbox
                    options_with_default = ["Select an option..."] + options
                    if current_answer and current_answer in options:
                        default_index = options.index(current_answer) + 1
                    else:
                        default_index = 0
                    
                    answer = st.selectbox(
                        "Select your answer",
                        options=options_with_default,
                        index=default_index,
                        key=select_key,
                        label_visibility="collapsed"
                    )
                    
                    # Store answer in session state
                    if answer and answer != "Select an option...":
                        st.session_state["assignment_answers"][select_key] = answer
                    
                    st.divider()
                
                # Submit and Cancel buttons
                col_submit1, col_submit2 = st.columns(2)
                with col_submit1:
                    if st.button("📤 Submit Assignment", type="primary", use_container_width=True):
                        # Check if all questions are answered
                        total_questions = len(questions)
                        answered_count = len(st.session_state["assignment_answers"])
                        
                        if answered_count < total_questions:
                            st.error(f"⚠️ Please answer all {total_questions} questions. You have answered {answered_count}.")
                        else:
                            # Calculate marks
                            marks_obtained = 0
                            for idx, question in enumerate(questions):
                                select_key = f"q_{idx}_{task['task_date']}_{task['task_name']}"
                                student_answer = st.session_state["assignment_answers"].get(select_key, "")
                                correct_answer = question.get("correct answer", "")
                                
                                if student_answer == correct_answer:
                                    marks_obtained += 1
                            
                            # Update session state with marks
                            st.session_state["assignment_marks"] = marks_obtained
                            st.session_state["submit_assignment"] = True
                            st.session_state["show_assignment"] = False  # Hide the form
                            st.rerun()
                
                with col_submit2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state["assignment_answers"] = {}
                        st.session_state["assignment_start_time"] = None
                        st.session_state["show_assignment"] = False
                        if "attempting_task" in st.session_state:
                            del st.session_state["attempting_task"]
                        st.rerun()
        
        # Check if assignment was just submitted
        elif st.session_state.get("submit_assignment", False):
            # Show submission result
            marks = st.session_state.get("assignment_marks", 0)
            total_marks = 0
            task_name = ""
            task_date = ""
            
            # Find the task to get total marks
            if "attempting_task" in st.session_state:
                attempt_data = st.session_state["attempting_task"]
                task_date = attempt_data.get("task_date", "")
                task_name = attempt_data.get("task_name", "")
                course_data = st.session_state.get("course_data")
                if course_data:
                    for t in course_data["tasks"]:
                        if t["task_date"] == task_date and t["task_name"] == task_name:
                            total_marks = t.get("total_marks", 0)
                            break
            
            # Display results
            st.subheader("📊 Assignment Results", divider="orange")
            
            # Create a nice result card
            with st.container(border=True):
                st.write(f"**📝 Assignment:** {task_name}")
                st.write(f"**📅 Date:** {task_date}")
                st.write(f"**✅ Marks Obtained:** {marks}/{total_marks}")
                
                # Calculate percentage
                if total_marks > 0:
                    percentage = (marks / total_marks) * 100
                    st.write(f"**📈 Percentage:** {percentage:.1f}%")
                    
                    # Show performance indicator
                    if percentage >= 80:
                        st.success("🌟 Excellent Performance!")
                    elif percentage >= 60:
                        st.info("👍 Good Performance!")
                    elif percentage >= 40:
                        st.warning("📚 Needs Improvement!")
                    else:
                        st.error("💪 Keep Practicing!")
            
            # Check if student has already completed this assignment (safety check)
            student_roll = st.session_state["roll_number"]
            already_completed = False
            course_data = st.session_state.get("course_data")
            if course_data:
                for t in course_data["tasks"]:
                    if t["task_date"] == task_date and t["task_name"] == task_name:
                        for stat in t["stats"]:
                            if stat["student_roll_number"] == student_roll and stat.get("status") == "completed":
                                already_completed = True
                                break
                        break
            
            if already_completed:
                st.warning("⚠️ This assignment was already completed. Results cannot be saved again.")
                if st.button("🔄 Go Back to Assignments", use_container_width=True):
                    # Clean up session state
                    st.session_state["submit_assignment"] = False
                    st.session_state["assignment_marks"] = 0
                    if "attempting_task" in st.session_state:
                        del st.session_state["attempting_task"]
                    st.session_state["assignment_answers"] = {}
                    st.session_state["assignment_start_time"] = None
                    st.rerun()
            else:
                # Save results to database
                col_save1, col_save2 = st.columns(2)
                with col_save1:
                    if st.button("✅ Save Results", type="primary", use_container_width=True):
                        # Update database with results
                        success = update_assignment_results(marks)
                        
                        if success:
                            # Clean up session state
                            st.session_state["submit_assignment"] = False
                            st.session_state["assignment_marks"] = 0
                            if "attempting_task" in st.session_state:
                                del st.session_state["attempting_task"]
                            st.session_state["assignment_answers"] = {}
                            st.session_state["assignment_start_time"] = None
                            st.success("✅ Results saved successfully!")
                            st.rerun()
                
                with col_save2:
                    if st.button("❌ Discard Results", use_container_width=True):
                        # Clean up session state without saving
                        st.session_state["submit_assignment"] = False
                        st.session_state["assignment_marks"] = 0
                        if "attempting_task" in st.session_state:
                            del st.session_state["attempting_task"]
                        st.session_state["assignment_answers"] = {}
                        st.session_state["assignment_start_time"] = None
                        st.warning("⚠️ Results discarded. You can re-attempt the assignment.")
                        st.rerun()
        
        else:
            # Default view - show available assignments
            if "course_data" in st.session_state and st.session_state["course_data"]:
                course = st.session_state["course_data"]
                tasks = course.get("tasks", [])
                
                if tasks:
                    st.subheader("📊 Available Assignments", divider="blue")
                    
                    # Create a DataFrame for better display
                    task_data = []
                    for task in tasks:
                        # Check student status for this task
                        student_roll = st.session_state["roll_number"]
                        student_stat = None
                        for stat in task.get("stats", []):
                            if stat["student_roll_number"] == student_roll:
                                student_stat = stat
                                break
                        
                        if student_stat:
                            status = student_stat.get("status", "incomplete")
                            marks = student_stat.get("total_marks_obtained", 0)
                            total = task.get("total_marks", 0)
                            
                            task_data.append({
                                "Date": task["task_date"],
                                "Assignment": task["task_name"],
                                "Status": "✅ Completed" if status == "completed" else "⏳ Incomplete",
                                "Marks": f"{marks}/{total}" if status == "completed" else "-"
                            })
                    
                    if task_data:
                        df = pd.DataFrame(task_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Summary statistics
                        st.divider()
                        st.subheader("📈 Summary")
                        completed_count = sum(1 for row in task_data if "Completed" in row["Status"])
                        total_count = len(task_data)
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("📝 Total Assignments", total_count)
                        col2.metric("✅ Completed", completed_count)
                        col3.metric("⏳ Pending", total_count - completed_count)
                    else:
                        st.info("ℹ️ No assignments available")
                else:
                    st.info("ℹ️ No assignments found for this course")

def update_assignment_results(marks_obtained):
    """
    Update the assignment results in the database
    """
    try:
        collection = st.session_state.get("collection")
        if collection is None:
            st.error("❌ Database connection failed")
            return False
        
        # Get current time
        current_time = datetime.now()
        current_date = current_time.strftime("%Y-%m-%d")
        current_time_str = current_time.strftime("%H:%M:%S")
        
        # Get assignment data from session
        attempt_data = st.session_state.get("attempting_task", {})
        if not attempt_data:
            st.error("❌ No assignment data found")
            return False
        
        # Get course data from session
        course_data = st.session_state.get("course_data")
        if not course_data:
            st.error("❌ No course data found")
            return False
        
        # Find the task and update the student's stats
        task_date = attempt_data["task_date"]
        task_name = attempt_data["task_name"]
        student_roll = st.session_state["roll_number"]
        
        # First, check if the student already completed this assignment
        for task in course_data["tasks"]:
            if task["task_date"] == task_date and task["task_name"] == task_name:
                for stat in task["stats"]:
                    if stat["student_roll_number"] == student_roll:
                        if stat.get("status") == "completed":
                            st.warning("⚠️ This assignment was already completed. Cannot save results again.")
                            return False
        
        # Find the task index and stat index
        task_found = False
        for task_idx, task in enumerate(course_data["tasks"]):
            if task["task_date"] == task_date and task["task_name"] == task_name:
                task_found = True
                
                # Find the student's stat
                for stat_idx, stat in enumerate(task["stats"]):
                    if stat["student_roll_number"] == student_roll:
                        # Prepare the update path
                        stats_path = f"tasks.{task_idx}.stats.{stat_idx}"
                        
                        # Update the document
                        result = collection.update_one(
                            {
                                "academicYear": st.session_state["year"],
                                "department": st.session_state["department"],
                                "courseName": st.session_state["subject"]
                            },
                            {
                                "$set": {
                                    f"{stats_path}.status": "completed",
                                    f"{stats_path}.total_marks_obtained": marks_obtained,
                                    f"{stats_path}.completed_date": current_date,
                                    f"{stats_path}.started_at": st.session_state.get("assignment_start_time", current_time_str),
                                    f"{stats_path}.ended_at": current_time_str
                                }
                            }
                        )
                        
                        if result.modified_count > 0:
                            # Update session state course_data
                            updated_course_data = collection.find_one({
                                "academicYear": st.session_state["year"],
                                "department": st.session_state["department"],
                                "courseName": st.session_state["subject"]
                            })
                            st.session_state["course_data"] = updated_course_data
                            st.success(f"✅ Results saved successfully! You scored {marks_obtained}/{task.get('total_marks', 0)}")
                            return True
                        else:
                            st.error("❌ Failed to save results. Please try again.")
                            return False
        
        if not task_found:
            st.error("❌ Task not found")
            return False
            
    except Exception as e:
        st.error(f"❌ Error saving results: {str(e)}")
        return False

def main2():
    """
    Wrapper function for the assignment section
    Called from mainFile.py when 'Assignment' is selected
    """
    main_layout()

# If you want to test this file independently
if __name__ == "__main__":
    main_layout()