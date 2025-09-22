import streamlit as st
import pandas as pd
import json
from llm_backend import llm, call_llm
from data_processor import generate_column_groups_summary_table, generate_mappings_for_all_columns

def analyze_columns():
    """Perform automatic column analysis."""
    
    if not st.session_state.dataframes:
        st.warning("Please upload files first.")
        return False
    
    with st.spinner("Analyzing columns across all datasets..."):
        # Create a simplified report with only essential information
        report = {
            "similarity_clusters": []
        }
        
        # Find similar columns across all datasets using LLM-based clustering
        # Only consider string-type columns for similarity analysis
        all_columns = []
        string_columns = []
        
        for filename, df in st.session_state.dataframes.items():
            for col in df.columns:
                all_columns.append(col)
                # Check if column name is a string and column contains string data
                if isinstance(col, str) and (df[col].dtype == 'object' or df[col].dtype == 'string'):
                    # Additional check: sample some values to ensure they're actually strings
                    sample_values = df[col].dropna().head(10)
                    if len(sample_values) > 0 and all(isinstance(val, str) for val in sample_values):
                        string_columns.append(col)
        
        # Use LLM-based clustering 
        if llm is not None:
            clusters = llm_based_column_clustering(st.session_state.dataframes, llm)
        else:
            st.error("LLM not available for column clustering")
            clusters = []
        
        report["similarity_clusters"] = clusters
        
        # Store analysis results
        st.session_state.analysis_report = report
        st.session_state.analysis_complete = True
        
        # Show similarity clusters with interactive multi-select dropdowns
        if report.get('similarity_clusters'):
            st.write("**Tip:** Use the dropdowns below to customize your column groups. Select/deselect columns as needed.")
            
            for i, cluster in enumerate(report['similarity_clusters']):
                if len(cluster) > 1:  # Only show clusters with multiple columns
                    # Group columns by file
                    columns_by_file = {}
                    for col in cluster:
                        for filename, df in st.session_state.dataframes.items():
                            if col in df.columns:
                                if filename not in columns_by_file:
                                    columns_by_file[filename] = []
                                columns_by_file[filename].append(col)
                                break
                    
                    # Display cluster with interactive dropdowns
                    st.write(f"**Cluster {i+1}:**")
                    
                    # Initialize user selections for this cluster if not exists
                    cluster_key = f"cluster_{i}"
                    if cluster_key not in st.session_state.user_cluster_selections:
                        st.session_state.user_cluster_selections[cluster_key] = cluster.copy()
                    
                    # Create multi-select dropdowns for each file
                    for filename, cols in columns_by_file.items():
                        # Get all available columns from this file
                        all_file_columns = st.session_state.dataframes[filename].columns.tolist()
                        
                        # Get current selections for this file in this cluster
                        current_selections = [col for col in cols if col in st.session_state.user_cluster_selections[cluster_key]]
                        
                        # Multi-select dropdown
                        selected_columns = st.multiselect(
                            f"**{filename}** columns:",
                            options=sorted([col for col in all_file_columns if isinstance(col, str)]),
                            default=current_selections,
                            key=f"cluster_{i}_{filename}",
                            help=f"Select columns from {filename} that should be in this cluster"
                        )
                        
                        # Update user selections
                        # Remove old selections for this file
                        st.session_state.user_cluster_selections[cluster_key] = [
                            col for col in st.session_state.user_cluster_selections[cluster_key] 
                            if col not in all_file_columns
                        ]
                        # Add new selections
                        st.session_state.user_cluster_selections[cluster_key].extend(selected_columns)
                    
                    # Show current cluster summary
                    current_cluster = st.session_state.user_cluster_selections[cluster_key]
                    if current_cluster:
                        st.write(f"**Current Cluster {i+1}:** {', '.join(sorted(current_cluster))}")
                    else:
                        st.write(f"**Cluster {i+1}:** No columns selected")
                    
                    st.divider()
            
            # Custom cluster creation section

            
            # Show summary of customized clusters (only if there are any clusters)
            has_user_clusters = any(selected_columns for selected_columns in st.session_state.user_cluster_selections.values())
            
            if has_user_clusters:
                st.subheader("Customized Clusters Summary")
                st.write("**Your customized column clusters:**")
                
                total_customized_columns = 0
                
                # Show user clusters
                for cluster_key, selected_columns in st.session_state.user_cluster_selections.items():
                    if selected_columns:
                        cluster_num = cluster_key.split('_')[1]
                        st.write(f"**Cluster {int(cluster_num)+1}:** {', '.join(sorted(selected_columns))}")
                        total_customized_columns += len(selected_columns)
                
                st.write(f"**Total columns in all clusters:** {total_customized_columns}")
                
                # Add a button to reset customizations
                if st.button("Reset All Customizations"):
                    st.session_state.user_cluster_selections = {}
                    st.success("All customizations reset! Run analysis again to see original clusters.")

        
        # Store output for preservation
        st.session_state.analysis_output = {
            'clusters_found': len([c for c in report.get('similarity_clusters', []) if len(c) > 1]),
            'total_columns_analyzed': len(all_columns),
            'string_columns_found': len(string_columns)
        }
        
        return True

def llm_based_column_clustering(dataframes, llm):
    """
    Use LLM to intelligently group similar columns based on names and sample values.
    
    Args:
        dataframes: Dictionary of {filename: dataframe}
        llm: Initialized LangChain LLM instance
    
    Returns:
        List of clusters, where each cluster is a list of column names
    """
    try:
        # Step 1: Collect column information
        column_info = []
        
        for filename, df in dataframes.items():
            for col in df.columns:
                # Only process string columns
                if isinstance(col, str) and (df[col].dtype == 'object' or df[col].dtype == 'string'):
                    # Get sample values (up to 30)
                    col_values = df[col].dropna()
                    string_values = [str(val) for val in col_values if isinstance(val, str)]
                    
                    if len(string_values) > 0:
                        # Take up to 30 samples (or all if less than 30)
                        sample_size = min(30, len(string_values))
                        sample_values = string_values[:sample_size]  # Take first 30 for consistency
                        
                        column_info.append({
                            'column_name': col,
                            'filename': filename,
                            'sample_values': sample_values,
                            'total_values': len(string_values)
                        })
        
        if len(column_info) < 2:
            return []
        
        # Step 2: Create LLM prompt
        prompt = create_column_clustering_prompt(column_info)
        
        # Step 3: Call LLM (removed redundant spinner)
        response = call_llm(prompt)
        
        # Step 4: Parse response
        clusters = parse_llm_clustering_response(response, column_info)
        
        return clusters
        
    except Exception as e:
        st.error(f"Error in LLM-based clustering: {e}")
        # Fallback: return each column as its own cluster
        fallback_clusters = []
        for filename, df in dataframes.items():
            for col in df.columns:
                if isinstance(col, str) and (df[col].dtype == 'object' or df[col].dtype == 'string'):
                    fallback_clusters.append([col])
        return fallback_clusters

def create_column_clustering_prompt(column_info):
    """Create a comprehensive prompt for LLM column clustering."""
    
    # Build column details string
    column_details = []
    for info in column_info:
        sample_str = ', '.join([f'"{val}"' for val in info['sample_values'][:20]])  # Show first 20 for readability
        if len(info['sample_values']) > 20:
            remaining_count = len(info['sample_values']) - 20
            sample_str += f' ... and {remaining_count} more values'
        
        column_details.append(f"Column: '{info['column_name']}' (File: {info['filename']})\n  Sample values: {sample_str}\n  Total values: {info['total_values']}")
    
    prompt = f"""You are an expert data analyst specializing in data cleaning and standardization. 

Your task is to analyze the following columns and group them into logical clusters based on their names and sample values. Columns in the same cluster should contain similar types of data.

ANALYZE THESE COLUMNS:
{chr(10).join(column_details)}

INSTRUCTIONS:
1. Group columns that likely contain the same type of information.
2. Use both column names and sample values to guide grouping.
3. Consider common patterns such as:
   - Brand names, product names, company names
   - Categories, types, classifications
   - Addresses, locations, regions
   - Descriptions, comments, notes
4. Each column must appear in exactly ONE cluster.
5. Only include clusters of columns with string-type values.don't include columns with majority of numeric or alphanumeric values.
6. Output strictly as a valid JSON array of arrays, where each inner array lists the grouped column names.
7. Do not include explanations, comments, or extra text outside the JSON.

EXAMPLE OUTPUT FORMAT:
[
  ["brand_name", "product_brand", "brand"],
  ["category", "product_type", "item_category"],
  ["address", "location", "shipping_address"]
]

IMPORTANT: Return ONLY the JSON array, no additional text or explanation.

YOUR CLUSTERING RESULT:"""

    return prompt

def parse_llm_clustering_response(response, column_info):
    """Parse the LLM response to extract column clusters."""
    try:
        # Clean the response
        cleaned_response = response.strip()
        
        # Remove markdown code blocks if present
        if '```json' in cleaned_response:
            cleaned_response = cleaned_response.split('```json')[1].split('```')[0]
        elif '```' in cleaned_response:
            cleaned_response = cleaned_response.split('```')[1]
        
        # Parse JSON
        clusters = json.loads(cleaned_response)
        
        # Validate clusters
        if not isinstance(clusters, list):
            st.warning("Invalid response format from LLM")
            return []
        
        # Validate that all columns are present and each appears only once
        all_columns_in_response = []
        for cluster in clusters:
            if isinstance(cluster, list):
                all_columns_in_response.extend(cluster)
        
        # Get all actual column names
        actual_column_names = [info['column_name'] for info in column_info]
        
        # Check if all columns are accounted for
        missing_columns = set(actual_column_names) - set(all_columns_in_response)
        extra_columns = set(all_columns_in_response) - set(actual_column_names)
        
        if missing_columns:
            st.warning(f"LLM missed some columns: {missing_columns}")
            # Add missing columns as individual clusters
            for col in missing_columns:
                clusters.append([col])
        
        if extra_columns:
            st.warning(f"LLM included non-existent columns: {extra_columns}")
            # Remove extra columns
            for cluster in clusters:
                if isinstance(cluster, list):
                    cluster[:] = [col for col in cluster if col in actual_column_names]
        
        
        return clusters
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse LLM response as JSON: {e}")
        st.warning("LLM response:")
        st.code(response[:500] + "..." if len(response) > 500 else response)
        # Fallback: return each column as its own cluster
        fallback_clusters = []
        for info in column_info:
            fallback_clusters.append([info['column_name']])
        return fallback_clusters

def show_column_analysis_page():
    """Display the column analysis page."""
    if st.session_state.dataframes:
        # Always show analysis results (run if not already done)
        if not st.session_state.analysis_complete or not st.session_state.analysis_report:
            analyze_columns()
        # Show analysis results
        st.header("Automatic Column Analysis")
        if st.session_state.analysis_report:
            report = st.session_state.analysis_report
            
            # Initialize custom clusters if not exists
            if 'custom_clusters' not in st.session_state:
                st.session_state.custom_clusters = []
            
            # Show similarity clusters in table format
            if report.get('similarity_clusters'):
                st.write("**Tip:** Use the dropdowns below to customize your column groups. Select/deselect columns as needed.")
                
                # Get all file names for table headers
                file_names = list(st.session_state.dataframes.keys())
                
                # Add CSS for styling
                st.markdown("""
                <style>
                .cluster-table-container {
                    border: 2px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 10px 0;
                    background-color: #f9f9f9;
                }
                .cluster-header {
                    background-color: #e9ecef;
                    border: 1px solid #ddd;
                    padding: 8px;
                    margin: 2px 0;
                    border-radius: 3px;
                    font-weight: bold;
                }
                .cluster-row {
                    background-color: white;
                    border: 1px solid #ddd;
                    padding: 6px;
                    margin: 1px 0;
                    border-radius: 3px;
                }
                .cluster-label {
                    background-color: #f0f0f0;
                    padding: 12px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    text-align: center;
                    margin: 4px 0;
                    min-height: 40px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Display column groups and generate button
                display_column_groups_and_generate_button()
    else:
        st.warning("Please upload files first.")

def show_custom_cluster_creation(file_names):
    """Display custom cluster creation interface."""
    # Initialize custom clusters if not exists
    if 'custom_clusters' not in st.session_state:
        st.session_state.custom_clusters = []
    
    # Button to add custom column group
    if st.button("Add Custom Column Group"):
        # Create a new empty custom cluster
        new_cluster_index = len(st.session_state.custom_clusters)
        st.session_state.custom_clusters.append([])
        
        # Initialize user selections for this new custom cluster
        custom_cluster_key = f"custom_cluster_{new_cluster_index}"
        if 'user_cluster_selections' not in st.session_state:
            st.session_state.user_cluster_selections = {}
        st.session_state.user_cluster_selections[custom_cluster_key] = []
        
        st.success(f"Added Custom Group {new_cluster_index + 1}!")
        st.rerun()

def display_column_groups_and_generate_button():
    """Display column groups and generate mappings button."""
    # Generate comprehensive summary table
    if 'custom_clusters' not in st.session_state:
        st.session_state.custom_clusters = []
    
    summary_data = generate_column_groups_summary_table(
        st.session_state.user_cluster_selections, 
        st.session_state.custom_clusters, 
        st.session_state.dataframes
    )
    
    if summary_data:
        st.subheader("📊 Comprehensive Column Groups Summary")
        st.write("Review your column groups before generating initial mappings:")
        
        # Create DataFrame and display as editable table
        summary_df = pd.DataFrame(summary_data)
        
        # Display as editable table
        edited_summary_df = st.data_editor(
            summary_df,
            use_container_width=True,
            height=400,
            column_config={
                "Column Group Name": st.column_config.TextColumn("Column Group Name", disabled=True),
                "Columns in Group": st.column_config.TextColumn("Columns in Group", disabled=True),
                "Total Unique Values": st.column_config.NumberColumn("Total Unique Values", disabled=True),
                "Sample Values (per column)": st.column_config.TextColumn("Sample Values (per column)", disabled=True, width="large"),
                "Additional Instructions/Feedback": st.column_config.TextColumn("Additional Instructions/Feedback", help="Add specific instructions for this group")
            },
            key="column_groups_summary_table"
        )
        
        # Store any feedback/instructions
        for idx, row in edited_summary_df.iterrows():
            feedback = row.get('Additional Instructions/Feedback', '').strip()
            if feedback:
                group_name = row['Column Group Name']
                if 'column_group_feedback' not in st.session_state:
                    st.session_state.column_group_feedback = {}
                st.session_state.column_group_feedback[group_name] = feedback
        
        # Generate mappings button
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if llm is None:
                st.error("❌ LLM not initialized. Cannot generate mappings.")
                st.info("Please check your API key configuration.")
            elif st.button("🚀 Generate Initial Mappings", type="primary", use_container_width=True):
                with st.spinner("Generating mappings for all individual columns..."):
                    all_mappings = generate_mappings_for_all_columns(
                        st.session_state.user_cluster_selections,
                        st.session_state.custom_clusters,
                        st.session_state.dataframes
                    )
                    st.session_state.all_column_mappings = all_mappings
                    st.session_state.mappings_generated = True
                    # Automatically navigate to Data Value Standardizer page
                    st.session_state.current_page = "🥤 Data Value Standardizer"
                    st.success("Initial mappings generated successfully! Redirecting to Data Value Standardizer...")
                    st.rerun()
        
        # Add regenerate button
        if st.session_state.get('mappings_generated', False):
            with col1:
                if llm is None:
                    st.error("❌ LLM not initialized. Cannot regenerate mappings.")
                    st.info("Please check your API key configuration.")
                elif st.button("🔄 Regenerate Mappings", help="Generate new mappings with current column selections"):
                    with st.spinner("Regenerating mappings for all individual columns..."):
                        all_mappings = generate_mappings_for_all_columns(
                            st.session_state.user_cluster_selections,
                            st.session_state.custom_clusters,
                            st.session_state.dataframes
                        )
                        st.session_state.all_column_mappings = all_mappings
                        st.success("Mappings regenerated successfully!")
    else:
        st.info("No column groups available. Please customize your clusters above to create groups.") 