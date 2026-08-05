import streamlit as st
import os
from streamlit_pdf_viewer import pdf_viewer
from mongodb1 import *  # Ensure this imports your MongoDB connection

def main_layout():
    """
    Main layout for the Study/Materials section
    Displays PDF materials organized by category
    """
    st.subheader("📚 Study Materials", divider="orange", text_alignment="center")
    
    # Check if materials exist in session state
    if "materials" not in st.session_state or not st.session_state["materials"]:
        st.info("ℹ️ No materials available for this course")
        return
    
    # Get all materials from session state
    materials_data = st.session_state["materials"]
    
    # Extract unique categories
    categories = list(set([material["category"] for material in materials_data]))
    
    if not categories:
        st.info("ℹ️ No categories found in materials")
        return
    
    # Create two columns with 1:2 ratio
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Display categories as pills
    with col1:
        st.subheader("📁 Categories", divider="blue")
        selected_category = st.pills(
            "Select Category",
            options=categories,
            selection_mode="single",
            key="materials_category_pills"
        )
    
    # Column 2: Display materials based on selected category
    with col2:
        if selected_category:
            # Filter materials by selected category
            category_materials = [
                material for material in materials_data 
                if material["category"] == selected_category
            ]
            
            if category_materials:
                st.subheader(f"📄 {selected_category} Materials", divider="blue")
                
                # Create a list of material options for selectbox
                material_options = []
                material_map = {}  # Map display name to material data
                
                for material in category_materials:
                    # Get the materials string and split by comma
                    materials_list = [m.strip() for m in material["materials"].split(",") if m.strip()]
                    root_path = material["root_path"]
                    
                    for material_name in materials_list:
                        display_name = material_name
                        # Store full path and material info
                        material_map[display_name] = {
                            "root_path": root_path,
                            "material_name": material_name,
                            "full_path": os.path.join(root_path, material_name)
                        }
                        material_options.append(display_name)
                
                if material_options:
                    # Display selectbox with material options
                    selected_material = st.selectbox(
                        "Select Material to View",
                        options=material_options,
                        key="materials_selectbox"
                    )
                    
                    if selected_material and selected_material in material_map:
                        material_info = material_map[selected_material]
                        full_path = material_info["full_path"]
                        
                        # Display the full path
                        st.caption(f"📂 Path: {full_path}")
                        
                        # Check if file exists
                        if os.path.exists(full_path):
                            try:
                                # Display PDF using streamlit-pdf-viewer
                                with open(full_path, 'rb') as f:
                                    pdf_bytes = f.read()
                                
                                # Show PDF viewer
                                st.info("📄 PDF Viewer")
                                pdf_viewer(
                                    input=pdf_bytes,
                                    width=700,
                                    height=600,
                                    key=f"pdf_viewer_{selected_material.replace(' ', '_')}"
                                )
                                
                                # Add download button as well
                                with open(full_path, 'rb') as f:
                                    st.download_button(
                                        label="📥 Download PDF",
                                        data=f.read(),
                                        file_name=selected_material,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                                    
                            except Exception as e:
                                st.error(f"❌ Error displaying PDF: {str(e)}")
                                st.info("Please check if the PDF file is valid and not corrupted.")
                                
                                # Fallback: Provide download option
                                try:
                                    with open(full_path, 'rb') as f:
                                        st.download_button(
                                            label="📥 Download PDF",
                                            data=f.read(),
                                            file_name=selected_material,
                                            mime="application/pdf",
                                            use_container_width=True
                                        )
                                except Exception as download_error:
                                    st.error(f"❌ Error downloading file: {str(download_error)}")
                        else:
                            st.error(f"❌ File not found at: {full_path}")
                            st.info("Please ensure the file exists at the specified path.")
                            
                            # Try to show the file if it exists in a different location
                            st.info("💡 Tip: Check if the root path is correct and the file name matches exactly.")
                else:
                    st.info("ℹ️ No materials found in this category")
            else:
                st.info("ℹ️ No materials found for the selected category")
        else:
            st.info("👈 Please select a category from the left to view materials")
            
            # Show a preview of available categories
            st.subheader("📊 Available Categories", divider="blue")
            for cat in categories:
                material_count = sum(1 for m in materials_data if m["category"] == cat)
                st.write(f"- **{cat}**: {material_count} material(s)")

# Alternative function name for compatibility with mainFile.py
def main1():
    """
    Wrapper function for the materials section
    Called from mainFile.py when 'Study' is selected
    """
    main_layout()

# If you want to test this file independently
if __name__ == "__main__":
    main_layout()