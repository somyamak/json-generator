import streamlit as st
import json
from copy import deepcopy
import uuid

# Configure Streamlit page
st.set_page_config(
    page_title="JSON Generator - Health Score API",
    page_icon="🧬",
    layout="wide"
)

# Template JSON structure - Replace this with your actual template
template_json = {
    "patient_id": "",
    "age": None,
    "gender": "",
    "weight": None,
    "height": None,
    "blood_pressure_systolic": None,
    "blood_pressure_diastolic": None,
    "heart_rate": None,
    "cholesterol_total": None,
    "cholesterol_hdl": None,
    "cholesterol_ldl": None,
    "glucose_level": None,
    "bmi": None,
    "smoking_status": "",
    "exercise_frequency": None,
    "medical_history": [],
    "medications": [],
    "lab_results": {
        "hemoglobin": None,
        "white_blood_cells": None,
        "platelets": None,
        "creatinine": None
    },
    "risk_factors": []
}

def initialize_session_state():
    """Initialize session state variables"""
    if 'json_blocks' not in st.session_state:
        st.session_state.json_blocks = {}
    if 'block_counter' not in st.session_state:
        st.session_state.block_counter = 0
    if 'generated_output' not in st.session_state:
        st.session_state.generated_output = ""

def create_empty_template():
    """Create a template with all values set to empty/null"""
    def make_empty(obj):
        if isinstance(obj, dict):
            return {k: make_empty(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return []
        elif isinstance(obj, str):
            return ""
        else:
            return None
    
    return make_empty(template_json)

def add_new_json_block():
    """Add a new JSON block to session state"""
    block_id = str(uuid.uuid4())
    st.session_state.json_blocks[block_id] = {
        'data': create_empty_template(),
        'counter': st.session_state.block_counter
    }
    st.session_state.block_counter += 1
    return block_id

def remove_json_block(block_id):
    """Remove a JSON block from session state"""
    if block_id in st.session_state.json_blocks:
        del st.session_state.json_blocks[block_id]

def clean_json_data(data):
    """Remove empty/null values from JSON data"""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                cleaned_value = clean_json_data(value)
                if cleaned_value or (isinstance(cleaned_value, list) and len(cleaned_value) == 0):
                    # Keep empty lists if they were explicitly set
                    if not (isinstance(cleaned_value, dict) and len(cleaned_value) == 0):
                        cleaned[key] = cleaned_value
            elif value is not None and value != "":
                cleaned[key] = value
        return cleaned
    elif isinstance(data, list):
        cleaned_list = []
        for item in data:
            if isinstance(item, (dict, list)):
                cleaned_item = clean_json_data(item)
                if cleaned_item or (isinstance(cleaned_item, list) and len(cleaned_item) == 0):
                    cleaned_list.append(cleaned_item)
            elif item is not None and item != "":
                cleaned_list.append(item)
        return cleaned_list
    else:
        return data

def generate_final_output():
    """Generate the final JSON output from all blocks"""
    all_blocks = []
    for block_data in st.session_state.json_blocks.values():
        clean_data = clean_json_data(block_data['data'])
        if clean_data:  # Only include non-empty blocks
            all_blocks.append(clean_data)
    
    if all_blocks:
        return json.dumps(all_blocks, indent=2)
    else:
        return "[]"

def render_json_editor(block_id, block_data):
    """Render JSON editor for a single block"""
    st.markdown(f"### 📋 JSON Block #{block_data['counter'] + 1}")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Convert current data to JSON string for editing
        json_str = json.dumps(block_data['data'], indent=2)
        
        # Text area for JSON editing
        edited_json_str = st.text_area(
            "Edit JSON:",
            value=json_str,
            height=300,
            key=f"json_editor_{block_id}",
            help="Edit the JSON directly. Use null for null values, [] for empty arrays."
        )
        
        # Try to parse the edited JSON
        try:
            edited_data = json.loads(edited_json_str)
            st.session_state.json_blocks[block_id]['data'] = edited_data
            st.success("✅ Valid JSON")
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {str(e)}")
    
    with col2:
        st.markdown("#### Actions")
        
        if st.button("🗑️ Delete Block", key=f"delete_{block_id}", type="secondary"):
            remove_json_block(block_id)
            st.rerun()
        
        st.markdown("---")
        
        # Preview cleaned data for this block
        clean_data = clean_json_data(block_data['data'])
        if clean_data:
            st.markdown("**Preview (cleaned):**")
            st.json(clean_data)
        else:
            st.info("Block is empty")

def main():
    """Main application function"""
    initialize_session_state()
    
    # Header
    st.title("🧬 JSON Generator - Health Score API")
    st.markdown("Generate and manage multiple JSON test cases for your Health Score API")
    
    # Control panel
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        if st.button("➕ Add New JSON Block", type="primary"):
            add_new_json_block()
            st.rerun()
    
    with col2:
        total_blocks = len(st.session_state.json_blocks)
        st.metric("Total Blocks", total_blocks)
    
    with col3:
        if st.button("🧹 Clear All Blocks", type="secondary"):
            st.session_state.json_blocks = {}
            st.session_state.block_counter = 0
            st.session_state.generated_output = ""
            st.rerun()
    
    st.divider()
    
    # Generate Output Section
    st.markdown("### 🎯 Generate Final Output")
    col1, col2 = st.columns([2, 2])
    
    with col1:
        if st.button("🚀 Generate JSON Output", type="primary"):
            st.session_state.generated_output = generate_final_output()
            st.success("✅ JSON output generated!")
    
    with col2:
        valid_blocks = sum(1 for block_data in st.session_state.json_blocks.values() 
                          if clean_json_data(block_data['data']))
        st.metric("Valid Blocks", valid_blocks)
    
    # Display generated output
    if st.session_state.generated_output:
        st.markdown("#### 📄 Generated JSON Array:")
        st.code(st.session_state.generated_output, language="json")
        
        # Download button
        st.download_button(
            label="💾 Download JSON File",
            data=st.session_state.generated_output,
            file_name="health_score_test_cases.json",
            mime="application/json",
            type="primary"
        )
        
        # Copy instructions
        st.info("💡 **To copy:** Click in the code box above and use Ctrl+A (select all) then Ctrl+C (copy)")
    
    st.divider()
    
    # Show template structure
    with st.expander("📖 View Template Structure", expanded=False):
        st.json(template_json)
        st.markdown("**Note:** Replace the `template_json` variable in the code with your actual JSON structure.")
    
    # Display JSON blocks
    if not st.session_state.json_blocks:
        st.info("👆 Click 'Add New JSON Block' to start creating test cases")
        
        # Auto-add first block
        if st.button("🚀 Start with First Block"):
            add_new_json_block()
            st.rerun()
    else:
        st.markdown("### 📝 JSON Blocks")
        
        # Sort blocks by counter for consistent display order
        sorted_blocks = sorted(
            st.session_state.json_blocks.items(), 
            key=lambda x: x[1]['counter']
        )
        
        for block_id, block_data in sorted_blocks:
            with st.container():
                render_json_editor(block_id, block_data)
                st.divider()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "💡 **Usage Tips:**\n"
        "- Use `null` for null values (not `None`)\n"
        "- Use `[]` for empty arrays, `{}` for empty objects\n" 
        "- Decimal values like `0.7`, `8.6`, `12.34` are fully supported\n"
        "- Empty fields (`null`, `\"\"`, `[]`) are automatically removed from final output\n"
        "- Click 'Generate JSON Output' to create the final array for API testing\n"
        "- Use the download button to save your test cases as a `.json` file"
    )

if __name__ == "__main__":
    main()
