import streamlit as st
import pandas as pd
from mongodb import *
from bson import ObjectId
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def main2():
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Add Tasks", "Edit Tasks", "View Tasks", "Delete Tasks", "Stats"])
    
    with tab1:
        add_tasks()
    with tab2:
        edit_tasks()
    with tab3:
        view_tasks()
    with tab4:
        delete_tasks()
    with tab5:
        stats_tasks()

def add_tasks():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Selection filters
    academic_year = col1.pills("Select Academic Year", ["2025-2029", "2024-2028", "2023-2027"], key="add_task_academic")
    department = col1.segmented_control("Select Department", ["AI&DS", "DS", "AI", "CSE"], key="add_task_dept")
    
    if academic_year and department:
        # Fetch unique course names
        courses_cursor = st.session_state["collection"].distinct(
            "courseName",
            {"academicYear": academic_year, "department": department}
        )
        
        if courses_cursor:
            subject = col1.radio(
                "Select Course",
                courses_cursor,
                horizontal=True,
                key="add_task_subject"
            )
            
            if subject:
                # Column 2: Add task form
                col2.subheader(f"Add Task for: {subject}", divider="blue")
                
                task_date = col2.date_input("Select Task Date", key="add_task_date")
                task_name = col2.text_input("Enter Task Name", key="add_task_name")
                task_file = col2.file_uploader("Upload Questions CSV", type=["csv"], key="add_task_file")
                
                if task_file:
                    try:
                        df = pd.read_csv(task_file)
                        
                        # Check if all required columns are present
                        required_columns = ["question name", "option a", "option b", "option c", "option d", "correct answer"]
                        
                        if all(col in df.columns for col in required_columns):
                            col2.success("✅ All required columns are present!")
                            col2.dataframe(df)
                            
                            # Fetch enrolled students for stats
                            course_doc = st.session_state["collection"].find_one({
                                "academicYear": academic_year,
                                "department": department,
                                "courseName": subject
                            })
                            
                            if course_doc and "enrolledStudents" in course_doc:
                                # Create stats for each student
                                stats_list = []
                                for student in course_doc["enrolledStudents"]:
                                    stats_list.append({
                                        "student_roll_number": student.get("student_roll_number", ""),
                                        "student_name": student.get("student_name", ""),
                                        "completed_date": None,
                                        "started_at": None,
                                        "ended_at": None,
                                        "status": "incomplete",
                                        "total_marks_obtained": 0
                                    })
                                
                                add_button = col2.button(
                                    "Add Task",
                                    type="primary",
                                    use_container_width=True,
                                    key="add_task_button"
                                )
                                
                                if add_button:
                                    # Create task document
                                    task_doc = {
                                        "task_date": task_date.strftime("%Y-%m-%d"),
                                        "task_name": task_name,
                                        "questions": df.to_dict(orient="records"),
                                        "stats": stats_list,
                                        "total_marks": df.shape[0]
                                    }
                                    
                                    # Update the course document - push to tasks array
                                    result = st.session_state["collection"].update_one(
                                        {
                                            "academicYear": academic_year,
                                            "department": department,
                                            "courseName": subject
                                        },
                                        {
                                            "$push": {"tasks": task_doc}
                                        }
                                    )
                                    
                                    if result.modified_count > 0:
                                        col2.success("✅ Task added successfully!")
                                        col2.balloons()
                                    else:
                                        col2.error("Failed to add task. Please try again.")
                            else:
                                col2.warning("No enrolled students found for this course")
                        else:
                            missing_cols = [col for col in required_columns if col not in df.columns]
                            col2.warning(f"⚠️ Missing columns: {', '.join(missing_cols)}")
                            col2.info("Required columns: question name, option a, option b, option c, option d, correct answer")
                    except Exception as e:
                        col2.error(f"Error reading CSV file: {str(e)}")
        else:
            col1.warning("No courses found for the selected batch and department")

def edit_tasks():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Selection filters
    academic_year = col1.pills("Select Academic Year", ["2025-2029", "2024-2028", "2023-2027"], key="edit_task_academic")
    department = col1.segmented_control("Select Department", ["AI&DS", "DS", "AI", "CSE"], key="edit_task_dept")
    
    if academic_year and department:
        # Fetch unique course names
        courses_cursor = st.session_state["collection"].distinct(
            "courseName",
            {"academicYear": academic_year, "department": department}
        )
        
        if courses_cursor:
            subject = col1.radio(
                "Select Course",
                courses_cursor,
                horizontal=True,
                key="edit_task_subject"
            )
            
            if subject:
                # Fetch the course document
                course = st.session_state["collection"].find_one({
                    "academicYear": academic_year,
                    "department": department,
                    "courseName": subject
                })
                
                if course and "tasks" in course and course["tasks"]:
                    # Column 2: Edit tasks
                    col2.subheader(f"Edit Tasks for: {subject}", divider="blue")
                    
                    # Select what to edit
                    edit_option = col2.radio(
                        "Select what to edit",
                        ["Date & Name", "Questions"],
                        horizontal=True,
                        key="edit_task_option"
                    )
                    
                    if edit_option == "Date & Name":
                        # Get unique task_date-task_name combinations
                        task_options = []
                        for task in course["tasks"]:
                            task_options.append(f"{task['task_date']} - {task['task_name']}")
                        
                        if task_options:
                            selected_task = col2.selectbox(
                                "Select Task to Edit",
                                task_options,
                                key="edit_task_select"
                            )
                            
                            if selected_task:
                                # Find the selected task
                                task_date, task_name = selected_task.split(" - ", 1)
                                selected_task_doc = next(
                                    (t for t in course["tasks"] if t["task_date"] == task_date and t["task_name"] == task_name),
                                    None
                                )
                                
                                if selected_task_doc:
                                    # Display current values
                                    st.divider()
                                    col2.write("**Current Values:**")
                                    col2.write(f"Task Date: {selected_task_doc['task_date']}")
                                    col2.write(f"Task Name: {selected_task_doc['task_name']}")
                                    
                                    # Edit fields
                                    st.divider()
                                    new_task_date = col2.date_input(
                                        "New Task Date",
                                        value=datetime.strptime(selected_task_doc['task_date'], "%Y-%m-%d").date(),
                                        key="edit_task_new_date"
                                    )
                                    new_task_name = col2.text_input(
                                        "New Task Name",
                                        value=selected_task_doc['task_name'],
                                        key="edit_task_new_name"
                                    )
                                    
                                    update_button = col2.button(
                                        "Update Task Details",
                                        type="primary",
                                        use_container_width=True,
                                        key="edit_task_update_details"
                                    )
                                    
                                    if update_button:
                                        # Update the specific task
                                        result = st.session_state["collection"].update_one(
                                            {
                                                "academicYear": academic_year,
                                                "department": department,
                                                "courseName": subject,
                                                "tasks.task_date": task_date,
                                                "tasks.task_name": task_name
                                            },
                                            {
                                                "$set": {
                                                    "tasks.$.task_date": new_task_date.strftime("%Y-%m-%d"),
                                                    "tasks.$.task_name": new_task_name
                                                }
                                            }
                                        )
                                        
                                        if result.modified_count > 0:
                                            col2.success("✅ Task details updated successfully!")
                                            st.rerun()
                                        else:
                                            col2.error("Failed to update task details. Please try again.")
                        else:
                            col2.info("No tasks found for this course")
                    
                    elif edit_option == "Questions":
                        # Get unique task dates
                        task_dates = list(set([t["task_date"] for t in course["tasks"]]))
                        
                        if task_dates:
                            selected_date = col2.selectbox(
                                "Select Task Date",
                                task_dates,
                                key="edit_task_date"
                            )
                            
                            if selected_date:
                                # Get task names for selected date
                                date_tasks = [t for t in course["tasks"] if t["task_date"] == selected_date]
                                task_names = [t["task_name"] for t in date_tasks]
                                
                                if task_names:
                                    selected_task_name = col2.selectbox(
                                        "Select Task Name",
                                        task_names,
                                        key="edit_task_name_select"
                                    )
                                    
                                    if selected_task_name:
                                        # Find the selected task
                                        selected_task_doc = next(
                                            (t for t in date_tasks if t["task_name"] == selected_task_name),
                                            None
                                        )
                                        
                                        if selected_task_doc:
                                            # Display questions in data editor
                                            questions_df = pd.DataFrame(selected_task_doc["questions"])
                                            col2.write("**Edit Questions:**")
                                            edited_df = col2.data_editor(
                                                questions_df,
                                                num_rows="dynamic",
                                                key="edit_questions_editor"
                                            )
                                            
                                            update_button = col2.button(
                                                "Update Questions",
                                                type="primary",
                                                use_container_width=True,
                                                key="edit_questions_update"
                                            )
                                            
                                            if update_button:
                                                # Update questions and total marks
                                                result = st.session_state["collection"].update_one(
                                                    {
                                                        "academicYear": academic_year,
                                                        "department": department,
                                                        "courseName": subject,
                                                        "tasks.task_date": selected_date,
                                                        "tasks.task_name": selected_task_name
                                                    },
                                                    {
                                                        "$set": {
                                                            "tasks.$.questions": edited_df.to_dict(orient="records"),
                                                            "tasks.$.total_marks": edited_df.shape[0]
                                                        }
                                                    }
                                                )
                                                
                                                if result.modified_count > 0:
                                                    col2.success("✅ Questions updated successfully!")
                                                    st.rerun()
                                                else:
                                                    col2.error("Failed to update questions. Please try again.")
                                else:
                                    col2.info("No tasks found for the selected date")
                        else:
                            col2.info("No task dates found")
                else:
                    col2.info("No tasks found for this course")
        else:
            col1.warning("No courses found for the selected batch and department")

def view_tasks():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Selection filters
    academic_year = col1.pills("Select Academic Year", ["2025-2029", "2024-2028", "2023-2027"], key="view_task_academic")
    department = col1.segmented_control("Select Department", ["AI&DS", "DS", "AI", "CSE"], key="view_task_dept")
    
    if academic_year and department:
        # Fetch unique course names
        courses_cursor = st.session_state["collection"].distinct(
            "courseName",
            {"academicYear": academic_year, "department": department}
        )
        
        if courses_cursor:
            subject = col1.radio(
                "Select Course",
                courses_cursor,
                horizontal=True,
                key="view_task_subject"
            )
            
            if subject:
                # Fetch the course document
                course = st.session_state["collection"].find_one({
                    "academicYear": academic_year,
                    "department": department,
                    "courseName": subject
                })
                
                if course and "tasks" in course and course["tasks"]:
                    # Column 2: View tasks
                    col2.subheader(f"View Tasks for: {subject}", divider="blue")
                    
                    # Get unique task dates
                    task_dates = list(set([t["task_date"] for t in course["tasks"]]))
                    
                    if task_dates:
                        selected_date = col2.selectbox(
                            "Select Task Date",
                            task_dates,
                            key="view_task_date"
                        )
                        
                        if selected_date:
                            # Get task names for selected date
                            date_tasks = [t for t in course["tasks"] if t["task_date"] == selected_date]
                            task_names = [t["task_name"] for t in date_tasks]
                            
                            if task_names:
                                selected_task_name = col2.selectbox(
                                    "Select Task Name",
                                    task_names,
                                    key="view_task_name"
                                )
                                
                                if selected_task_name:
                                    # Find the selected task
                                    selected_task_doc = next(
                                        (t for t in date_tasks if t["task_name"] == selected_task_name),
                                        None
                                    )
                                    
                                    if selected_task_doc:
                                        # Display task details
                                        col2.write(f"**Task Date:** {selected_task_doc['task_date']}")
                                        col2.write(f"**Task Name:** {selected_task_doc['task_name']}")
                                        col2.write(f"**Total Marks:** {selected_task_doc.get('total_marks', 0)}")
                                        
                                        # Display questions
                                        col2.subheader("Questions", divider="blue")
                                        questions_df = pd.DataFrame(selected_task_doc["questions"])
                                        col2.dataframe(questions_df)
                                        
                                        # Display stats
                                        if "stats" in selected_task_doc and selected_task_doc["stats"]:
                                            col2.subheader("Student Statistics", divider="blue")
                                            stats_df = pd.DataFrame(selected_task_doc["stats"])
                                            col2.dataframe(stats_df)
                            else:
                                col2.info("No tasks found for the selected date")
                    else:
                        col2.info("No tasks found for this course")
                else:
                    col2.info("No tasks found for this course")
        else:
            col1.warning("No courses found for the selected batch and department")

def delete_tasks():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Selection filters
    academic_year = col1.pills("Select Academic Year", ["2025-2029", "2024-2028", "2023-2027"], key="delete_task_academic")
    department = col1.segmented_control("Select Department", ["AI&DS", "DS", "AI", "CSE"], key="delete_task_dept")
    
    if academic_year and department:
        # Fetch unique course names
        courses_cursor = st.session_state["collection"].distinct(
            "courseName",
            {"academicYear": academic_year, "department": department}
        )
        
        if courses_cursor:
            subject = col1.radio(
                "Select Course",
                courses_cursor,
                horizontal=True,
                key="delete_task_subject"
            )
            
            if subject:
                # Fetch the course document
                course = st.session_state["collection"].find_one({
                    "academicYear": academic_year,
                    "department": department,
                    "courseName": subject
                })
                
                if course and "tasks" in course and course["tasks"]:
                    # Column 2: Delete tasks
                    col2.subheader(f"Delete Tasks for: {subject}", divider="blue")
                    
                    # Get unique task dates
                    task_dates = list(set([t["task_date"] for t in course["tasks"]]))
                    
                    if task_dates:
                        selected_date = col2.selectbox(
                            "Select Task Date",
                            task_dates,
                            key="delete_task_date"
                        )
                        
                        if selected_date:
                            # Get task names for selected date
                            date_tasks = [t for t in course["tasks"] if t["task_date"] == selected_date]
                            task_names = [t["task_name"] for t in date_tasks]
                            
                            if task_names:
                                selected_task_name = col2.selectbox(
                                    "Select Task Name to Delete",
                                    task_names,
                                    key="delete_task_name"
                                )
                                
                                if selected_task_name:
                                    # Find the selected task
                                    selected_task_doc = next(
                                        (t for t in date_tasks if t["task_name"] == selected_task_name),
                                        None
                                    )
                                    
                                    if selected_task_doc:
                                        # Display task details
                                        col2.warning(f"⚠️ You are about to delete task: {selected_task_name}")
                                        col2.write(f"**Date:** {selected_task_doc['task_date']}")
                                        col2.write(f"**Total Questions:** {len(selected_task_doc.get('questions', []))}")
                                        
                                        # Show questions in data editor for selection
                                        questions_df = pd.DataFrame(selected_task_doc["questions"])
                                        col2.write("**Questions in this task:**")
                                        edited_df = col2.data_editor(
                                            questions_df,
                                            num_rows="dynamic",
                                            key="delete_questions_editor"
                                        )
                                        
                                        # Delete options
                                        delete_option = col2.radio(
                                            "Delete Option",
                                            ["Delete Entire Task", "Delete Selected Questions"],
                                            horizontal=True,
                                            key="delete_task_option"
                                        )
                                        
                                        if delete_option == "Delete Entire Task":
                                            confirm_text = col2.text_input(
                                                "Type 'DELETE' to confirm deleting entire task",
                                                key="delete_task_confirm"
                                            )
                                            
                                            if col2.button(
                                                "Delete Entire Task",
                                                type="primary",
                                                use_container_width=True,
                                                key="delete_task_button"
                                            ):
                                                if confirm_text == "DELETE":
                                                    # Remove the entire task from tasks array
                                                    result = st.session_state["collection"].update_one(
                                                        {
                                                            "academicYear": academic_year,
                                                            "department": department,
                                                            "courseName": subject
                                                        },
                                                        {
                                                            "$pull": {
                                                                "tasks": {
                                                                    "task_date": selected_date,
                                                                    "task_name": selected_task_name
                                                                }
                                                            }
                                                        }
                                                    )
                                                    
                                                    if result.modified_count > 0:
                                                        col2.success("✅ Task deleted successfully!")
                                                        st.rerun()
                                                    else:
                                                        col2.error("Failed to delete task. Please try again.")
                                                else:
                                                    col2.error("Please type 'DELETE' to confirm")
                                        
                                        else:  # Delete Selected Questions
                                            original_count = len(questions_df)
                                            new_count = len(edited_df)
                                            
                                            if new_count < original_count:
                                                col2.info(f"Removing {original_count - new_count} question(s)")
                                                
                                                if col2.button(
                                                    "Update Questions (Delete Selected)",
                                                    type="primary",
                                                    use_container_width=True,
                                                    key="delete_questions_update"
                                                ):
                                                    # Update questions and total marks
                                                    result = st.session_state["collection"].update_one(
                                                        {
                                                            "academicYear": academic_year,
                                                            "department": department,
                                                            "courseName": subject,
                                                            "tasks.task_date": selected_date,
                                                            "tasks.task_name": selected_task_name
                                                        },
                                                        {
                                                            "$set": {
                                                                "tasks.$.questions": edited_df.to_dict(orient="records"),
                                                                "tasks.$.total_marks": new_count
                                                            }
                                                        }
                                                    )
                                                    
                                                    if result.modified_count > 0:
                                                        col2.success("✅ Questions updated successfully!")
                                                        st.rerun()
                                                    else:
                                                        col2.error("Failed to update questions. Please try again.")
                                            else:
                                                col2.info("No questions were removed. Use the data editor to delete rows.")
                            else:
                                col2.info("No tasks found for the selected date")
                    else:
                        col2.info("No tasks found for this course")
                else:
                    col2.info("No tasks found for this course")
        else:
            col1.warning("No courses found for the selected batch and department")

def stats_tasks():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Selection filters
    academic_year = col1.pills("Select Academic Year", ["2025-2029", "2024-2028", "2023-2027"], key="stats_task_academic")
    department = col1.segmented_control("Select Department", ["AI&DS", "DS", "AI", "CSE"], key="stats_task_dept")
    
    if academic_year and department:
        # Fetch unique course names
        courses_cursor = st.session_state["collection"].distinct(
            "courseName",
            {"academicYear": academic_year, "department": department}
        )
        
        if courses_cursor:
            subject = col1.radio(
                "Select Course",
                courses_cursor,
                horizontal=True,
                key="stats_task_subject"
            )
            
            if subject:
                # Fetch the course document
                course = st.session_state["collection"].find_one({
                    "academicYear": academic_year,
                    "department": department,
                    "courseName": subject
                })
                
                if course and "tasks" in course and course["tasks"]:
                    # Column 2: View stats
                    col2.subheader(f"📊 Statistics Dashboard for: {subject}", divider="blue")
                    
                    # Add View Mode Radio
                    view_mode = col2.radio(
                        "Select View Mode",
                        ["📋 General", "📈 Visualizations"],
                        horizontal=True,
                        key="stats_view_mode"
                    )
                    
                    # Get unique task dates
                    task_dates = list(set([t["task_date"] for t in course["tasks"]]))
                    
                    if task_dates:
                        selected_date = col2.selectbox(
                            "Select Task Date",
                            task_dates,
                            key="stats_task_date"
                        )
                        
                        if selected_date:
                            # Get task names for selected date
                            date_tasks = [t for t in course["tasks"] if t["task_date"] == selected_date]
                            task_names = [t["task_name"] for t in date_tasks]
                            
                            if task_names:
                                if view_mode == "📋 General":
                                    display_general_stats(col2, date_tasks, task_names, course, academic_year, department, subject)
                                else:
                                    display_visualizations(col2, date_tasks, task_names, course, academic_year, department, subject)
                            else:
                                col2.info("No tasks found for the selected date")
                    else:
                        col2.info("No tasks found for this course")
                else:
                    col2.info("No tasks found for this course")
        else:
            col1.warning("No courses found for the selected batch and department")

def display_general_stats(col2, date_tasks, task_names, course, academic_year, department, subject):
    """Display general statistics view"""
    
    selected_task_name = col2.selectbox(
        "Select Task Name",
        task_names,
        key="stats_task_name_general"
    )
    
    if selected_task_name:
        # Find the selected task
        selected_task_doc = next(
            (t for t in date_tasks if t["task_name"] == selected_task_name),
            None
        )
        
        if selected_task_doc and "stats" in selected_task_doc:
            # Display stats
            stats_df = pd.DataFrame(selected_task_doc["stats"])
            
            if not stats_df.empty:
                col2.write(f"**Task Date:** {selected_task_doc['task_date']}")
                col2.write(f"**Task Name:** {selected_task_doc['task_name']}")
                col2.write(f"**Total Marks:** {selected_task_doc.get('total_marks', 0)}")
                col2.write(f"**Total Students:** {len(stats_df)}")
                
                col2.subheader("📊 Student Performance Statistics", divider="blue")
                
                # Add summary statistics in columns
                col_metrics1, col_metrics2, col_metrics3 = col2.columns(3)
                
                completed_count = len(stats_df[stats_df['status'] == 'completed'])
                incomplete_count = len(stats_df[stats_df['status'] == 'incomplete'])
                
                col_metrics1.metric(
                    "✅ Completed",
                    completed_count,
                    delta=f"{completed_count/len(stats_df)*100:.1f}%"
                )
                col_metrics2.metric(
                    "⏳ Incomplete",
                    incomplete_count,
                    delta=f"{incomplete_count/len(stats_df)*100:.1f}%"
                )
                
                # Calculate average marks if any completed
                completed_students = stats_df[stats_df['status'] == 'completed']
                if not completed_students.empty:
                    avg_marks = completed_students['total_marks_obtained'].mean()
                    max_marks = selected_task_doc.get('total_marks', 0)
                    col_metrics3.metric(
                        "📈 Avg Marks (Completed)",
                        f"{avg_marks:.2f}/{max_marks}",
                        delta=f"{avg_marks/max_marks*100:.1f}%"
                    )
                else:
                    col_metrics3.metric("📈 Avg Marks", "No completions")
                
                # Display detailed statistics table
                col2.subheader("📋 Detailed Student Data", divider="blue")
                
                # Display dataframe without styling to avoid applymap error
                col2.dataframe(stats_df, use_container_width=True)
            else:
                col2.info("No statistics found for this task")
        else:
            col2.info("No statistics found for this task")

def display_visualizations(col2, date_tasks, task_names, course, academic_year, department, subject):
    """Display visualizations for task statistics"""
    
    # Get all tasks for the course (not just selected date)
    all_tasks = course.get("tasks", [])
    
    if not all_tasks:
        col2.info("No tasks found for this course")
        return
    
    # Prepare visualization options
    viz_options = [
        "📊 Task Completion Rates",
        "📈 Student Performance Distribution",
        "🏆 Top Performers Leaderboard",
        "📉 Bottom Performers Analysis",
        "📊 Marks Distribution Histogram",
        "📈 Performance Trend Over Time",
        "📅 Task-wise Comparison",
        "👥 Student Performance Heatmap",
        "📊 Completion Status Pie Chart",
        "📈 Average Marks Comparison",
        "🎯 Pass/Fail Analysis",
        "📊 Gender-wise Performance",
        "📈 Student Progress Timeline",
        "📊 Question-wise Difficulty Analysis",
        "📈 Performance Correlation Analysis",
        "📊 Task Difficulty Ranking",
        "🏅 Medal Standings (Gold/Silver/Bronze)",
        "📈 Score Distribution Box Plot",
        "📊 Student Engagement Metrics",
        "📈 Performance Improvement Analysis",
        "📊 Class Performance Summary",
        "📈 Top 10 Students Performance",
        "📊 Task Completion Timeline",
        "📈 Performance Variance Analysis",
        "📊 Overall Course Analytics"
    ]
    
    selected_viz = col2.selectbox(
        "🎯 Select Visualization",
        viz_options,
        key="stats_viz_select"
    )
    
    # Prepare comprehensive data
    all_stats_data = []
    for task in all_tasks:
        for stat in task.get("stats", []):
            if stat.get("status") == "completed":
                all_stats_data.append({
                    "task_date": task.get("task_date", ""),
                    "task_name": task.get("task_name", ""),
                    "student_name": stat.get("student_name", ""),
                    "student_roll_number": stat.get("student_roll_number", ""),
                    "marks": stat.get("total_marks_obtained", 0),
                    "total_marks": task.get("total_marks", 0),
                    "percentage": (stat.get("total_marks_obtained", 0) / task.get("total_marks", 1)) * 100 if task.get("total_marks", 0) > 0 else 0,
                    "completed_date": stat.get("completed_date", ""),
                    "status": stat.get("status", "incomplete")
                })
    
    if not all_stats_data:
        col2.info("No completed task data available for visualizations")
        return
    
    df = pd.DataFrame(all_stats_data)
    
    # Generate selected visualization
    if selected_viz == "📊 Task Completion Rates":
        # Calculate completion rates per task
        completion_data = []
        for task in all_tasks:
            total_students = len(task.get("stats", []))
            completed = len([s for s in task.get("stats", []) if s.get("status") == "completed"])
            completion_data.append({
                "Task": f"{task['task_date']}\n{task['task_name']}",
                "Completion Rate": (completed / total_students * 100) if total_students > 0 else 0,
                "Completed": completed,
                "Total": total_students
            })
        
        df_completion = pd.DataFrame(completion_data)
        
        fig = px.bar(
            df_completion,
            x="Task",
            y="Completion Rate",
            title="Task Completion Rates",
            color="Completion Rate",
            color_continuous_scale="Viridis",
            text="Completion Rate",
            labels={"Completion Rate": "Completion Rate (%)", "Task": "Task"}
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            xaxis_title="Task",
            yaxis_title="Completion Rate (%)",
            height=400,
            showlegend=False
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows the percentage of students who completed each task")
    
    elif selected_viz == "📈 Student Performance Distribution":
        # Distribution of marks across all tasks
        fig = px.histogram(
            df,
            x="percentage",
            nbins=20,
            title="Student Performance Distribution",
            labels={"percentage": "Percentage Score (%)", "count": "Number of Students"},
            color_discrete_sequence=["#FF6B6B"]
        )
        fig.update_layout(
            xaxis_title="Percentage Score (%)",
            yaxis_title="Number of Students",
            height=400,
            showlegend=False
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows the distribution of student scores across all tasks")
    
    elif selected_viz == "🏆 Top Performers Leaderboard":
        # Calculate average performance per student
        student_avg = df.groupby("student_name").agg({
            "marks": "mean",
            "percentage": "mean",
            "task_name": "count"
        }).reset_index()
        student_avg.columns = ["Student", "Avg Marks", "Avg Percentage", "Tasks Completed"]
        student_avg = student_avg.sort_values("Avg Percentage", ascending=False).head(10)
        
        fig = px.bar(
            student_avg,
            x="Student",
            y="Avg Percentage",
            title="Top 10 Performers",
            color="Avg Percentage",
            color_continuous_scale="Viridis",
            text="Avg Percentage",
            hover_data=["Avg Marks", "Tasks Completed"]
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            xaxis_title="Student",
            yaxis_title="Average Percentage (%)",
            height=400,
            showlegend=False
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows the top 10 students based on average performance")
    
    elif selected_viz == "📉 Bottom Performers Analysis":
        # Calculate average performance per student (bottom)
        student_avg = df.groupby("student_name").agg({
            "marks": "mean",
            "percentage": "mean",
            "task_name": "count"
        }).reset_index()
        student_avg.columns = ["Student", "Avg Marks", "Avg Percentage", "Tasks Completed"]
        student_avg = student_avg.sort_values("Avg Percentage").head(10)
        
        fig = px.bar(
            student_avg,
            x="Student",
            y="Avg Percentage",
            title="Bottom 10 Performers (Need Improvement)",
            color="Avg Percentage",
            color_continuous_scale="Reds",
            text="Avg Percentage",
            hover_data=["Avg Marks", "Tasks Completed"]
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            xaxis_title="Student",
            yaxis_title="Average Percentage (%)",
            height=400,
            showlegend=False
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows students who need improvement based on average performance")
    
    elif selected_viz == "📊 Marks Distribution Histogram":
        fig = px.histogram(
            df,
            x="marks",
            nbins=15,
            title="Marks Distribution",
            labels={"marks": "Marks Obtained", "count": "Frequency"},
            color_discrete_sequence=["#4ECDC4"]
        )
        fig.update_layout(
            xaxis_title="Marks Obtained",
            yaxis_title="Frequency",
            height=400,
            showlegend=False
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows how marks are distributed among students")
    
    elif selected_viz == "📈 Performance Trend Over Time":
        # Group by date
        trend_data = df.groupby("task_date").agg({
            "percentage": "mean",
            "marks": "mean"
        }).reset_index()
        trend_data.columns = ["Date", "Avg Percentage", "Avg Marks"]
        trend_data = trend_data.sort_values("Date")
        
        fig = px.line(
            trend_data,
            x="Date",
            y="Avg Percentage",
            title="Average Performance Trend Over Time",
            markers=True,
            labels={"Avg Percentage": "Average Percentage (%)", "Date": "Task Date"}
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Average Percentage (%)",
            height=400
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows how average student performance changes over time")
    
    elif selected_viz == "📅 Task-wise Comparison":
        # Compare tasks
        task_avg = df.groupby(["task_date", "task_name"]).agg({
            "percentage": "mean",
            "marks": "mean",
            "student_name": "count"
        }).reset_index()
        task_avg.columns = ["Date", "Task", "Avg Percentage", "Avg Marks", "Students"]
        
        fig = px.bar(
            task_avg,
            x="Task",
            y="Avg Percentage",
            title="Task-wise Performance Comparison",
            color="Avg Percentage",
            color_continuous_scale="Plasma",
            text="Avg Percentage",
            hover_data=["Date", "Avg Marks", "Students"]
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            xaxis_title="Task",
            yaxis_title="Average Percentage (%)",
            height=400,
            showlegend=False,
            xaxis_tickangle=-45
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Compares average performance across different tasks")
    
    elif selected_viz == "👥 Student Performance Heatmap":
        # Create heatmap of student performance across tasks
        pivot_data = df.pivot_table(
            values="percentage",
            index="student_name",
            columns="task_name",
            aggfunc="first",
            fill_value=0
        )
        
        fig = px.imshow(
            pivot_data,
            title="Student Performance Heatmap",
            labels=dict(x="Task", y="Student", color="Percentage (%)"),
            color_continuous_scale="Viridis",
            aspect="auto"
        )
        fig.update_layout(height=500)
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows how each student performed on each task (color-coded)")
    
    elif selected_viz == "📊 Completion Status Pie Chart":
        # Overall completion status
        total_completed = len(df)
        total_students_all = sum(len(t.get("stats", [])) for t in all_tasks)
        total_incomplete = total_students_all - total_completed
        
        status_data = pd.DataFrame({
            "Status": ["Completed", "Incomplete"],
            "Count": [total_completed, total_incomplete]
        })
        
        fig = px.pie(
            status_data,
            values="Count",
            names="Status",
            title="Overall Task Completion Status",
            color_discrete_sequence=["#4ECDC4", "#FF6B6B"]
        )
        fig.update_layout(height=400)
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows the overall completion ratio across all tasks")
    
    elif selected_viz == "📈 Average Marks Comparison":
        # Group by student
        student_avg = df.groupby("student_name").agg({
            "marks": "mean",
            "percentage": "mean"
        }).reset_index()
        student_avg.columns = ["Student", "Avg Marks", "Avg Percentage"]
        student_avg = student_avg.sort_values("Avg Percentage", ascending=False)
        
        fig = px.bar(
            student_avg.head(15),
            x="Student",
            y="Avg Marks",
            title="Average Marks by Student (Top 15)",
            color="Avg Percentage",
            color_continuous_scale="Viridis",
            text="Avg Marks",
            hover_data=["Avg Percentage"]
        )
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(
            xaxis_title="Student",
            yaxis_title="Average Marks",
            height=400,
            showlegend=False
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows average marks for each student")
    
    elif selected_viz == "🎯 Pass/Fail Analysis":
        # Define pass as 40% and above
        df["Result"] = df["percentage"].apply(lambda x: "Pass" if x >= 40 else "Fail")
        pass_fail = df.groupby("task_name")["Result"].value_counts().unstack().fillna(0)
        
        fig = px.bar(
            pass_fail,
            barmode="group",
            title="Pass/Fail Analysis by Task",
            labels={"value": "Number of Students", "task_name": "Task", "Result": "Result"},
            color_discrete_sequence=["#4ECDC4", "#FF6B6B"]
        )
        fig.update_layout(
            xaxis_title="Task",
            yaxis_title="Number of Students",
            height=400
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows pass/fail distribution for each task (40% passing threshold)")
    
    elif selected_viz == "📊 Gender-wise Performance":
        # Get gender data from course
        students_data = course.get("enrolledStudents", [])
        student_gender = {}
        for student in students_data:
            student_gender[student.get("student_name", "")] = student.get("student_gender", "Unknown")
        
        # Add gender to df
        df["Gender"] = df["student_name"].map(student_gender)
        df_gender = df.dropna(subset=["Gender"])
        
        if not df_gender.empty:
            gender_avg = df_gender.groupby("Gender")["percentage"].mean().reset_index()
            
            fig = px.bar(
                gender_avg,
                x="Gender",
                y="percentage",
                title="Average Performance by Gender",
                color="Gender",
                color_discrete_sequence=["#FF6B6B", "#4ECDC4"],
                text="percentage"
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(
                xaxis_title="Gender",
                yaxis_title="Average Percentage (%)",
                height=400,
                showlegend=False
            )
            col2.plotly_chart(fig, use_container_width=True)
            col2.info("💡 Shows performance comparison between genders")
        else:
            col2.info("No gender data available")
    
    elif selected_viz == "📈 Student Progress Timeline":
        # For each student, show their progress
        student_choice = col2.selectbox(
            "Select Student to View",
            sorted(df["student_name"].unique()),
            key="student_timeline_select"
        )
        
        if student_choice:
            student_data = df[df["student_name"] == student_choice].sort_values("task_date")
            
            fig = px.line(
                student_data,
                x="task_date",
                y="percentage",
                title=f"Performance Timeline - {student_choice}",
                markers=True,
                labels={"percentage": "Percentage (%)", "task_date": "Task Date"}
            )
            fig.update_layout(
                xaxis_title="Task Date",
                yaxis_title="Percentage (%)",
                height=400
            )
            col2.plotly_chart(fig, use_container_width=True)
            col2.info(f"💡 Shows the performance timeline for {student_choice}")
    
    elif selected_viz == "📊 Question-wise Difficulty Analysis":
        # Analyze question difficulty based on student answers
        difficulty_data = []
        for task in all_tasks:
            for question in task.get("questions", []):
                question_name = question.get("question name", "")
                correct_answer = question.get("correct answer", "")
                
                # Count how many students got it right
                students_correct = 0
                students_wrong = 0
                
                for stat in task.get("stats", []):
                    if stat.get("status") == "completed":
                        # We don't have question-level answers in the current schema
                        # This is a placeholder for future enhancement
                        pass
                
                difficulty_data.append({
                    "question_name": question_name,
                    "difficulty": "Pending"  # Placeholder
                })
        
        col2.info("ℹ️ Question-wise difficulty analysis requires question-level answer tracking")
    
    elif selected_viz == "📈 Performance Correlation Analysis":
        # Check correlation between different tasks
        if len(df["task_name"].unique()) >= 2:
            pivot_corr = df.pivot_table(
                values="percentage",
                index="student_name",
                columns="task_name",
                aggfunc="first",
                fill_value=0
            )
            
            if pivot_corr.shape[1] >= 2:
                corr_matrix = pivot_corr.corr()
                
                fig = px.imshow(
                    corr_matrix,
                    title="Task Performance Correlation Matrix",
                    labels=dict(x="Task", y="Task", color="Correlation"),
                    color_continuous_scale="RdBu",
                    aspect="auto"
                )
                fig.update_layout(height=400)
                col2.plotly_chart(fig, use_container_width=True)
                col2.info("💡 Shows how performance in different tasks correlates")
            else:
                col2.info("Need at least 2 tasks for correlation analysis")
        else:
            col2.info("Need at least 2 tasks for correlation analysis")
    
    elif selected_viz == "📊 Task Difficulty Ranking":
        # Rank tasks by difficulty (lower average = harder)
        task_difficulty = df.groupby("task_name").agg({
            "percentage": "mean",
            "marks": "mean",
            "student_name": "count"
        }).reset_index()
        task_difficulty.columns = ["Task", "Avg Percentage", "Avg Marks", "Students"]
        task_difficulty = task_difficulty.sort_values("Avg Percentage")
        
        fig = px.bar(
            task_difficulty,
            x="Task",
            y="Avg Percentage",
            title="Task Difficulty Ranking (Hardest to Easiest)",
            color="Avg Percentage",
            color_continuous_scale="RdBu",
            text="Avg Percentage",
            hover_data=["Avg Marks", "Students"]
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            xaxis_title="Task",
            yaxis_title="Average Percentage (%)",
            height=400,
            showlegend=False,
            xaxis_tickangle=-45
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Ranks tasks by difficulty based on student performance")
    
    elif selected_viz == "🏅 Medal Standings (Gold/Silver/Bronze)":
        # For each task, assign medals to top 3
        medal_data = []
        for task in all_tasks:
            task_stats = [s for s in task.get("stats", []) if s.get("status") == "completed"]
            task_stats.sort(key=lambda x: x.get("total_marks_obtained", 0), reverse=True)
            
            for i, stat in enumerate(task_stats[:3]):
                medal = "Gold" if i == 0 else "Silver" if i == 1 else "Bronze"
                medal_data.append({
                    "Task": f"{task['task_date']}\n{task['task_name']}",
                    "Student": stat.get("student_name", ""),
                    "Medal": medal,
                    "Marks": stat.get("total_marks_obtained", 0)
                })
        
        if medal_data:
            df_medals = pd.DataFrame(medal_data)
            
            # Count medals per student
            medal_counts = df_medals.groupby(["Student", "Medal"]).size().unstack(fill_value=0)
            
            # Create grouped bar chart
            fig = px.bar(
                medal_counts,
                barmode="group",
                title="Medal Standings",
                labels={"value": "Number of Medals", "Student": "Student", "Medal": "Medal"},
                color_discrete_sequence=["#FFD700", "#C0C0C0", "#CD7F32"]
            )
            fig.update_layout(
                xaxis_title="Student",
                yaxis_title="Number of Medals",
                height=400
            )
            col2.plotly_chart(fig, use_container_width=True)
            col2.info("💡 Shows medal standings (Gold/Silver/Bronze) across all tasks")
        else:
            col2.info("No completed tasks available for medal standings")
    
    elif selected_viz == "📈 Score Distribution Box Plot":
        fig = px.box(
            df,
            x="task_name",
            y="percentage",
            title="Score Distribution by Task",
            labels={"percentage": "Percentage (%)", "task_name": "Task"},
            color="task_name",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(
            xaxis_title="Task",
            yaxis_title="Percentage (%)",
            height=400,
            showlegend=False
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows the distribution of scores for each task (median, quartiles, outliers)")
    
    elif selected_viz == "📊 Student Engagement Metrics":
        # Calculate engagement metrics
        engagement_data = []
        for student in course.get("enrolledStudents", []):
            student_name = student.get("student_name", "")
            student_roll = student.get("student_roll_number", "")
            
            # Count tasks completed
            tasks_completed = len(df[df["student_name"] == student_name])
            total_tasks = len(all_tasks)
            
            # Calculate average score
            student_scores = df[df["student_name"] == student_name]
            avg_score = student_scores["percentage"].mean() if not student_scores.empty else 0
            
            engagement_data.append({
                "Student": student_name,
                "Roll Number": student_roll,
                "Tasks Completed": tasks_completed,
                "Total Tasks": total_tasks,
                "Completion Rate": (tasks_completed / total_tasks * 100) if total_tasks > 0 else 0,
                "Average Score": avg_score
            })
        
        df_engagement = pd.DataFrame(engagement_data)
        df_engagement = df_engagement.sort_values("Completion Rate", ascending=False)
        
        # Create subplot with two charts
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Task Completion Rate by Student", "Average Score by Student"),
            vertical_spacing=0.15
        )
        
        fig.add_trace(
            go.Bar(x=df_engagement["Student"], y=df_engagement["Completion Rate"], name="Completion Rate", marker_color="#4ECDC4"),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=df_engagement["Student"], y=df_engagement["Average Score"], name="Average Score", marker_color="#FF6B6B"),
            row=2, col=1
        )
        
        fig.update_layout(height=500, showlegend=False)
        fig.update_xaxes(title_text="Student", row=2, col=1)
        fig.update_yaxes(title_text="Completion Rate (%)", row=1, col=1)
        fig.update_yaxes(title_text="Average Score (%)", row=2, col=1)
        
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows student engagement metrics - completion rates and average scores")
    
    elif selected_viz == "📈 Performance Improvement Analysis":
        # Calculate improvement between first and last task
        improvement_data = []
        for student in df["student_name"].unique():
            student_data = df[df["student_name"] == student].sort_values("task_date")
            if len(student_data) >= 2:
                first_score = student_data.iloc[0]["percentage"]
                last_score = student_data.iloc[-1]["percentage"]
                improvement = last_score - first_score
                improvement_data.append({
                    "Student": student,
                    "First Score": first_score,
                    "Last Score": last_score,
                    "Improvement": improvement
                })
        
        if improvement_data:
            df_improvement = pd.DataFrame(improvement_data)
            df_improvement = df_improvement.sort_values("Improvement", ascending=False)
            
            fig = px.bar(
                df_improvement,
                x="Student",
                y="Improvement",
                title="Performance Improvement Analysis",
                color="Improvement",
                color_continuous_scale="RdYlGn",
                text="Improvement",
                hover_data=["First Score", "Last Score"]
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(
                xaxis_title="Student",
                yaxis_title="Improvement (Percentage Points)",
                height=400,
                showlegend=False
            )
            col2.plotly_chart(fig, use_container_width=True)
            col2.info("💡 Shows how much each student improved from their first to last task")
        else:
            col2.info("Need students with at least 2 tasks for improvement analysis")
    
    elif selected_viz == "📊 Class Performance Summary":
        # Overall summary statistics
        total_students = len(course.get("enrolledStudents", []))
        total_tasks = len(all_tasks)
        total_completions = len(df)
        avg_score = df["percentage"].mean() if not df.empty else 0
        
        # Create summary cards
        col_summary1, col_summary2, col_summary3, col_summary4 = col2.columns(4)
        col_summary1.metric("👥 Total Students", total_students)
        col_summary2.metric("📝 Total Tasks", total_tasks)
        col_summary3.metric("✅ Total Completions", total_completions)
        col_summary4.metric("📊 Class Average", f"{avg_score:.1f}%")
        
        # Distribution chart
        fig = px.histogram(
            df,
            x="percentage",
            nbins=10,
            title="Class Performance Distribution",
            labels={"percentage": "Percentage Score (%)", "count": "Number of Students"},
            color_discrete_sequence=["#45B7D1"]
        )
        fig.update_layout(
            xaxis_title="Percentage Score (%)",
            yaxis_title="Number of Students",
            height=300,
            showlegend=False
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Comprehensive summary of class performance")
    
    elif selected_viz == "📈 Top 10 Students Performance":
        # Get top 10 students
        top_students = df.groupby("student_name").agg({
            "percentage": "mean",
            "marks": "mean",
            "task_name": "count"
        }).reset_index()
        top_students.columns = ["Student", "Avg Percentage", "Avg Marks", "Tasks Completed"]
        top_students = top_students.sort_values("Avg Percentage", ascending=False).head(10)
        
        fig = px.bar(
            top_students,
            x="Student",
            y="Avg Percentage",
            title="Top 10 Students Performance",
            color="Avg Percentage",
            color_continuous_scale="Viridis",
            text="Avg Percentage",
            hover_data=["Avg Marks", "Tasks Completed"]
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            xaxis_title="Student",
            yaxis_title="Average Percentage (%)",
            height=400,
            showlegend=False
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Detailed performance view of top 10 students")
    
    elif selected_viz == "📊 Task Completion Timeline":
        # Timeline of task completions
        completion_timeline = df.groupby("task_date").size().reset_index()
        completion_timeline.columns = ["Date", "Completions"]
        completion_timeline = completion_timeline.sort_values("Date")
        
        fig = px.line(
            completion_timeline,
            x="Date",
            y="Completions",
            title="Task Completion Timeline",
            markers=True,
            labels={"Completions": "Number of Completions", "Date": "Date"}
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Completions",
            height=400
        )
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows the number of task completions over time")
    
    elif selected_viz == "📈 Performance Variance Analysis":
        # Analyze variance in performance
        variance_data = df.groupby("student_name").agg({
            "percentage": ["mean", "std"]
        }).reset_index()
        variance_data.columns = ["Student", "Avg Percentage", "Std Deviation"]
        variance_data = variance_data.sort_values("Std Deviation", ascending=False)
        
        fig = px.scatter(
            variance_data,
            x="Avg Percentage",
            y="Std Deviation",
            title="Performance Variance Analysis",
            labels={"Avg Percentage": "Average Percentage (%)", "Std Deviation": "Standard Deviation"},
            hover_data=["Student"],
            color="Std Deviation",
            color_continuous_scale="Viridis"
        )
        fig.update_layout(height=400)
        col2.plotly_chart(fig, use_container_width=True)
        col2.info("💡 Shows the relationship between average performance and consistency")
    
    elif selected_viz == "📊 Overall Course Analytics":
        # Comprehensive analytics dashboard
        col2.subheader("📊 Course Analytics Dashboard", divider="green")
        
        # Key metrics
        total_students = len(course.get("enrolledStudents", []))
        total_tasks = len(all_tasks)
        total_completions = len(df)
        avg_score = df["percentage"].mean() if not df.empty else 0
        pass_rate = len(df[df["percentage"] >= 40]) / len(df) * 100 if len(df) > 0 else 0
        
        col_metrics1, col_metrics2, col_metrics3, col_metrics4 = col2.columns(4)
        col_metrics1.metric("👥 Students", total_students)
        col_metrics2.metric("📝 Tasks", total_tasks)
        col_metrics3.metric("✅ Completions", total_completions)
        col_metrics4.metric("📊 Pass Rate", f"{pass_rate:.1f}%")
        
        # Performance distribution
        fig = px.histogram(
            df,
            x="percentage",
            nbins=15,
            title="Performance Distribution",
            labels={"percentage": "Percentage Score (%)", "count": "Number of Students"},
            color_discrete_sequence=["#45B7D1"]
        )
        fig.update_layout(height=300, showlegend=False)
        col2.plotly_chart(fig, use_container_width=True)
        
        # Task completion rates
        completion_data = []
        for task in all_tasks:
            total = len(task.get("stats", []))
            completed = len([s for s in task.get("stats", []) if s.get("status") == "completed"])
            completion_data.append({
                "Task": f"{task['task_date']}\n{task['task_name']}",
                "Completion Rate": (completed / total * 100) if total > 0 else 0
            })
        
        df_completion = pd.DataFrame(completion_data)
        fig2 = px.bar(
            df_completion,
            x="Task",
            y="Completion Rate",
            title="Task Completion Rates",
            color="Completion Rate",
            color_continuous_scale="Viridis",
            text="Completion Rate"
        )
        fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig2.update_layout(height=300, showlegend=False)
        col2.plotly_chart(fig2, use_container_width=True)
        
        col2.info("💡 Comprehensive analytics overview for the entire course")