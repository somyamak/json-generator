import streamlit as st
import json
import copy
from typing import Dict, Any, List, Union

# Page configuration
st.set_page_config(
    page_title="JSON Generator + Editor",
    page_icon="🔧",
    layout="wide"
)

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary for easier form editing.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for nested keys
    
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Handle lists by converting to string representation
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)

def unflatten_dict(flat_dict: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """
    Unflatten a dictionary back to nested structure.
    
    Args:
        flat_dict: Flattened dictionary
        sep: Separator used for nested keys
    
    Returns:
        Nested dictionary
    """
    result = {}
    for key, value in flat_dict.items():
        keys = key.split(sep)
        d = result
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        
        # Try to convert string representations back to appropriate types
        if isinstance(value, str):
            # Try to parse as JSON for lists/objects
            if value.startswith('[') and value.endswith(']'):
                try:
                    d[keys[-1]] = json.loads(value)
                except:
                    d[keys[-1]] = value
            # Try to parse numbers
            elif value.isdigit():
                d[keys[-1]] = int(value)
            elif '.' in value and value.replace('.', '').isdigit():
                d[keys[-1]] = float(value)
            # Boolean values
            elif value.lower() in ['true', 'false']:
                d[keys[-1]] = value.lower() == 'true'
            else:
                d[keys[-1]] = value
        else:
            d[keys[-1]] = value
    
    return result

def clean_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove empty, null, or None values from JSON.
    
    Args:
        data: Dictionary to clean
    
    Returns:
        Cleaned dictionary
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, dict):
                cleaned_nested = clean_json(value)
                if cleaned_nested:  # Only add if not empty
                    cleaned[key] = cleaned_nested
            elif isinstance(value, list):
                cleaned_list = [clean_json(item) if isinstance(item, dict) else item 
                              for item in value if item not in [None, "", []]]
                if cleaned_list:
                    cleaned[key] = cleaned_list
            elif value not in [None, "", "null", "None"]:
                cleaned[key] = value
        return cleaned
    return data

def initialize_session_state():
    """Initialize session state variables."""
    if 'original_json' not in st.session_state:
        st.session_state.original_json = None
    if 'generated_jsons' not in st.session_state:
        st.session_state.generated_jsons = []
    if 'edited_jsons' not in st.session_state:
        st.session_state.edited_jsons = {}
    if 'output_jsons' not in st.session_state:
        st.session_state.output_jsons = {}
    if 'show_forms' not in st.session_state:
        st.session_state.show_forms = False
    if 'current_editing' not in st.session_state:
        st.session_state.current_editing = None

def create_json_form(json_data: Dict[str, Any], form_key: str, json_index: int):
    """
    Create an editable form for a JSON object.
    
    Args:
        json_data: The JSON data to edit
        form_key: Unique key for the form
        json_index: Index of the JSON being edited
    """
    st.subheader(f"📝 Edit {form_key}")
    
    # Flatten the JSON for easier editing
    flat_data = flatten_dict(json_data)
    
    # Create form
    with st.form(key=f"form_{form_key}"):
        edited_values = {}
        
        # Create input fields for each flattened key
        for key, value in flat_data.items():
            # Determine the appropriate input widget based on value type
            if isinstance(value, bool):
                edited_values[key] = st.checkbox(key, value=value)
            elif isinstance(value, (int, float)):
                edited_values[key] = st.number_input(key, value=float(value))
            else:
                # For strings, lists, etc.
                edited_values[key] = st.text_input(key, value=str(value) if value is not None else "")
        
        col1, col2 = st.columns(2)
        with col1:
            generate_clicked = st.form_submit_button("🔄 Generate Output JSON", type="primary")
        with col2:
            preview_clicked = st.form_submit_button("👁️ Preview Changes")
        
        if generate_clicked or preview_clicked:
            # Unflatten the edited values back to nested structure
            unflattened = unflatten_dict(edited_values)
            
            # Store the edited JSON
            st.session_state.edited_jsons[json_index] = unflattened
            
            if generate_clicked:
                # Clean and store the output JSON
                cleaned_json = clean_json(unflattened)
                st.session_state.output_jsons[json_index] = cleaned_json
                st.success(f"✅ Output generated for {form_key}!")
            
            if preview_clicked:
                st.info("📋 Preview of your changes:")
                st.json(unflattened)

def display_output_json(json_index: int, json_key: str):
    """
    Display the output JSON with copy functionality.
    
    Args:
        json_index: Index of the JSON
        json_key: Key/name of the JSON
    """
    if json_index in st.session_state.output_jsons:
        st.subheader(f"📤 Output for {json_key}")
        
        output_json = st.session_state.output_jsons[json_index]
        json_string = json.dumps(output_json, indent=2)
        
        # Display the JSON
        st.code(json_string, language="json")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Copy functionality using download button
            st.download_button(
                label="📋 Download JSON",
                data=json_string,
                file_name=f"{json_key}.json",
                mime="application/json",
                key=f"download_{json_index}"
            )
        
        with col2:
            # Edit again button
            if st.button(f"🔁 Edit Again", key=f"edit_again_{json_index}"):
                st.session_state.current_editing = json_index
                st.rerun()

def main():
    """Main application function."""
    initialize_session_state()
    
    st.title("🔧 JSON Generator + Editor")
    st.markdown("**Build and edit multiple JSON versions for your health score API**")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("📋 Navigation")
        if st.session_state.original_json:
            st.success("✅ Base JSON loaded")
            if st.button("🔄 Start Over"):
                # Reset all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        if st.session_state.generated_jsons:
            st.info(f"📊 {len(st.session_state.generated_jsons)} JSONs generated")
        
        if st.session_state.output_jsons:
            st.success(f"✨ {len(st.session_state.output_jsons)} outputs ready")
    
    # Step 1: Input Base JSON Template
    if not st.session_state.original_json:
        st.header("1️⃣ Input Base JSON Template")
        st.markdown("Paste your base JSON structure below:")
        
        # Provide a sample JSON for demonstration
        sample_json = {
            "user_info": {
                "name": "",
                "age": 0,
                "email": ""
            },
            "health_metrics": {
                "bmi": 0.0,
                "blood_pressure": {
                    "systolic": 0,
                    "diastolic": 0
                },
                "cholesterol": 0
            },
            "lifestyle": {
                "exercise_hours_per_week": 0,
                "smoking": False,
                "alcohol_consumption": ""
            }
        }
        
        json_input = st.text_area(
            "JSON Template (json0):",
            value=json.dumps(sample_json, indent=2),
            height=300,
            help="This will be your base template for generating multiple versions"
        )
        
        if st.button("📥 Load JSON Template", type="primary"):
            try:
                parsed_json = json.loads(json_input)
                st.session_state.original_json = parsed_json
                st.success("✅ JSON template loaded successfully!")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON format: {str(e)}")
    
    # Step 2: Generate Multiple JSONs
    elif not st.session_state.show_forms:
        st.header("2️⃣ Generate Multiple JSONs")
        
        # Display the loaded JSON
        st.subheader("📋 Your Base JSON Template:")
        st.json(st.session_state.original_json)
        
        # Generation options
        col1, col2 = st.columns(2)
        
        with col1:
            num_jsons = st.number_input(
                "How many JSONs to generate?",
                min_value=1,
                max_value=20,
                value=3,
                help="Specify the number of JSON copies you want to create"
            )
        
        with col2:
            st.markdown("**Generation Options:**")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔁 Duplicate JSON", type="primary"):
                    # Generate exact copies
                    st.session_state.generated_jsons = [
                        copy.deepcopy(st.session_state.original_json) 
                        for _ in range(num_jsons)
                    ]
                    st.session_state.show_forms = True
                    st.success(f"✅ Generated {num_jsons} duplicate JSONs!")
                    st.rerun()
            
            with col_b:
                if st.button("🆕 Create Empty JSONs"):
                    # Generate empty versions
                    def make_empty(obj):
                        if isinstance(obj, dict):
                            return {k: make_empty(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return []
                        elif isinstance(obj, str):
                            return ""
                        elif isinstance(obj, (int, float)):
                            return 0
                        elif isinstance(obj, bool):
                            return False
                        else:
                            return None
                    
                    empty_template = make_empty(st.session_state.original_json)
                    st.session_state.generated_jsons = [
                        copy.deepcopy(empty_template) 
                        for _ in range(num_jsons)
                    ]
                    st.session_state.show_forms = True
                    st.success(f"✅ Generated {num_jsons} empty JSONs!")
                    st.rerun()
    
    # Step 3: Edit Forms and Display Outputs
    else:
        st.header("3️⃣ Edit Your JSONs")
        
        # Display editing interface
        for i, json_data in enumerate(st.session_state.generated_jsons):
            json_key = f"json{i}"
            
            # Create two columns: form on left, output on right
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Show form if this JSON is being edited or no specific JSON is being edited
                if st.session_state.current_editing is None or st.session_state.current_editing == i:
                    create_json_form(
                        st.session_state.edited_jsons.get(i, json_data),
                        json_key,
                        i
                    )
            
            with col2:
                # Show output if available
                display_output_json(i, json_key)
            
            # Add separator between JSONs
            if i < len(st.session_state.generated_jsons) - 1:
                st.divider()
        
        # Reset current editing when done
        if st.session_state.current_editing is not None:
            if st.button("📝 Edit All JSONs"):
                st.session_state.current_editing = None
                st.rerun()

if __name__ == "__main__":
    main()
