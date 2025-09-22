import streamlit as st
import pandas as pd

def upload_files():
    """Handle file upload with Excel sheet selection."""
    st.header("Upload Data Files")
    
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=['csv', 'xlsx', 'xls'],
        accept_multiple_files=True,
        help="Upload CSV or Excel files. For Excel files, you can select specific sheets."
    )
    
    if uploaded_files:
        dataframes = {}
        excel_sheets = {}
        
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            
            try:
                if file_name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    dataframes[file_name] = df
                    st.success(f"Successfully loaded {file_name}")
                
                elif file_name.endswith(('.xlsx', '.xls')):
                    # Get available sheets
                    excel_file = pd.ExcelFile(uploaded_file)
                    available_sheets = excel_file.sheet_names
                    print(f'available_sheets: {available_sheets}')
                    if len(available_sheets) > 1:
                        st.write(f"**{file_name}** has multiple sheets:")
                        selected_sheets = st.multiselect(
                            f"Select sheets to import from {file_name}",
                            sorted(available_sheets),
                            default=sorted(available_sheets)[:1],
                            key=f"sheets_{file_name}"
                        )
                        
                        for sheet_name in selected_sheets:
                            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                            full_name = f"{file_name} - {sheet_name}"
                            dataframes[full_name] = df
                            st.success(f"Loaded {full_name}: {df.shape[0]} rows, {df.shape[1]} columns")
                    else:
                        df = pd.read_excel(uploaded_file)
                        dataframes[file_name] = df
                        st.success(f"Loaded {file_name}: {df.shape[0]} rows, {df.shape[1]} columns")
            
            except Exception as e:
                st.error(f"Error loading {file_name}: {e}")
        
        if dataframes:
            st.session_state.dataframes = dataframes
            
            # Show dataset summary
            st.subheader("Dataset Summary")
            summary_data = []
            for filename, df in dataframes.items():
                summary_data.append({
                    'Dataset': filename,
                    'Rows': df.shape[0],
                    'Columns': df.shape[1],
                    'Memory Usage': f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
            
            # Store output for preservation
            st.session_state.upload_output = {
                'datasets_loaded': len(dataframes),
                'summary': summary_data,
                'filenames': list(dataframes.keys())
            }
            
            # Navigation button
            st.divider()
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("Continue to Column Analysis", type="primary"):
                    # Import analyze_columns from column_analysis_page
                    from column_analysis_page import analyze_columns
                    analyze_columns()
                    st.session_state.current_page = "🔍 Column Analysis"
                    st.rerun()
            
            return True
    
    return False 