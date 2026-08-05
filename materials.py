import streamlit as st
from mongodb import *
from bson import ObjectId
import base64
import os
from streamlit_pdf_viewer import pdf_viewer

def main1():
    tab1, tab2, tab3, tab4 = st.tabs(["Add Materials", "Edit Materials", "Delete Materials", "View Materials"])
    
    with tab1:
        add_materials()
    with tab2:
        edit_materials()
    with tab3:
        delete_materials()
    with tab4:
        view_materials()

def add_materials():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Selection filters
    batch = col1.pills("Select Batch", ["2025-2029", "2024-2028", "2023-2027"], key="add_batch")
    department = col1.segmented_control("Select Department", ["AI&DS", "DS", "AI", "CSE"], key="add_dept")
    
    if batch and department:
        # Fetch unique course names
        courses_cursor = st.session_state["collection"].distinct(
            "courseName",
            {"academicYear": batch, "department": department}
        )
        
        if courses_cursor:
            subject = col1.radio(
                "Select Course",
                courses_cursor,
                horizontal=True,
                key="add_subject"
            )
            
            continue_toggle = col1.toggle("Continue to Add Materials", key="add_continue")
            
            if continue_toggle and subject:
                # Column 2: Add materials form
                col2.subheader(f"Add Materials for: {subject}", divider="blue")
                
                category = col2.segmented_control(
                    "Select Category",
                    ["Unit 1", "Unit 2", "Unit 3", "Unit 4", "Unit 5", "Textbook", "Others"],
                    key="add_category"
                )
                
                root_path = col2.text_input("Enter Root Path", key="add_root_path")
                materials = col2.text_area(
                    "Enter Materials (comma separated)",
                    placeholder="e.g., material1.pdf, material2.pdf, material3.pdf",
                    key="add_materials"
                )
                
                add_button = col2.button("Add Materials", type="primary", use_container_width=True, key="add_button")
                
                if add_button:
                    if not root_path or not materials:
                        col2.error("Please fill in all fields")
                    else:
                        # Create material document
                        material_doc = {
                            "category": category,
                            "root_path": root_path,
                            "materials": materials  # Store as comma-separated string
                        }
                        
                        # Update the course document - push to materials array
                        result = st.session_state["collection"].update_one(
                            {
                                "academicYear": batch,
                                "department": department,
                                "courseName": subject
                            },
                            {
                                "$push": {"materials": material_doc}
                            }
                        )
                        
                        if result.modified_count > 0:
                            col2.success("✅ Materials added successfully!")
                            col2.balloons()
                        else:
                            col2.error("Failed to add materials. Please try again.")
        else:
            col1.warning("No courses found for the selected batch and department")

def edit_materials():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Selection filters
    batch = col1.pills("Select Batch", ["2025-2029", "2024-2028", "2023-2027"], key="edit_batch")
    department = col1.segmented_control("Select Department", ["AI&DS", "DS", "AI", "CSE"], key="edit_dept")
    
    if batch and department:
        # Fetch unique course names
        courses_cursor = st.session_state["collection"].distinct(
            "courseName",
            {"academicYear": batch, "department": department}
        )
        
        if courses_cursor:
            subject = col1.radio(
                "Select Course",
                courses_cursor,
                horizontal=True,
                key="edit_subject"
            )
            
            if subject:
                # Fetch the course document
                course = st.session_state["collection"].find_one({
                    "academicYear": batch,
                    "department": department,
                    "courseName": subject
                })
                
                if course and "materials" in course and course["materials"]:
                    # Column 2: Edit materials
                    col2.subheader(f"Edit Materials for: {subject}", divider="blue")
                    
                    # Get unique categories from existing materials
                    existing_categories = list(set([m["category"] for m in course["materials"]]))
                    
                    if existing_categories:
                        category = col2.selectbox(
                            "Select Category to Edit",
                            existing_categories,
                            key="edit_category"
                        )
                        
                        # Find materials with selected category
                        category_materials = [m for m in course["materials"] if m["category"] == category]
                        
                        if category_materials:
                            # Create options for root path selection
                            root_path_options = [m["root_path"] for m in category_materials]
                            selected_root_path = col2.selectbox(
                                "Select Root Path to Edit",
                                root_path_options,
                                key="edit_root_path"
                            )
                            
                            # Find the specific material document
                            selected_material = next(
                                (m for m in category_materials if m["root_path"] == selected_root_path),
                                None
                            )
                            
                            if selected_material:
                                # Display current values and allow editing
                                st.divider()
                                
                                new_category = col2.text_input(
                                    "Category",
                                    value=selected_material["category"],
                                    key="edit_new_category"
                                )
                                
                                new_root_path = col2.text_input(
                                    "Root Path",
                                    value=selected_material["root_path"],
                                    key="edit_new_root_path"
                                )
                                
                                new_materials = col2.text_area(
                                    "Materials (comma separated)",
                                    value=selected_material["materials"],
                                    key="edit_new_materials"
                                )
                                
                                update_button = col2.button(
                                    "Update Materials",
                                    type="primary",
                                    use_container_width=True,
                                    key="edit_update_button"
                                )
                                
                                if update_button:
                                    if not new_category or not new_root_path or not new_materials:
                                        col2.error("Please fill in all fields")
                                    else:
                                        # Update the specific material in the array
                                        result = st.session_state["collection"].update_one(
                                            {
                                                "academicYear": batch,
                                                "department": department,
                                                "courseName": subject,
                                                "materials.category": category,
                                                "materials.root_path": selected_root_path
                                            },
                                            {
                                                "$set": {
                                                    "materials.$.category": new_category,
                                                    "materials.$.root_path": new_root_path,
                                                    "materials.$.materials": new_materials
                                                }
                                            }
                                        )
                                        
                                        if result.modified_count > 0:
                                            col2.success("✅ Materials updated successfully!")
                                            st.rerun()
                                        else:
                                            col2.error("Failed to update materials. Please try again.")
                            else:
                                col2.warning("Selected material not found")
                        else:
                            col2.info(f"No materials found for category: {category}")
                    else:
                        col2.info("No categories found in materials")
                else:
                    col2.info("No materials found for this course")
        else:
            col1.warning("No courses found for the selected batch and department")

def delete_materials():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Selection filters
    batch = col1.pills("Select Batch", ["2025-2029", "2024-2028", "2023-2027"], key="delete_batch")
    department = col1.segmented_control("Select Department", ["AI&DS", "DS", "AI", "CSE"], key="delete_dept")
    
    if batch and department:
        # Fetch unique course names
        courses_cursor = st.session_state["collection"].distinct(
            "courseName",
            {"academicYear": batch, "department": department}
        )
        
        if courses_cursor:
            subject = col1.radio(
                "Select Course",
                courses_cursor,
                horizontal=True,
                key="delete_subject"
            )
            
            if subject:
                # Fetch the course document
                course = st.session_state["collection"].find_one({
                    "academicYear": batch,
                    "department": department,
                    "courseName": subject
                })
                
                if course and "materials" in course and course["materials"]:
                    # Column 2: Delete materials
                    col2.subheader(f"Delete Materials for: {subject}", divider="blue")
                    
                    # Get unique categories
                    categories = list(set([m["category"] for m in course["materials"]]))
                    
                    if categories:
                        category = col2.segmented_control(
                            "Select Category to Delete",
                            categories,
                            key="delete_category"
                        )
                        
                        if category:
                            # Get materials for selected category
                            category_materials = [m for m in course["materials"] if m["category"] == category]
                            
                            if category_materials:
                                # Display materials to delete
                                col2.warning(f"⚠️ You are about to delete materials from category: **{category}**")
                                
                                # Show all materials in this category
                                col2.write("**Materials in this category:**")
                                for material in category_materials:
                                    col2.write(f"- {material['root_path']}")
                                
                                # Select root path to delete (optional - user can delete entire category or specific root path)
                                delete_option = col2.radio(
                                    "Delete Option",
                                    ["Delete Entire Category", "Delete Specific Root Path"],
                                    key="delete_option"
                                )
                                
                                if delete_option == "Delete Specific Root Path":
                                    root_paths = [m["root_path"] for m in category_materials]
                                    selected_root_path = col2.selectbox(
                                        "Select Root Path to Delete",
                                        root_paths,
                                        key="delete_root_path"
                                    )
                                    
                                    if selected_root_path:
                                        confirm_delete = col2.text_input(
                                            f"Type 'DELETE' to confirm deleting {selected_root_path}",
                                            key="delete_confirm_specific"
                                        )
                                        
                                        if col2.button("Delete Materials", type="primary", use_container_width=True, key="delete_button_specific"):
                                            if confirm_delete == "DELETE":
                                                # Remove specific material from the array
                                                result = st.session_state["collection"].update_one(
                                                    {
                                                        "academicYear": batch,
                                                        "department": department,
                                                        "courseName": subject
                                                    },
                                                    {
                                                        "$pull": {
                                                            "materials": {
                                                                "category": category,
                                                                "root_path": selected_root_path
                                                            }
                                                        }
                                                    }
                                                )
                                                
                                                if result.modified_count > 0:
                                                    col2.success("✅ Materials deleted successfully!")
                                                    st.rerun()
                                                else:
                                                    col2.error("Failed to delete materials. Please try again.")
                                            else:
                                                col2.error("Please type 'DELETE' to confirm")
                                
                                else:  # Delete Entire Category
                                    confirm_delete = col2.text_input(
                                        f"Type 'DELETE' to confirm deleting entire category: {category}",
                                        key="delete_confirm_category"
                                    )
                                    
                                    if col2.button("Delete Entire Category", type="primary", use_container_width=True, key="delete_button_category"):
                                        if confirm_delete == "DELETE":
                                            # Remove all materials in this category
                                            result = st.session_state["collection"].update_one(
                                                {
                                                    "academicYear": batch,
                                                    "department": department,
                                                    "courseName": subject
                                                },
                                                {
                                                    "$pull": {
                                                        "materials": {
                                                            "category": category
                                                        }
                                                    }
                                                }
                                            )
                                            
                                            if result.modified_count > 0:
                                                col2.success("✅ Entire category deleted successfully!")
                                                st.rerun()
                                            else:
                                                col2.error("Failed to delete category. Please try again.")
                                        else:
                                            col2.error("Please type 'DELETE' to confirm")
                            else:
                                col2.info(f"No materials found for category: {category}")
                    else:
                        col2.info("No categories found in materials")
                else:
                    col2.info("No materials found for this course")
        else:
            col1.warning("No courses found for the selected batch and department")

def view_materials():
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Selection filters
    batch = col1.pills("Select Batch", ["2025-2029", "2024-2028", "2023-2027"], key="view_batch")
    department = col1.segmented_control("Select Department", ["AI&DS", "DS", "AI", "CSE"], key="view_dept")
    
    if batch and department:
        # Fetch unique course names
        courses_cursor = st.session_state["collection"].distinct(
            "courseName",
            {"academicYear": batch, "department": department}
        )
        
        if courses_cursor:
            subject = col1.radio(
                "Select Course",
                courses_cursor,
                horizontal=True,
                key="view_subject"
            )
            
            if subject:
                # Fetch the course document
                course = st.session_state["collection"].find_one({
                    "academicYear": batch,
                    "department": department,
                    "courseName": subject
                })
                
                if course and "materials" in course and course["materials"]:
                    # Column 2: View materials
                    col2.subheader(f"View Materials for: {subject}", divider="blue")
                    
                    # Get unique categories
                    categories = list(set([m["category"] for m in course["materials"]]))
                    
                    if categories:
                        # Display categories as segmented control
                        category = col2.segmented_control(
                            "Select Category",
                            categories,
                            key="view_category"
                        )
                        
                        if category:
                            # Get materials for selected category
                            category_materials = [m for m in course["materials"] if m["category"] == category]
                            
                            if category_materials:
                                # Display root path selection
                                root_paths = [m["root_path"] for m in category_materials]
                                selected_root_path = col2.selectbox(
                                    "Select Root Path",
                                    root_paths,
                                    key="view_root_path"
                                )
                                
                                if selected_root_path:
                                    # Find the selected material
                                    selected_material = next(
                                        (m for m in category_materials if m["root_path"] == selected_root_path),
                                        None
                                    )
                                    
                                    if selected_material:
                                        # Display root path
                                        col2.write(f"**Root Path:** {selected_material['root_path']}")
                                        
                                        # Split materials and display in select box
                                        materials_list = [x.strip() for x in selected_material["materials"].split(",") if x.strip()]
                                        
                                        if materials_list:
                                            selected_material_name = col2.selectbox(
                                                "Select Material to View",
                                                materials_list,
                                                key="view_material_select"
                                            )
                                            
                                            if selected_material_name:
                                                # Construct full path
                                                full_path = selected_material["root_path"] + selected_material_name
                                                
                                                # Display the material
                                                try:
                                                    col2.write(f"**Full Path:** {full_path}")
                                                    
                                                    # Check if file exists
                                                    if not os.path.exists(full_path):
                                                        col2.error(f"❌ File not found at: {full_path}")
                                                        col2.info("Please check if the root path is correct and the file exists.")
                                                        return
                                                    
                                                    # Get file extension
                                                    file_extension = selected_material_name.split('.')[-1].lower()
                                                    
                                                    # Handle different file types
                                                    if file_extension == 'pdf':
                                                        col2.info("📄 PDF Viewer")
                                                        try:
                                                            # Use streamlit-pdf-viewer
                                                            with open(full_path, 'rb') as f:
                                                                pdf_bytes = f.read()
                                                                with col2:
                                                                    pdf_viewer(input=pdf_bytes, width=700, height=600)
                                                        except Exception as e:
                                                            col2.error(f"Error displaying PDF: {str(e)}")
                                                            # Fallback: Provide download button only
                                                            with open(full_path, 'rb') as f:
                                                                col2.download_button(
                                                                    label="📥 Download PDF",
                                                                    data=f.read(),
                                                                    file_name=selected_material_name,
                                                                    mime="application/pdf",
                                                                    use_container_width=True
                                                                )
                                                            
                                                    
                                                    else:
                                                        # Default: Provide download option
                                                        col2.warning(f"Preview not available for .{file_extension} files")
                                                        with open(full_path, 'rb') as f:
                                                            col2.download_button(
                                                                label=f"📥 Download {selected_material_name}",
                                                                data=f.read(),
                                                                file_name=selected_material_name,
                                                                use_container_width=True
                                                            )
                                                        
                                                except Exception as e:
                                                    col2.error(f"Error displaying material: {str(e)}")
                                        else:
                                            col2.info("No materials found in this category/root path")
                            else:
                                col2.info(f"No materials found for category: {category}")
                    else:
                        col2.info("No categories found in materials")
                else:
                    col2.info("No materials found for this course")
        else:
            col1.warning("No courses found for the selected batch and department")
