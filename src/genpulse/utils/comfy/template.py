import json
import os
from typing import Dict, Any
from genpulse import config

# Basic caching for templates
_TEMPLATE_CACHE = {}

def load_template(template_name: str) -> Dict[str, Any]:
    """
    Load a ComfyUI workflow template by name (e.g., 'sdxl_t2i').
    Looks for files in src/genpulse/templates/comfy/{name}.json
    """
    if template_name in _TEMPLATE_CACHE:
        return _TEMPLATE_CACHE[template_name]
        
    # Construct base path relative to project root or use an env var
    # Assuming code layout: src/genpulse/utils/comfy/template.py
    # Templates at: src/genpulse/templates/comfy/
    
    # We can use a relative path lookup
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # base_dir is now src/genpulse
    template_path = os.path.join(base_dir, "templates", "comfy", f"{template_name}.json")
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"ComfyUI Template not found: {template_path}")
        
    with open(template_path, 'r') as f:
        data = json.load(f)
        _TEMPLATE_CACHE[template_name] = data
        return data

# We can also move apply_simple_params here if we want a simpler logic than the complex INPUT_ one
def apply_simple_params(workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple replacement: Just loops through params and replaces if keys match INPUT_ convention.
    """
    # ... logic handled by core.apply_params mainly
    return workflow
