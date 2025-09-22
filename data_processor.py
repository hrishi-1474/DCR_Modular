import streamlit as st
import pandas as pd
import json
import concurrent.futures
from llm_backend import llm, call_llm_parallel, process_llm_response, initial_prompt_template, refinement_prompt_template, call_llm, clean_brand_name

def calculate_column_group_summary(cluster_columns, dataframes):
    """Calculate summary information for a column group."""
    all_unique_values = set()
    cluster_columns_info = []
    
    for col in cluster_columns:
        # Only process string columns
        if isinstance(col, str):
            for filename, df in dataframes.items():
                if col in df.columns:
                    if df[col].dtype == 'object' or df[col].dtype == 'string':
                        # Get unique values from this column and filter for strings only
                        col_values = df[col].dropna().tolist()
                        string_values = []
                        for val in col_values:
                            if isinstance(val, str):
                                # Clean the brand name before processing
                                cleaned_val = clean_brand_name(val)
                                string_values.append(cleaned_val)
                        
                        # Get unique string values
                        col_unique_values = list(set(string_values))
                        all_unique_values.update(col_unique_values)
                        cluster_columns_info.append({
                            'filename': filename,
                            'column': col,
                            'unique_count': len(col_unique_values),
                            'total_count': df[col].count()
                        })
    
    unique_values = list(all_unique_values)
    
    # Get sample values (first 10 or all if less than 10) for display
    sample_values = unique_values[:10] if len(unique_values) > 10 else unique_values
    
    return {
        'total_unique_values': len(unique_values),
        'sample_values': sample_values,
        'all_unique_values': unique_values,  # Add this to return all unique values
        'columns_info': cluster_columns_info
    }

def get_columns_with_filenames(selected_columns, dataframes):
    """Get columns with their corresponding file names."""
    columns_with_files = []
    for col in selected_columns:
        # Only process string columns
        if isinstance(col, str):
            for filename, df in dataframes.items():
                if col in df.columns:
                    # Extract sheet name from filename if it contains " - "
                    if " - " in filename:
                        sheet_name = filename.split(" - ")[-1]
                        display_name = sheet_name
                    else:
                        display_name = filename
                    columns_with_files.append(f"{display_name}: {col}")
                    break
    return sorted(columns_with_files)

def generate_column_groups_summary_table(user_cluster_selections, custom_clusters, dataframes):
    """Generate comprehensive summary table for all column groups with per-column sample values."""
    summary_data = []
    
    # Process auto-generated column groups
    for cluster_key, selected_columns in user_cluster_selections.items():
        if selected_columns and cluster_key.startswith('cluster_'):
            cluster_num = cluster_key.split('_')[1]
            group_name = f"Column Group {int(cluster_num)+1}"
            
            # Get columns with file names
            columns_with_files = get_columns_with_filenames(selected_columns, dataframes)
            
            # Calculate total unique values for the group
            summary = calculate_column_group_summary(selected_columns, dataframes)
            total_unique_values = summary['total_unique_values']
            
            # Create detailed sample values string for each column
            detailed_samples = []
            for col in selected_columns:
                for filename, df in dataframes.items():
                    if col in df.columns:
                        if df[col].dtype == 'object' or df[col].dtype == 'string':
                            # Get sample values from this specific column
                            col_values = df[col].dropna()
                            string_values = [str(val) for val in col_values if isinstance(val, str)]
                            
                            if len(string_values) > 0:
                                # Take first 5 sample values from this column
                                sample_size = min(5, len(string_values))
                                sample_values = string_values[:sample_size]
                                sample_str = ', '.join([f'"{val}"' for val in sample_values])
                                
                                if len(string_values) > 5:
                                    remaining = len(string_values) - 5
                                    sample_str += f' ... and {remaining} more'
                                
                                detailed_samples.append(f"{col}: {sample_str}")
                            else:
                                detailed_samples.append(f"{col}: (no string values)")
                        else:
                            detailed_samples.append(f"{col}: (not string column)")
                        break
            
            # Join all column samples with line breaks for better readability
            samples_display = '\n'.join(detailed_samples)
            
            summary_data.append({
                'Column Group Name': group_name,
                'Columns in Group': ', '.join(columns_with_files),
                'Total Unique Values': total_unique_values,
                'Sample Values (per column)': samples_display,
                'Additional Instructions/Feedback': ''
            })
    
    # Process custom column groups
    for i, custom_cluster in enumerate(custom_clusters):
        custom_cluster_key = f"custom_cluster_{i}"
        if custom_cluster_key in user_cluster_selections:
            selected_columns = user_cluster_selections[custom_cluster_key]
            if selected_columns:
                group_name = f"Custom Column Group {i+1}"
                
                # Get columns with file names
                columns_with_files = get_columns_with_filenames(selected_columns, dataframes)
                
                # Calculate total unique values for the group
                summary = calculate_column_group_summary(selected_columns, dataframes)
                total_unique_values = summary['total_unique_values']
                
                # Create detailed sample values string for each column
                detailed_samples = []
                for col in selected_columns:
                    for filename, df in dataframes.items():
                        if col in df.columns:
                            if df[col].dtype == 'object' or df[col].dtype == 'string':
                                # Get sample values from this specific column
                                col_values = df[col].dropna()
                                string_values = [str(val) for val in col_values if isinstance(val, str)]
                                
                                if len(string_values) > 0:
                                    # Take first 5 sample values from this column
                                    sample_size = min(5, len(string_values))
                                    sample_values = string_values[:sample_size]
                                    sample_str = ', '.join([f'"{val}"' for val in sample_values])
                                    
                                    if len(string_values) > 5:
                                        remaining = len(string_values) - 5
                                        sample_str += f' ... and {remaining} more'
                                    
                                    detailed_samples.append(f"{col}: {sample_str}")
                                else:
                                    detailed_samples.append(f"{col}: (no string values)")
                            else:
                                detailed_samples.append(f"{col}: (not string column)")
                            break
                
                # Join all column samples with line breaks for better readability
                samples_display = '\n'.join(detailed_samples)
                
                summary_data.append({
                    'Column Group Name': group_name,
                    'Columns in Group': ', '.join(columns_with_files),
                    'Total Unique Values': total_unique_values,
                    'Sample Values (per column)': samples_display,
                    'Additional Instructions/Feedback': ''
                })
    
    return summary_data

def generate_mappings_for_all_columns(user_cluster_selections, custom_clusters, dataframes):
    """Generate initial mappings for all individual columns using parallel processing."""
    all_column_mappings = {}
    
    # Check if LLM is available
    if llm is None:
        st.error("LLM not initialized. Cannot generate mappings.")
        return all_column_mappings
    
    # Prepare all tasks for parallel processing
    tasks = []
    
    # Process auto-generated column groups
    for cluster_key, selected_columns in user_cluster_selections.items():
        if selected_columns and cluster_key.startswith('cluster_'):
            cluster_num = cluster_key.split('_')[1]
            group_name = f"Column Group {int(cluster_num)+1}"
            
            # Process each column individually
            for col in selected_columns:
                # Get unique values for this specific column
                column_values = set()
                for filename, df in dataframes.items():
                    if col in df.columns:
                        if df[col].dtype == 'object' or df[col].dtype == 'string':
                            col_values = df[col].dropna()
                            string_values = [str(val) for val in col_values if isinstance(val, str)]
                            column_values.update(string_values)
                
                if column_values:
                    # Create column identifier
                    column_id = f"{group_name} - {col}"
                    
                    # Clean brand names before processing
                    cleaned_values = [clean_brand_name(val) for val in column_values]
                    unique_values = list(set(cleaned_values))
                    
                    if unique_values:
                        initial_prompt = initial_prompt_template(unique_values)
                        tasks.append((column_id, initial_prompt, unique_values))
    
    # Process custom column groups
    for i, custom_cluster in enumerate(custom_clusters):
        custom_cluster_key = f"custom_cluster_{i}"
        if custom_cluster_key in user_cluster_selections:
            selected_columns = user_cluster_selections[custom_cluster_key]
            if selected_columns:
                group_name = f"Custom Column Group {i+1}"
                
                # Process each column individually
                for col in selected_columns:
                    # Get unique values for this specific column
                    column_values = set()
                    for filename, df in dataframes.items():
                        if col in df.columns:
                            if df[col].dtype == 'object' or df[col].dtype == 'string':
                                col_values = df[col].dropna()
                                string_values = [str(val) for val in col_values if isinstance(val, str)]
                                column_values.update(string_values)
                    
                    if column_values:
                        # Create column identifier
                        column_id = f"{group_name} - {col}"
                        
                        # Clean brand names before processing
                        cleaned_values = [clean_brand_name(val) for val in column_values]
                        unique_values = list(set(cleaned_values))
                        
                        if unique_values:
                            initial_prompt = initial_prompt_template(unique_values)
                            tasks.append((column_id, initial_prompt, unique_values))
    
    # Execute LLM calls in parallel
    if tasks:
        # Create a progress container for real-time updates
        progress_container = st.empty()
        completed_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tasks), 5)) as executor:
            # Submit all tasks
            future_to_column = {
                executor.submit(call_llm_parallel, prompt, column_id): (column_id, unique_values)
                for column_id, prompt, unique_values in tasks
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_column):
                column_id, unique_values = future_to_column[future]
                try:
                    result_column_id, output, error = future.result()
                    completed_count += 1
                    
                    # Update progress message
                    progress_container.success(f"Generating mappings for {column_id} ({completed_count}/{len(tasks)})")
                    
                    if error:
                        st.error(f"Error processing {column_id}: {error}")
                        all_column_mappings[column_id] = f"Error: {error}"
                    else:
                        # output is now a string from llm.predict()
                        processed_output = process_llm_response(output, column_id)
                        all_column_mappings[column_id] = processed_output
                        
                except Exception as e:
                    completed_count += 1
                    progress_container.error(f"❌ Failed {column_id} ({completed_count}/{len(tasks)})")
                    st.error(f"Unexpected error processing {column_id}: {e}")
                    all_column_mappings[column_id] = f"Error: {e}"
    
    return all_column_mappings

def process_feedback_for_all_columns(all_column_mappings, all_column_feedback):
    """Process feedback for all individual columns and generate refined mappings."""
    refined_mappings = {}
    
    for column_id, mapping_output in all_column_mappings.items():
        if column_id in all_column_feedback and all_column_feedback[column_id]:
            # Process feedback for this specific column
            feedback_list = all_column_feedback[column_id]
            
            # Create feedback JSON for refinement
            feedback_json = json.dumps(feedback_list, indent=2)
            
            # Generate refinement prompt
            refinement_prompt = refinement_prompt_template(mapping_output, feedback_json)
            
            # Call LLM for refinement
            try:  
                refined_response = call_llm(refinement_prompt)
                refined_output = process_llm_response(refined_response, column_id)
                refined_mappings[column_id] = refined_output
            except Exception as e:
                st.error(f"Error refining {column_id}: {e}")
                refined_mappings[column_id] = mapping_output  # Keep original if refinement fails
        else:
            # No feedback for this column, keep original mapping
            refined_mappings[column_id] = mapping_output
    
    return refined_mappings

def calculate_standardization_stats(mapping_output):
    """Calculate standardization statistics from mapping output."""
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
                            'Classified As': canonical
                        })
        
        if mappings:
            # Count original unique values
            original_values = set()
            # Count unique standardized values
            standardized_values = set()
            
            for item in mappings:
                original_values.add(item['Brand Name'])
                standardized_values.add(item['Classified As'])
            
            return {
                'original_count': len(original_values),
                'standardized_count': len(standardized_values),
                'reduction': len(original_values) - len(standardized_values),
                'reduction_percentage': round(((len(original_values) - len(standardized_values)) / len(original_values)) * 100, 1) if len(original_values) > 0 else 0
            }
    except Exception as e:
        print(f"Error calculating standardization stats: {e}")
        return None
    return None 