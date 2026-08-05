import streamlit as st
import pandas as pd
from mongodb import *
from bson import ObjectId

def courses_ui_main():
    tab1,tab2,tab3,tab4 = st.tabs(["Add Courses","Edit Courses","Delete Courses","Stats"])
    with tab1:
        addCourses()
    with tab2:
        editCourses()
    with tab3:
        deleteCourses()
    with tab4:
        pass

def addCourses():
    col1,col2 = st.columns([1,2], border=True, gap="small")
    courseName = col1.text_input("Enter Course Name")
    academicYear = col1.pills("Select The Batch", ["2025-2029","2024-2028","2023-2027"])
    department = col1.radio("Select The Department", ["AI&DS","DS","AI","CSE"], horizontal=True)
    courseCurriculum = col1.file_uploader("Upload The Course Curriculum", ["csv"])
    enrolledStudents = col1.file_uploader("Upload The Students List", ["csv"])
    
    if courseName and academicYear and department and courseCurriculum and enrolledStudents:
        unit_df = pd.read_csv(courseCurriculum)
        unit1_documents = unit_df[unit_df["unit_number"]==1][["topic_name","yt_link","description"]]
        unit2_documents = unit_df[unit_df["unit_number"]==2][["topic_name","yt_link","description"]]
        unit3_documents = unit_df[unit_df["unit_number"]==3][["topic_name","yt_link","description"]]
        unit4_documents = unit_df[unit_df["unit_number"]==4][["topic_name","yt_link","description"]]
        unit5_documents = unit_df[unit_df["unit_number"]==5][["topic_name","yt_link","description"]]
        students_df = pd.read_csv(enrolledStudents)
        
        if all(col in unit_df.columns for col in ["unit_number","topic_name","yt_link","description"]):
            if all(col in students_df.columns for col in ["student_name","student_roll_number","student_gender","student_batch","student_department","student_password"]):
                document = {
                    "courseName": courseName,
                    "academicYear": academicYear,
                    "department": department,
                    "enrolledStudents": students_df[["student_name","student_roll_number","student_gender","student_password"]].to_dict(orient="records"),
                    "unit 1": unit1_documents[["topic_name","yt_link","description"]].to_dict(orient="records"),
                    "unit 2": unit2_documents[["topic_name","yt_link","description"]].to_dict(orient="records"),
                    "unit 3": unit3_documents[["topic_name","yt_link","description"]].to_dict(orient="records"),
                    "unit 4": unit4_documents[["topic_name","yt_link","description"]].to_dict(orient="records"),
                    "unit 5": unit5_documents[["topic_name","yt_link","description"]].to_dict(orient="records"),
                    "materials": [],
                    "tasks": []
                }
                toggle_on = col1.toggle("View The Data")
                if toggle_on:
                    col2.subheader("Primary Details", divider="blue")
                    col2.write(f"Course Name : {courseName}")
                    col2.write(f"Batch : {academicYear}")
                    col2.write(f"Department : {department}")
                    col2.subheader("Enrolled Students", divider="blue")
                    col2.dataframe(students_df)
                    col2.subheader("Course LMS", divider="blue")
                    col2.dataframe(unit_df)
                    submit_button = col2.button("Submit The Course", type="primary", width="stretch")
                    if submit_button:
                        response = st.session_state["collection"].insert_one(document)
                        if response.inserted_id:
                            col2.success("Course Added To Data Base")
                            col2.balloons()
            else:
                col2.info("Kindly Ensure These Are The Column Names Need To Present\nstudent_name,student_roll_number,student_gender,student_batch,student_department,student_password")
        else:
            col2.info("Kindly Ensure These Are The Column Names Need To Present\nunit_number,topic_name,yt_link,description")
    else:
        col2.info("All Fields Are Required")

def editCourses():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Select course to edit
    batch = col1.pills("Select Batch", ["2025-2029","2024-2028","2023-2027"], key="unique-one")
    department = col1.segmented_control("Select Department", ["AI&DS","DS","AI","CSE"], key="one")
    edit_toggle = col1.toggle("Edit Course", value=False)
    
    if edit_toggle and batch and department:
        # Find all courses matching the batch and department
        courses_cursor = st.session_state["collection"].find({
            "academicYear": batch,
            "department": department
        }, {"_id": 1, "courseName": 1})
        
        course_list = list(courses_cursor)
        
        if course_list:
            # Create a list of course names for selection
            course_names = [course["courseName"] for course in course_list]
            selected_course_name = col1.segmented_control(
                "Select the course you wanted to edit",
                course_names
            )
            
            # Find the full course document for the selected course name
            if selected_course_name:
                course = st.session_state["collection"].find_one({
                    "academicYear": batch,
                    "department": department,
                    "courseName": selected_course_name
                })
                
                if course:
                    col2.success(f"Editing Course: {course['courseName']}")
                    
                    # Select what to edit
                    edit_option = col2.radio(
                        "Select Field to Edit",
                        ["Course Name", "Academic Year", "Department", "Unit Content", "Student Details"],
                        horizontal=True
                    )
                    
                    if edit_option == "Course Name":
                        new_course_name = col2.text_input("New Course Name", value=course['courseName'])
                        if col2.button("Update Course Name", type="primary"):
                            # Check if course name already exists for this batch and department
                            existing = st.session_state["collection"].find_one({
                                "academicYear": batch,
                                "department": department,
                                "courseName": new_course_name
                            })
                            if existing and existing['_id'] != course['_id']:
                                col2.error("A course with this name already exists in the selected batch and department!")
                            else:
                                result = st.session_state["collection"].update_one(
                                    {"_id": course['_id']},
                                    {"$set": {"courseName": new_course_name}}
                                )
                                if result.modified_count > 0:
                                    col2.success("Course Name Updated Successfully!")
                                    st.rerun()
                    
                    elif edit_option == "Academic Year":
                        new_batch = col2.pills("Select New Batch", ["2025-2029","2024-2028","2023-2027"])
                        if col2.button("Update Academic Year", type="primary"):
                            # Check if course exists with new batch
                            existing = st.session_state["collection"].find_one({
                                "academicYear": new_batch,
                                "department": course['department'],
                                "courseName": course['courseName']
                            })
                            if existing and existing['_id'] != course['_id']:
                                col2.error("This course already exists in the selected batch!")
                            else:
                                result = st.session_state["collection"].update_one(
                                    {"_id": course['_id']},
                                    {"$set": {"academicYear": new_batch}}
                                )
                                if result.modified_count > 0:
                                    col2.success("Academic Year Updated Successfully!")
                                    st.rerun()
                    
                    elif edit_option == "Department":
                        new_department = col2.radio("Select New Department", ["AI&DS","DS","AI","CSE"], horizontal=True)
                        if col2.button("Update Department", type="primary"):
                            # Check if course exists with new department
                            existing = st.session_state["collection"].find_one({
                                "academicYear": course['academicYear'],
                                "department": new_department,
                                "courseName": course['courseName']
                            })
                            if existing and existing['_id'] != course['_id']:
                                col2.error("This course already exists in the selected department!")
                            else:
                                result = st.session_state["collection"].update_one(
                                    {"_id": course['_id']},
                                    {"$set": {"department": new_department}}
                                )
                                if result.modified_count > 0:
                                    col2.success("Department Updated Successfully!")
                                    st.rerun()
                    
                    elif edit_option == "Unit Content":
                        # Select unit
                        unit_options = ["unit 1", "unit 2", "unit 3", "unit 4", "unit 5"]
                        selected_unit = col2.selectbox("Select Unit", unit_options)
                        
                        # Get current unit data
                        current_unit_data = course.get(selected_unit, [])
                        
                        if current_unit_data:
                            # Create a dataframe for editing
                            unit_df = pd.DataFrame(current_unit_data)
                            col2.dataframe(unit_df)
                            
                            # Select topic to edit
                            topic_names = [topic['topic_name'] for topic in current_unit_data]
                            selected_topic = col2.selectbox("Select Topic to Edit", topic_names)
                            
                            if selected_topic:
                                # Find the topic
                                topic_index = next(i for i, t in enumerate(current_unit_data) if t['topic_name'] == selected_topic)
                                topic_data = current_unit_data[topic_index]
                                
                                # Edit fields
                                new_topic_name = col2.text_input("Topic Name", value=topic_data['topic_name'])
                                new_yt_link = col2.text_input("YouTube Link", value=topic_data['yt_link'])
                                new_description = col2.text_area("Description", value=topic_data['description'])
                                
                                if col2.button("Update Topic", type="primary"):
                                    # Update the topic in the unit
                                    current_unit_data[topic_index] = {
                                        "topic_name": new_topic_name,
                                        "yt_link": new_yt_link,
                                        "description": new_description
                                    }
                                    
                                    result = st.session_state["collection"].update_one(
                                        {"_id": course['_id']},
                                        {"$set": {selected_unit: current_unit_data}}
                                    )
                                    if result.modified_count > 0:
                                        col2.success("Topic Updated Successfully!")
                                        st.rerun()
                        else:
                            col2.info(f"No topics found in {selected_unit}")
                    
                    elif edit_option == "Student Details":
                        # Display current students
                        students = course.get('enrolledStudents', [])
                        
                        if students:
                            students_df = pd.DataFrame(students)
                            col2.dataframe(students_df)
                            
                            # Select student to edit
                            student_names = [s['student_name'] for s in students]
                            selected_student = col2.selectbox("Select Student to Edit", student_names)
                            
                            if selected_student:
                                student_index = next(i for i, s in enumerate(students) if s['student_name'] == selected_student)
                                student_data = students[student_index]
                                
                                # Edit student fields
                                col2.subheader("Edit Student Details")
                                new_name = col2.text_input("Student Name", value=student_data['student_name'])
                                new_roll = col2.text_input("Roll Number", value=student_data['student_roll_number'])
                                new_gender = col2.selectbox("Gender", ["Male", "Female", "Other"], 
                                                           index=["Male", "Female", "Other"].index(student_data.get('student_gender', 'Male')))
                                new_password = col2.text_input("Password", value=student_data.get('student_password', ''), type="password")
                                
                                if col2.button("Update Student", type="primary"):
                                    students[student_index] = {
                                        "student_name": new_name,
                                        "student_roll_number": new_roll,
                                        "student_gender": new_gender,
                                        "student_password": new_password
                                    }
                                    
                                    result = st.session_state["collection"].update_one(
                                        {"_id": course['_id']},
                                        {"$set": {"enrolledStudents": students}}
                                    )
                                    if result.modified_count > 0:
                                        col2.success("Student Details Updated Successfully!")
                                        st.rerun()
                        else:
                            col2.info("No students enrolled in this course")
                else:
                    col2.warning("Selected course not found!")
        else:
            col2.warning("No courses found with the selected batch and department")

def deleteCourses():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Select course to delete
    batch = col1.pills("Select Batch", ["2025-2029","2024-2028","2023-2027"], key="delete-batch")
    department = col1.segmented_control("Select Department", ["AI&DS","DS","AI","CSE"], key="delete-dept")
    delete_toggle = col1.toggle("Delete Course", value=False)
    
    if delete_toggle and batch and department:
        # Find all courses matching the batch and department
        courses_cursor = st.session_state["collection"].find({
            "academicYear": batch,
            "department": department
        }, {"_id": 1, "courseName": 1})
        
        course_list = list(courses_cursor)
        
        if course_list:
            # Create a list of course names for selection
            course_names = [course["courseName"] for course in course_list]
            selected_course_name = col1.segmented_control(
                "Select the course you want to delete",
                course_names,
                key="delete-course-select"
            )
            
            # Find the full course document for the selected course name
            if selected_course_name:
                course = st.session_state["collection"].find_one({
                    "academicYear": batch,
                    "department": department,
                    "courseName": selected_course_name
                })
                
                if course:
                    col2.success(f"Course Found: {course['courseName']}")
                    
                    # Delete options
                    delete_option = col2.radio(
                        "Select Delete Option",
                        ["Delete Entire Course", "Delete Unit Topic", "Delete Student"],
                        horizontal=True
                    )
                    
                    if delete_option == "Delete Entire Course":
                        col2.warning(f"⚠️ Are you sure you want to delete the entire course: {course['courseName']}?")
                        confirm_text = col2.text_input("Type 'DELETE' to confirm")
                        if col2.button("Delete Entire Course", type="primary", use_container_width=True):
                            if confirm_text == "DELETE":
                                result = st.session_state["collection"].delete_one({"_id": course['_id']})
                                if result.deleted_count > 0:
                                    col2.success("Course Deleted Successfully!")
                                    st.rerun()
                            else:
                                col2.error("Please type 'DELETE' to confirm")
                    
                    elif delete_option == "Delete Unit Topic":
                        unit_options = ["unit 1", "unit 2", "unit 3", "unit 4", "unit 5"]
                        selected_unit = col2.selectbox("Select Unit", unit_options)
                        
                        # Get current unit data
                        current_unit_data = course.get(selected_unit, [])
                        
                        if current_unit_data:
                            topic_names = [topic['topic_name'] for topic in current_unit_data]
                            selected_topic = col2.selectbox("Select Topic to Delete", topic_names)
                            
                            if selected_topic:
                                col2.warning(f"Are you sure you want to delete topic: '{selected_topic}' from {selected_unit}?")
                                if col2.button("Delete Topic", type="primary", use_container_width=True):
                                    # Remove the topic
                                    updated_unit_data = [t for t in current_unit_data if t['topic_name'] != selected_topic]
                                    
                                    result = st.session_state["collection"].update_one(
                                        {"_id": course['_id']},
                                        {"$set": {selected_unit: updated_unit_data}}
                                    )
                                    if result.modified_count > 0:
                                        col2.success(f"Topic '{selected_topic}' Deleted Successfully!")
                                        st.rerun()
                        else:
                            col2.info(f"No topics found in {selected_unit}")
                    
                    elif delete_option == "Delete Student":
                        students = course.get('enrolledStudents', [])
                        
                        if students:
                            student_names = [s['student_name'] for s in students]
                            selected_student = col2.selectbox("Select Student to Delete", student_names)
                            
                            if selected_student:
                                col2.warning(f"Are you sure you want to delete student: '{selected_student}' from the course?")
                                if col2.button("Delete Student", type="primary", use_container_width=True):
                                    # Remove the student
                                    updated_students = [s for s in students if s['student_name'] != selected_student]
                                    
                                    result = st.session_state["collection"].update_one(
                                        {"_id": course['_id']},
                                        {"$set": {"enrolledStudents": updated_students}}
                                    )
                                    if result.modified_count > 0:
                                        col2.success(f"Student '{selected_student}' Deleted Successfully!")
                                        st.rerun()
                        else:
                            col2.info("No students enrolled in this course")
                else:
                    col2.warning("Selected course not found!")
        else:
            col2.warning("No courses found with the selected batch and department")