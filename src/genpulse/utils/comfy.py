from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class WorkflowParam(BaseModel):
    name: str
    node_id: str
    field_path: str
    type: str # string, int, float, image_url
    default: Any = None
    description: str = ""

def parse_workflow_template(workflow: Dict[str, Any]) -> List[WorkflowParam]:
    """
    Parses a ComfyUI API-JSON workflow.
    Identifies dynamic parameters based on Node Titles or explicit marking conventions.
    
    Convention:
    Edit the Node Title in ComfyUI (Right click -> Title).
    If Title starts with 'INPUT_<NAME>', the primary widget of that node becomes a variable.
    
    Example:
    Node 3 (CLIPTextEncode) Title: "INPUT_prompt"
    -> Variable "prompt" maps to Node 3's "text" input.
    """
    params = []
    
    # Mapping of Node Class -> Primary Input Field
    PRIMARY_FIELDS = {
        "CLIPTextEncode": "text",
        "KSampler": "seed",
        "LoadImage": "image",
        "EmptyLatentImage": ["width", "height"], # Special case
        "PrimitiveNode": "value", # If using primitive nodes
    }
    
    for node_id, node in workflow.items():
        meta = node.get("_meta", {})
        title = meta.get("title", "")
        class_type = node.get("class_type")
        
        # Check convention
        if title.startswith("INPUT_"):
            var_name = title[len("INPUT_"):].lower()
            
            # Determine which field to map
            # 1. First check generic primary field map
            target_fields = []
            
            if class_type in PRIMARY_FIELDS:
                val = PRIMARY_FIELDS[class_type]
                if isinstance(val, list):
                    # For things like Width/Height, we might create multiple params
                    # strict: INPUT_width, INPUT_height? Or specialized logic.
                    # Let's keep it simple: if INPUT_dimensions, expose width/height?
                    # For now, simplistic mapping.
                    target_fields = val
                else:
                    target_fields = [val]
            else:
                # Fallback: try common names
                if "text" in node.get("inputs", {}):
                    target_fields = ["text"]
                elif "seed" in node.get("inputs", {}):
                    target_fields = ["seed"]
            
            for field in target_fields:
                if field not in node.get("inputs", {}):
                    continue
                    
                current_val = node["inputs"][field]
                final_var_name = var_name
                
                # Special handling for multi-field nodes
                if len(target_fields) > 1:
                    final_var_name = f"{var_name}_{field}"
                
                params.append(WorkflowParam(
                    name=final_var_name,
                    node_id=node_id,
                    field_path=field,
                    type=type(current_val).__name__,
                    default=current_val,
                    description=f"Mapped from Node {node_id} ({class_type})"
                ))
                
    return params

def apply_params(workflow: Dict[str, Any], params_map: Dict[str, Any], schema: List[WorkflowParam]) -> Dict[str, Any]:
    """
    Injects values into the workflow based on the schema and provided params.
    Returns a new workflow dict ready for execution.
    """
    import copy
    wf = copy.deepcopy(workflow)
    
    for param in schema:
        if param.name in params_map:
            val = params_map[param.name]
            # Type casting if needed could go here
            if node := wf.get(param.node_id):
                node["inputs"][param.field_path] = val
                
    return wf
