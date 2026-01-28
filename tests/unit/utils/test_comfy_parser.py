import pytest
from genpulse.utils.comfy import parse_workflow_template, apply_params

def test_parse_simple_workflow():
    wf = {
        "3": {
            "class_type": "CLIPTextEncode", 
            "_meta": {"title": "INPUT_prompt"},
            "inputs": {"text": "default"}
        }
    }
    params = parse_workflow_template(wf)
    assert len(params) == 1
    assert params[0].name == "prompt"
    assert params[0].field_path == "text"

def test_parse_multiple_inputs():
    wf = {
        "1": {
            "class_type": "KSampler",
            "_meta": {"title": "INPUT_seed"},
            "inputs": {"seed": 123}
        },
        "2": {
            "class_type": "LoadImage",
            "_meta": {"title": "INPUT_image"},
            "inputs": {"image": "default.png"}
        }
    }
    params = parse_workflow_template(wf)
    assert len(params) == 2
    names = {p.name for p in params}
    assert "seed" in names
    assert "image" in names

def test_apply_params():
    wf = {
        "3": {
            "class_type": "CLIPTextEncode", 
            "_meta": {"title": "INPUT_prompt"},
            "inputs": {"text": "default"}
        }
    }
    schema = parse_workflow_template(wf)
    
    new_wf = apply_params(wf, {"prompt": "hello world"}, schema)
    assert new_wf["3"]["inputs"]["text"] == "hello world"
    # Original should not be modified
    assert wf["3"]["inputs"]["text"] == "default"
