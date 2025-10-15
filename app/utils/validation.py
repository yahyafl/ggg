def validate_order_json(data: dict) -> bool:
    required_fields = ["action", "share_name", "order_type", "price", "quantity", "order_duration"]
    valid_actions = {"buy", "sell"}
    valid_order_types = {"market", "limit"}
    valid_durations = {"today", "gtc", "gtd", None}

    try:
        if not all(field in data for field in required_fields): return False
        if data["action"] not in valid_actions: return False
        if not isinstance(data["share_name"], str) or not data["share_name"].isupper(): return False
        if data["order_type"] not in valid_order_types: return False
        if data["price"] is not None and not isinstance(data["price"], (int, float)): return False
        if not isinstance(data["quantity"], int) or data["quantity"] <= 0: return False
        if data["order_duration"] not in valid_durations: return False
        if data["order_type"] == "market" and data["price"] is not None: return False
        if data["order_type"] == "limit" and not isinstance(data["price"], (int, float)): return False
        return True
    except Exception:
        return False
