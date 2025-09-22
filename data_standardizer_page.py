import streamlit as st
import pandas as pd
import json
import re
from llm_backend import llm, clean_invalid_escapes
from data_processor import process_feedback_for_all_columns, calculate_standardization_stats

def dedicated_data_cleaning_interface():
    """Dedicated data cleaning interface with comprehensive mappings table and iterative refinement."""
    st.header("Data Value Standardizer")
    # Check if dataframes are available
    if not st.session_state.dataframes:
        st.error("No data uploaded. Please upload files first.")
        st.info("Go to 'Upload Files' to upload your datasets.")
        return
    
    # Check if mappings have been generated
    if not st.session_state.mappings_generated or not st.session_state.all_column_mappings:
        st.warning("Please generate initial mappings first in the Column Analysis page.")
        st.info("Go to 'Column Analysis' to generate mappings for all individual columns.")
        return
    
    # Step 1: Display all mappings and allow feedback
    if st.session_state.cleaning_iteration == 0:
        st.subheader("Iteration 0: Review and provide feedback for all individual column mappings")
        
        # Display all generated mappings
        if st.session_state.all_column_mappings:
            st.success(f"{len(st.session_state.all_column_mappings)} individual column(s) have mappings ready for review.")
            
            # Store feedback
            st.session_state.all_column_feedback = {}
            
            # Display separate table for each individual column
            for column_id, mapping_output in st.session_state.all_column_mappings.items():
                st.markdown(f"### {column_id}")
                
                try: 
                    mapping_output = re.sub(r"```(?:json)?", "", mapping_output).strip()
                    mapping_output = clean_invalid_escapes(mapping_output)
                    
                    # Parse the key=value format instead of JSON
                    mappings = []
                    lines = mapping_output.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if '=' in line:
                            parts = line.split('=', 1)  # Split on first = only
                            if len(parts) == 2:
                                original, canonical = parts[0].strip(), parts[1].strip()
                                if original and canonical:
                                    mappings.append({
                                        'Brand Name': original,
                                        'Classified As': canonical,
                                        'Feedback': ''
                                    })
                    
                    # Create table data for this specific column
                    column_table_data = mappings
                    
                    if column_table_data:
                        column_df = pd.DataFrame(column_table_data)
                        
                        # Display editable table for this column
                        edited_column_df = st.data_editor(
                            column_df,
                            use_container_width=True,
                            height=300,
                            key=f"column_table_{column_id}_{st.session_state.cleaning_iteration}",
                            column_config={
                                "Brand Name": st.column_config.TextColumn("Brand Name", disabled=True),
                                "Classified As": st.column_config.TextColumn("Classified As", disabled=True),
                                "Feedback": st.column_config.TextColumn("Feedback", help="Enter corrected classification here")
                            }
                        )
                        
                        # Calculate and display standardization stats
                        stats = calculate_standardization_stats(mapping_output)
                        if stats:
                            st.success(f"**Standardization Impact:** Reduced unique values from {stats['original_count']} to {stats['standardized_count']} ({stats['reduction']} fewer, {stats['reduction_percentage']}% reduction)")
                        
                        # Store feedback for this column
                        for idx, row in edited_column_df.iterrows():
                            feedback = row['Feedback']
                            if feedback.strip():
                                if column_id not in st.session_state.all_column_feedback:
                                    st.session_state.all_column_feedback[column_id] = []
                                st.session_state.all_column_feedback[column_id].append({
                                    "Brand Name": row['Brand Name'],
                                    "Classified As": feedback.strip()
                                })
                        
                        st.write(f"*{len(column_table_data)} mappings in {column_id}*")
                            
                    else:
                        st.warning(f"No valid mappings found for {column_id}")
                        
                    
                except json.JSONDecodeError as e:
                    st.error(f"Error parsing mappings for {column_id}: {e}")
                    st.code(mapping_output[:200] + "..." if len(mapping_output) > 200 else mapping_output)
                    # Show some context around the error position
                    start = max(e.pos - 50, 0)
                    end = min(e.pos + 50, len(mapping_output))
                    snippet = mapping_output[start:end]
                    
                    print("\n--- Context around error ---")
                    print(snippet)
                    print(" " * (e.pos - start) + "^ (error here)")
                    
                st.divider()
            
            # Process feedback button for all columns
            st.divider()
            col1, col2 = st.columns([1, 1])

            with col1:
                if llm is None:
                    st.error("❌ LLM not initialized. Cannot process feedback.")
                    st.info("Please check your API key configuration.")
                elif st.button("Process Feedback for All Columns", type="primary"):
                    with st.spinner("Processing feedback for all individual columns..."):
                        refined_mappings = process_feedback_for_all_columns(
                            st.session_state.all_column_mappings,
                            st.session_state.all_column_feedback
                        )
                        st.session_state.all_column_mappings = refined_mappings
                        st.session_state.cleaning_iteration = 1
                        st.success("Feedback processed for all individual columns! Starting iterative refinement...")
                        st.rerun()

            with col2:
                if st.button("Apply & Finish", type="primary"):
                    st.session_state.cleaning_finished = True
                    st.success("All mappings finalized! Generating output files...")
                    st.rerun()
        else:
            st.error("No mappings available. Please generate mappings in the Column Analysis page.")
    
    # Step 2+: Iterative Refinement Loop (for all individual columns)
    elif not st.session_state.cleaning_finished:
        st.subheader(f"Iteration {st.session_state.cleaning_iteration}")
        st.write("**Iterative refinement for all individual columns:**")
        
        st.markdown("### Current Mappings with Inline Feedback")
        
        # Store feedback for refinement
        refinement_feedback = {}

        # Display separate table for each individual column
        for column_id, mapping_output in st.session_state.all_column_mappings.items():
            st.markdown(f"### {column_id}")
            
            try:
               
                
                # Parse the key=value format instead of JSON
                mappings = []
                lines = mapping_output.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if '=' in line:
                        parts = line.split('=', 1)  # Split on first = only
                        if len(parts) == 2:
                            original, canonical = parts[0].strip(), parts[1].strip()
                            if original and canonical:
                                mappings.append({
                                    'Brand Name': original,
                                    'Classified As': canonical,
                                    'Feedback': ''
                                })
                
                # Create table data for this specific column
                column_table_data = mappings
                
                if column_table_data:
                    column_df = pd.DataFrame(column_table_data)
                    
                    # Display editable table for this column
                    edited_column_df = st.data_editor(
                        column_df,
                        use_container_width=True,
                        height=300,
                        key=f"refinement_column_table_{column_id}_{st.session_state.cleaning_iteration}",
                        column_config={
                            "Brand Name": st.column_config.TextColumn("Brand Name", disabled=True),
                            "Classified As": st.column_config.TextColumn("Classified As", disabled=True),
                            "Feedback": st.column_config.TextColumn("Feedback", help="Enter corrected classification here")
                        }
                    )
                    
                    # Calculate and display standardization stats
                    stats = calculate_standardization_stats(mapping_output)
                    if stats:
                        st.success(f"**Standardization Impact:** Reduced unique values from {stats['original_count']} to {stats['standardized_count']} ({stats['reduction']} fewer, {stats['reduction_percentage']}% reduction)")
                    
                    # Store feedback for this column
                    for idx, row in edited_column_df.iterrows():
                        feedback = row['Feedback']
                        if feedback.strip():
                            if column_id not in refinement_feedback:
                                refinement_feedback[column_id] = []
                            refinement_feedback[column_id].append({
                                "Brand Name": row['Brand Name'],
                                "Classified As": feedback.strip()
                            })
                    
                    st.write(f"*{len(column_table_data)} mappings in {column_id}*")
                    
                    # Add standardization impact line at the bottom
                    if stats:
                        st.info(f"**Standardization Impact:** Reduced unique values from {stats['original_count']} to {stats['standardized_count']} ({stats['reduction_percentage']}% reduction)")
                        
                else:
                    st.warning(f"No valid mappings found for {column_id}")
                    
            except json.JSONDecodeError as e:
                st.error(f"Error parsing mappings for {column_id}: {e}")
                st.code(mapping_output[:200] + "..." if len(mapping_output) > 200 else mapping_output)
                # Show some context around the error position
                start = max(e.pos - 50, 0)
                end = min(e.pos + 50, len(mapping_output))
                snippet = mapping_output[start:end]
                
                print("\n--- Context around error ---")
                print(snippet)
                print(" " * (e.pos - start) + "^ (error here)")
                
                st.divider()

        # Refinement action buttons
        st.divider()
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Process Feedback for All Columns", key=f"process_refinement_{st.session_state.cleaning_iteration}"):
                if any(refinement_feedback.values()):
                    with st.spinner("Processing refinement feedback for all individual columns..."):
                        refined_mappings = process_feedback_for_all_columns(
                            st.session_state.all_column_mappings,
                            refinement_feedback
                        )
                        st.session_state.all_column_mappings = refined_mappings
                        st.session_state.cleaning_iteration += 1
                        st.success("Refinement feedback processed! Starting next iteration...")
                        st.rerun()
                else:
                    st.warning("No refinement feedback provided. Please enter corrections in the Feedback column.")

        with col2:
            if st.button("Apply & Finish", key=f"apply_finish_{st.session_state.cleaning_iteration}"):
                st.session_state.cleaning_finished = True
                st.success("All mappings finalized! Generating output files...")
                st.rerun()
    
    # Final Output Display
    if st.session_state.cleaning_finished:
        generate_final_output()

def generate_final_output():
    """Generate final Excel outputs."""
    st.subheader("Final Output:")
    st.write("All individual columns have been processed successfully!")
    
    # Generate two specific Excel files
    try:
        # File A: Excel with only final mappings (one sheet per individual column)
        with pd.ExcelWriter("final_mappings_only.xlsx", engine='openpyxl') as writer:
            for column_id, mapping_output in st.session_state.all_column_mappings.items():
                try:
                    
                    # Parse the key=value format instead of JSON
                    mappings = []
                    lines = mapping_output.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if '=' in line:
                            parts = line.split('=', 1)  # Split on first = only
                            if len(parts) == 2:
                                original, canonical = parts[0].strip(), parts[1].strip()
                                if original and canonical:
                                    mappings.append({
                                        'Brand Name': original,
                                        'Classified As': canonical,
                                        'Feedback': ''
                                    })
                    
                    # Create mapping dataframe for this column
                    mapping_data = mappings
                    
                    if mapping_data:
                        mapping_df = pd.DataFrame(mapping_data)
                        # Clean sheet name for Excel
                        safe_sheet_name = column_id.replace(' ', '_').replace(':', '_').replace('-', '_')[:31]
                        mapping_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                    
                except Exception as e:
                    st.error(f"Error processing mappings for {column_id}: {e}")
        
        # Download File A
        with open("final_mappings_only.xlsx", "rb") as file:
            st.download_button(
                "📊 Download Final Mappings Excel",
                data=file.read(),
                file_name="final_mappings_only.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # File B: Excel with all original data plus new mapping columns
        with pd.ExcelWriter("cleaned_data_with_mappings.xlsx", engine='openpyxl') as writer:
            for filename, df in st.session_state.dataframes.items():
                # Create a copy of the dataframe
                df_with_mappings = df.copy()
                
                # Add mapping columns for all individual columns
                for column_id, mapping_output in st.session_state.all_column_mappings.items():
                    try:
                        # Parse the key=value format instead of JSON
                        mappings = []
                        lines = mapping_output.split('\n')
                        
                        for line in lines:
                            line = line.strip()
                            if '=' in line:
                                parts = line.split('=', 1)  # Split on first = only
                                if len(parts) == 2:
                                    original, canonical = parts[0].strip(), parts[1].strip()
                                    if original and canonical:
                                        mappings.append({
                                            'Brand Name': original,
                                            'Classified As': canonical,
                                            'Feedback': ''
                                        })
                        
                        # Create value mapping dictionary - FIX THE KEYS HERE
                        value_mapping = {}
                        for item in mappings:
                            value_mapping[item['Brand Name']] = item['Classified As']  # Fixed keys
                        
                        # Extract column name from column_id (format: "Column Group X - ColumnName")
                        if " - " in column_id:
                            column_name = column_id.split(" - ")[1]
                        else:
                            column_name = column_id
                        
                        # Add mapping column for this specific column
                        if column_name in df.columns:
                            # Create new column name
                            new_col_name = f"{column_name}_standardized"
                            
                            # Apply mapping to create new column
                            df_with_mappings[new_col_name] = df[column_name].map(value_mapping).fillna(df[column_name])
                    
                    except Exception as e:
                        st.error(f"Error processing mappings for {column_id}: {e}")
                
                # Write to Excel sheet
                sheet_name = filename.replace('.csv', '').replace('.xlsx', '').replace('.xls', '')[:31]
                df_with_mappings.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Download File B
        with open("cleaned_data_with_mappings.xlsx", "rb") as file:
            st.download_button(
                "📋 Download Cleaned Data with Mappings Excel",
                data=file.read(),
                file_name="cleaned_data_with_mappings.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.success("Two Excel files generated successfully!")
        
    except Exception as e:
        st.error(f"Error creating Excel files: {e}")
    
    # Navigation back to main app
    st.divider()
    if st.button("Start New Cleaning"):
        # Clear ALL session state variables
        st.session_state.clear()
        
        # Re-initialize essential session state variables
        st.session_state.dataframes = {}
        st.session_state.analysis_complete = False
        st.session_state.upload_output = None
        st.session_state.analysis_output = None
        st.session_state.current_page = "📁 Upload Files"
        st.session_state.cleaning_iteration = 0
        st.session_state.data_values = []
        st.session_state.output_history = []
        st.session_state.latest_output = ""
        st.session_state.cleaning_finished = False
        st.session_state.user_cluster_selections = {}
        st.session_state.cluster_index = None
        st.session_state.cluster_columns = []
        st.session_state.cluster_columns_info = []
        st.session_state.inline_feedback = {}
        st.session_state.all_column_mappings = {}
        st.session_state.all_column_feedback = {}
        st.session_state.mappings_generated = False
        
        # Navigate to Upload Files page and refresh
        st.rerun() 