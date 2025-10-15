import json

def extract_json(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    json_start = raw_text.find("{")
    json_end = raw_text.rfind("}") + 1

    if json_start == -1 or json_end == -1:
        return {"error": "no_json_found", "raw_output": raw_text}

    try:
        return json.loads(raw_text[json_start:json_end])
    except json.JSONDecodeError:
        return {"error": "invalid_json", "raw_output": raw_text}
