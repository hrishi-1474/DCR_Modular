import streamlit as st
import json
import os
import re
import yaml
from langchain_openai import ChatOpenAI
import tiktoken

# --- Load API key from YAML ---
try:
    with open("llm_keys.yaml", "r") as file:
        os.environ["OPENAI_API_KEY"] = st.secrets["open_ai"]
except Exception as e:
    st.error(f"Error loading API key: {e}")
    st.info("Please create a 'llm_keys.yaml' file with your OpenAI API key")

# --- Initialize LangChain LLM ---
try:
    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0, top_p=1)
except Exception as e:
    st.error(f"Error initializing LLM: {e}")
    llm = None

def initialize_llm_processor():
    """Initialize the LLM processor."""
    if llm is None:
        st.error("LLM not initialized. Please check your API key configuration.")
        return None
    return llm

# --- LLM Call Functions ---
def call_llm(prompt):
    if llm is None:
        return "Error: LLM not initialized"
    try:
        return llm.predict(prompt).strip()
    except Exception as e:
        return f"Error calling LLM: {e}"


def call_llm_parallel(prompt, column_id):
    """Call LLM with error handling and column ID tracking for parallel processing."""
    try:
        # Use invoke to get token information
        response = llm.invoke(prompt)
        result = response.content
        
        # Get token information from response metadata
        if hasattr(response, 'response_metadata') and response.response_metadata:
            metadata = response.response_metadata
            if 'token_usage' in metadata:
                completion_tokens = metadata['token_usage'].get('completion_tokens', 0)
                prompt_tokens = metadata['token_usage'].get('prompt_tokens', 0)
                total_tokens = metadata['token_usage'].get('total_tokens', 0)
                print(f"🔢 Token Usage for {column_id}:")
                print(f"   Prompt tokens: {prompt_tokens}")
                print(f"   Completion tokens: {completion_tokens}")
            else:
                print(f"⚠️ No token usage info available for {column_id}")
        else:
            print(f"⚠️ No response metadata available for {column_id}")
        
        return column_id, result, None
    except Exception as e:
        return column_id, None, str(e)

def process_llm_response(output, column_id):
    """Process LLM response and extract simple key-value mappings."""
    try:
        # Clean the output
        cleaned_output = output.strip()
        
        # First try to parse as simple key-value format
        mappings = []
        lines = cleaned_output.split('\n')
        
        for line in lines:
            line = line.strip()
            if '=' in line:
                parts = line.split('=', 1)  # Split on first = only
                if len(parts) == 2:
                    original, canonical = parts[0].strip(), parts[1].strip()
                    if original and canonical:
                        mappings.append({
                            "Brand Name": original,
                            "Classified As": canonical
                        })
        
        # If we found mappings in simple format, return the original cleaned output
        if mappings:
            return cleaned_output
        
        # Fallback: try to parse as JSON (for backward compatibility)
        try:
            # Try to find JSON array in the response
            json_match = re.search(r'\[.*\]', cleaned_output, re.DOTALL | re.MULTILINE)
            if json_match:
                parsed_output = json_match.group()
                json.loads(parsed_output)  # Validate
                return parsed_output
        except:
            pass
        
        # If all parsing fails, return error message
        return f"Error: Could not parse response for {column_id}. Expected format: original_name=canonical_name"
            
    except Exception as e:
        st.warning(f"Failed to parse response for {column_id}: {e}")
        return f"Error: {str(e)}"

# --- Prompt Templates ---
def initial_prompt_template(data_values):
    # Convert list to space-separated string for token efficiency
    brand_names_text = " ".join([f'"{name}"' for name in data_values])
    
    return f"""You are an expert in cleaning and deduplicating product brand names in retail data.

Below is a list of {len(data_values)} brand names extracted from different data sources. These names may vary due to typos, prefixes/suffixes (e.g., "U-", "C-", version numbers), formatting inconsistencies, or minor descriptive additions.

Your task is to:
1. Identify brand names that likely refer to the same brand.
2. Group such similar names together under a shared 'canonical' brand name.
3. The canonical name must be selected from the provided variants — ideally the most commonly used or recognizable form.

CRITICAL REQUIREMENTS:
- You MUST return exactly {len(data_values)} mappings (one for each input value).
- Every input brand name must appear exactly once in the output.
- Every provided brand name must be included under some group (even if standalone).
- Do not add extra mappings or skip any input values.
- Do not invent new brand names not in the original brand name list.
- Use format: original_name=canonical_name
- One mapping per line
- No extra text, quotes, or formatting
- Every provided brand name must be included under some group (even if standalone).


Brand names: {brand_names_text}

Return the output strictly in the following format:

**Output format**:
GATORADE 5V5=GATORADE
PEPSI MAX=PEPSI
COCA COLA ZERO=COCA COLA

"""

def refinement_prompt_template(prev_classification, feedback):
    return f"""
You previously classified brand names as follows:
{prev_classification}

A human reviewer has suggested the following refinements:
{feedback}

Your task is to:
- Apply the human feedback carefully to improve classification.
- Update the brand name mappings based on the human feedback provided.
- you may also apply the same change (or a consistent pattern) to other brand names that are: Lexically similar or 
  Follow a similar naming pattern
- Ensure all brand names are still classified under a canonical name from the list.

CRITICAL REQUIREMENTS:
- You MUST return exactly the same number of mappings as the previous classification.
- Every input brand name must appear exactly once in the output.
- Use format: original_name=canonical_name
- One mapping per line
- No extra text or formatting
- Do not add extra mappings or skip any input values.
- Do not invent new brand names not in the original list.

Return the output strictly in the following format:

**Output format**:
GATORADE 5V5=GATORADE
PEPSI MAX=PEPSI
COCA COLA ZERO=COCA COLA"""

# --- Utility Functions ---

def clean_invalid_escapes(s: str) -> str:
    # Replace any backslash not followed by a valid JSON escape
    return re.sub(r'\\(?![\\/"bfnrtu])', r'\\\\', s)

def clean_brand_name(name: str) -> str:
    """Clean brand names by removing invalid backslashes and normalizing whitespace."""
    if not isinstance(name, str):
        return name
    
    # Replace invalid backslashes: keep only valid escapes
    # Valid ones in JSON: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
    name = re.sub(r'\\(?![\\/"bfnrtu])', r'\\\\', name)
    
    # Optionally: collapse multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name 
