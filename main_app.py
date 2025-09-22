import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import re
from typing import Dict, List, Tuple, Optional, Any
import yaml

# Import all page modules
from upload_page import upload_files
from column_analysis_page import show_column_analysis_page
from data_standardizer_page import dedicated_data_cleaning_interface

# Page configuration
st.set_page_config(
    page_title="Clean Room Data Processor",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean white theme with gray/silver buttons
st.markdown("""
<style>
/* Remove all custom backgrounds - use default white */
.stApp {
    background-color: white;
}

/* Fix white strip at top */
.stApp > header {
    background-color: white !important;
}

/* Main content area styling */
.main .block-container {
    background-color: white;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Sidebar styling */
.css-1d391kg {
    background-color: #f8f9fa;
}

/* Button styling - Modern gray/silver theme */
.stButton > button {
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stButton > button:hover {
    background-color: #5a6268;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    transform: translateY(-1px);
}

.stButton > button:active {
    background-color: #545b62;
    transform: translateY(0px);
}

/* Primary button styling */
.stButton > button[data-baseweb="button"][data-testid="baseButton-primary"] {
    background-color: #495057;
    color: white;
}

.stButton > button[data-baseweb="button"][data-testid="baseButton-primary"]:hover {
    background-color: #343a40;
}

/* Success/download buttons */
.stDownloadButton > button {
    background-color: #28a745;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stDownloadButton > button:hover {
    background-color: #218838;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    transform: translateY(-1px);
}

/* Radio button styling - circular buttons */
.stRadio > div {
    gap: 0.5rem;
}

.stRadio > div > label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0;
    cursor: pointer;
}

.stRadio > div > label > div[data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    flex: 1;
}

/* Style the radio button itself */
.stRadio > div > label > div:first-child {
    width: 16px !important;
    height: 16px !important;
    border-radius: 50% !important;
    border: 2px solid #dee2e6 !important;
    background-color: white !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    min-width: 16px !important;
    min-height: 16px !important;
}

/* Selected state */
.stRadio > div > label > div:first-child[data-testid="baseButton-secondary"] {
    border-color: #495057 !important;
    background-color: #495057 !important;
}

/* Inner dot for selected state - darker center */
.stRadio > div > label > div:first-child[data-testid="baseButton-secondary"]::after {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #212529;
}

.stRadio > div > label > div:hover {
    background-color: #e9ecef;
    border-color: #adb5bd;
}

/* Multi-select styling */
.stMultiSelect > div > div {
    background-color: white;
    border: 1px solid #ced4da;
    border-radius: 6px;
}

/* File uploader styling */
.stFileUploader > div > div {
    background-color: #f8f9fa;
    border: 2px dashed #dee2e6;
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
}

/* Success/info/warning/error message styling */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
}

/* Data editor styling */
.stDataFrame, .stDataEditor {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    overflow: hidden;
}

/* Header styling */
h1, h2, h3 {
    color: #212529;
    font-weight: 600;
}

/* Divider styling */
hr {
    border-color: #dee2e6;
    margin: 2rem 0;
}

/* Download button styling - remove green background */
.stDownloadButton > button {
    background-color: #6c757d !important;
    border-color: #6c757d !important;
    color: white !important;
}

.stDownloadButton > button:hover {
    background-color: #5a6268 !important;
    border-color: #545b62 !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
def initialize_session_state():
    """Initialize all session state variables."""
    if 'dataframes' not in st.session_state:
        st.session_state.dataframes = {}
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'upload_output' not in st.session_state:
        st.session_state.upload_output = None
    if 'analysis_output' not in st.session_state:
        st.session_state.analysis_output = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "📁 Upload Files"

    # Add cleaning interface session state variables
    if 'cleaning_iteration' not in st.session_state:
        st.session_state.cleaning_iteration = 0
    if 'data_values' not in st.session_state:
        st.session_state.data_values = []
    if 'output_history' not in st.session_state:
        st.session_state.output_history = []
    if 'latest_output' not in st.session_state:
        st.session_state.latest_output = ""
    if 'cleaning_finished' not in st.session_state:
        st.session_state.cleaning_finished = False

    if 'user_cluster_selections' not in st.session_state:
        st.session_state.user_cluster_selections = {}
    if 'cluster_index' not in st.session_state:
        st.session_state.cluster_index = None
    if 'cluster_columns' not in st.session_state:
        st.session_state.cluster_columns = []
    if 'cluster_columns_info' not in st.session_state:
        st.session_state.cluster_columns_info = []
    if 'inline_feedback' not in st.session_state:
        st.session_state.inline_feedback = {}

    # Add new session state variables for multi-cluster mapping
    if 'all_column_mappings' not in st.session_state:
        st.session_state.all_column_mappings = {}
    if 'all_column_feedback' not in st.session_state:
        st.session_state.all_column_feedback = {}
    if 'mappings_generated' not in st.session_state:
        st.session_state.mappings_generated = False

def main():
    """Main Streamlit application."""
    st.title("Data Clean Room Processor")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar with PepsiCo logo and navigation
    with st.sidebar:
        # PepsiCo logo
        st.image("PepsiCo_logo.png", width=200)
        st.markdown("---")
        
        # Navigation section
        st.markdown("### Navigation")
        st.markdown("Choose a step:")
        page = st.radio(
            "",
            [
                "Upload Files",
                "Column Analysis", 
                "Data Value Standardizer"
            ],
            index=["Upload Files", "Column Analysis", "Data Value Standardizer"].index(st.session_state.current_page.replace("📁 ", "").replace("🔍 ", "").replace("🥤 ", "")),
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Status section
        st.markdown("### Status:")
        
        # Dataset status
        if st.session_state.dataframes:
            dataset_count = len(st.session_state.dataframes)
            st.success(f"{dataset_count} dataset(s) loaded")
        else:
            st.info("No datasets loaded")
        
        # Analysis status
        if st.session_state.get('analysis_complete', False):
            st.success("Analysis complete")
        else:
            st.info("Analysis pending")
        
        # Data cleaning status
        if st.session_state.get('cleaning_finished', False):
            st.success("Data cleaned")
        else:
            st.info("Data cleaning pending")
    
    # Update current page based on selection
    if page == "Upload Files":
        current_page = "📁 Upload Files"
    elif page == "Column Analysis":
        current_page = "🔍 Column Analysis"  
    elif page == "Data Value Standardizer":
        current_page = "🥤 Data Value Standardizer"
    
    # Only update if page actually changed to prevent unnecessary reruns
    if st.session_state.current_page != current_page:
        st.session_state.current_page = current_page
        st.rerun()
    
    # Main content based on navigation
    if st.session_state.current_page == "📁 Upload Files":
        upload_files()
    
    elif st.session_state.current_page == "🔍 Column Analysis":
        if st.session_state.dataframes:
            # Always show analysis results (run if not already done)
            if not st.session_state.analysis_complete or not st.session_state.analysis_report:
                from column_analysis_page import analyze_columns
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
                    
                    # Create table-like structure with borders and styling
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
                    
                    /* Ensure proper alignment of multiselect widgets */
                    .stMultiSelect {
                        margin: 0 !important;
                        padding: 0 !important;
                        display: flex !important;
                        align-items: center !important;
                    }
                    
                    /* Align columns properly */
                    .stColumns {
                        align-items: center !important;
                    }
                    
                    /* Remove any extra spacing */
                    .stMultiSelect > div {
                        margin: 0 !important;
                        padding: 0 !important;
                    }
                    
                    /* Ensure column group labels and dropdowns are at same level */
                    .cluster-label {
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                        height: 40px !important;
                        margin: 0 !important;
                    }
                    
                    /* Force vertical alignment */
                    .stColumns > div {
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Start table container
                    st.markdown('<div class="cluster-table-container">', unsafe_allow_html=True)
                    
                    # Create table header
                    header_cols = st.columns([1] + [1] * len(file_names))
                    with header_cols[0]:
                        st.markdown('<div class="cluster-header" style="text-align: center;">Column Group</div>', unsafe_allow_html=True)
                    for i, filename in enumerate(file_names):
                        with header_cols[i+1]:
                            # Extract sheet name from filename if it contains " - "
                            if " - " in filename:
                                sheet_name = filename.split(" - ")[-1]
                                display_name = sheet_name
                            else:
                                display_name = filename
                            st.markdown(f'<div class="cluster-header">{display_name}</div>', unsafe_allow_html=True)
                    
                    # Display auto-generated clusters as rows
                    for i, cluster in enumerate(report['similarity_clusters']):
                        if len(cluster) > 1:  # Only show clusters with multiple columns
                            cluster_key = f"cluster_{i}"
                            if cluster_key not in st.session_state.user_cluster_selections:
                                st.session_state.user_cluster_selections[cluster_key] = cluster.copy()
                            
                            # Create row for this cluster
                            if len(file_names) <= 3:
                                # For 1-3 files, use equal spacing
                                col1, *file_cols = st.columns([1] + [1] * len(file_names))
                            else:
                                # For more files, use smaller widths to fit more columns
                                col1, *file_cols = st.columns([1] + [0.8] * len(file_names))
                            
                            with col1:
                                st.markdown(f'<div class="cluster-label">Column Group {i+1}</div>', unsafe_allow_html=True)
                            
                            # Group columns by file for this cluster
                            columns_by_file = {}
                            for col in cluster:
                                for filename, df in st.session_state.dataframes.items():
                                    if col in df.columns:
                                        if filename not in columns_by_file:
                                            columns_by_file[filename] = []
                                        columns_by_file[filename].append(col)
                                        break
                            
                            # Create dropdowns for each file
                            for j, filename in enumerate(file_names):
                                with file_cols[j]:
                                    file_columns = list(st.session_state.dataframes[filename].columns)
                                    current_selections = columns_by_file.get(filename, [])
                                    
                                    # Filter current selections to only include those in user_cluster_selections
                                    filtered_selections = [col for col in current_selections 
                                                         if col in st.session_state.user_cluster_selections[cluster_key]]
                                    
                                    selected_columns = st.multiselect(
                                        f"columns",
                                        options=sorted([col for col in file_columns if isinstance(col, str)]),
                                        default=filtered_selections,
                                        key=f"cluster_{i}_{filename}_analysis",
                                        label_visibility="collapsed"
                                    )
                                    
                                    # Update user selections for this cluster
                                    # Remove old selections for this file from this cluster
                                    st.session_state.user_cluster_selections[cluster_key] = [
                                        col for col in st.session_state.user_cluster_selections[cluster_key] 
                                        if col not in file_columns
                                    ]
                                    # Add new selections
                                    st.session_state.user_cluster_selections[cluster_key].extend(selected_columns)
                    
                    # Display custom clusters
                    if 'custom_clusters' not in st.session_state:
                        st.session_state.custom_clusters = []
                    
                    for i, custom_cluster in enumerate(st.session_state.custom_clusters):
                        custom_cluster_key = f"custom_cluster_{i}"
                        if custom_cluster_key not in st.session_state.user_cluster_selections:
                            st.session_state.user_cluster_selections[custom_cluster_key] = custom_cluster.copy()
                        
                        # Create row for custom cluster
                        if len(file_names) <= 3:
                            col1, *file_cols = st.columns([1] + [1] * len(file_names))
                        else:
                            col1, *file_cols = st.columns([1] + [0.8] * len(file_names))
                        
                        with col1:
                            st.markdown(f'<div class="cluster-label">Custom Group {i+1}</div>', unsafe_allow_html=True)
                        
                        # Create dropdowns for each file for custom cluster
                        for j, filename in enumerate(file_names):
                            with file_cols[j]:
                                file_columns = list(st.session_state.dataframes[filename].columns)
                                current_selections = [col for col in custom_cluster if col in file_columns]
                                
                                # Filter current selections to only include those in user_cluster_selections
                                filtered_selections = [col for col in current_selections 
                                                     if col in st.session_state.user_cluster_selections[custom_cluster_key]]
                                
                                selected_columns = st.multiselect(
                                    f"columns",
                                    options=sorted([col for col in file_columns if isinstance(col, str)]),
                                    default=filtered_selections,
                                    key=f"custom_cluster_{i}_{filename}_analysis",
                                    label_visibility="collapsed"
                                )
                                
                                # Update user selections for this custom cluster
                                # Remove old selections for this file from this cluster
                                st.session_state.user_cluster_selections[custom_cluster_key] = [
                                    col for col in st.session_state.user_cluster_selections[custom_cluster_key] 
                                    if col not in file_columns
                                ]
                                # Add new selections
                                st.session_state.user_cluster_selections[custom_cluster_key].extend(selected_columns)
                        
                        # Update the custom cluster with current selections
                        st.session_state.custom_clusters[i] = st.session_state.user_cluster_selections[custom_cluster_key].copy()
                    
                    # End table container
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Custom cluster creation section
                    from column_analysis_page import show_custom_cluster_creation
                    show_custom_cluster_creation(file_names)
                    
                    # Display column groups and generate button
                    from column_analysis_page import display_column_groups_and_generate_button
                    display_column_groups_and_generate_button()
        else:
            st.warning("Please upload files first.")
    
    elif st.session_state.current_page == "🥤 Data Value Standardizer":
        dedicated_data_cleaning_interface()

if __name__ == "__main__":
    main() 