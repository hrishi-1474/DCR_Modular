# DCR Modular - Data Clean Room Processor (Modularized)

This is the modularized version of the Data Clean Room Processor application, organized into logical, maintainable modules.

## 📁 File Structure

```
DCR_Modular/
├── main_app.py                 # 🎯 Main orchestrator - run this file
├── llm_backend.py             # 🤖 LLM-related functions and utilities
├── data_processor.py          # 📊 Data processing and analysis functions
├── upload_page.py             # 📤 Upload Files page functionality
├── column_analysis_page.py    # 🔍 Column Analysis page functionality
├── data_standardizer_page.py  # 🥤 Data Value Standardizer page functionality
├── requirements.txt           # 📋 Python dependencies
├── llm_keys.yaml             # 🔑 API keys configuration
└── README.md                 # 📖 This file
```

## 🚀 How to Run

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys:**
   - Edit `llm_keys.yaml` to add your OpenAI API key
   - Format: `open_ai: "your-api-key-here"`

3. **Run the Application:**
   ```bash
   streamlit run main_app.py
   ```

## 🧩 Module Overview

### 1. **main_app.py** - Main Orchestrator
- **Purpose**: Entry point and navigation controller
- **Contains**: Page routing, session state management, CSS styling
- **Imports**: All page modules and coordinates their execution

### 2. **llm_backend.py** - LLM Backend
- **Purpose**: All LLM-related functionality
- **Contains**:
  - LLM initialization and configuration
  - API calling functions (`call_llm`, `call_llm_json`, `call_llm_parallel`)
  - Response processing (`process_llm_response`)
  - Prompt templates (`initial_prompt_template`, `refinement_prompt_template`)
  - Utility functions (`count_tokens`, `clean_brand_name`, `clean_invalid_escapes`)

### 3. **data_processor.py** - Data Processing
- **Purpose**: Data analysis and mapping generation
- **Contains**:
  - Column analysis functions (`calculate_column_group_summary`)
  - Summary generation (`generate_column_groups_summary_table`)
  - Mapping functions (`generate_mappings_for_all_columns`, `process_feedback_for_all_columns`)
  - Statistics calculation (`calculate_standardization_stats`)

### 4. **upload_page.py** - Upload Functionality
- **Purpose**: File upload and dataset loading
- **Contains**:
  - Multi-file upload handling
  - Excel sheet selection
  - Dataset validation and summary
  - Navigation to Column Analysis

### 5. **column_analysis_page.py** - Column Analysis
- **Purpose**: LLM-based column clustering and analysis
- **Contains**:
  - Automatic column analysis (`analyze_columns`)
  - LLM-based clustering (`llm_based_column_clustering`)
  - Interactive cluster customization
  - Mapping generation triggers

### 6. **data_standardizer_page.py** - Data Standardization
- **Purpose**: Data cleaning interface and Excel output
- **Contains**:
  - Interactive mapping tables
  - Feedback collection and processing
  - Iterative refinement workflow
  - Excel file generation and download

## 🔧 Key Benefits of Modularization

### ✅ **Maintainability**
- Each module has a single, clear responsibility
- Easy to locate and modify specific functionality
- Reduced code duplication

### ✅ **Scalability**
- New features can be added as separate modules
- Easy to extend existing functionality
- Clear separation of concerns

### ✅ **Testing**
- Individual modules can be tested independently
- Easier to write unit tests for specific functions
- Better error isolation

### ✅ **Collaboration**
- Multiple developers can work on different modules
- Clear interfaces between components
- Reduced merge conflicts

### ✅ **Reusability**
- Functions can be imported and used across modules
- Backend functions can be used in other applications
- Easy to create command-line versions

## 🔄 Migration from Original

### **What Changed:**
- Split `streamlit_app.py` into 6 focused modules
- Organized functions by purpose and responsibility
- Maintained exact same functionality and behavior
- Added proper import statements and dependencies

### **What Stayed the Same:**
- All function logic and algorithms
- User interface and workflow
- Session state management
- LLM integration and prompts
- Excel output generation

## 🛠 Development Guidelines

### **Adding New Features:**
1. Determine which module the feature belongs to
2. Add the function to the appropriate module
3. Update imports in files that need the new feature
4. Test the new functionality

### **Modifying Existing Features:**
1. Locate the function in its respective module
2. Make changes while maintaining the function signature
3. Update any dependent functions if needed
4. Test across all affected pages

### **Creating New Pages:**
1. Create a new page module (e.g., `new_page.py`)
2. Import it in `main_app.py`
3. Add navigation logic in the main app
4. Update session state initialization if needed

## 📝 Notes

- **Backwards Compatible**: The modular version provides exactly the same functionality as the original
- **Performance**: No performance impact from modularization
- **Dependencies**: Same requirements as the original application
- **Configuration**: Uses the same `llm_keys.yaml` file format

## 🚨 Important

Make sure to run the application from the `DCR_Modular` directory so that all imports work correctly:

```bash
cd DCR_Modular
streamlit run main_app.py
``` 