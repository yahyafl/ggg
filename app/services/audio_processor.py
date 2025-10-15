import tempfile
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.services.gemini_client import client
from app.utils.json_helper import extract_json
from app.utils.validation import validate_order_json

executor = ThreadPoolExecutor()

async def process_audio_file(file_bytes: bytes) -> dict:
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_audio:
        temp_audio.write(file_bytes)
        temp_path = temp_audio.name

    try:
        # Upload audio
        uploaded_audio = client.files.upload(file=temp_path)

        full_prompt = [
            uploaded_audio,
           """
            Transcribe this audio and translate to English. 
            Then apply these detailed extraction rules:
            You are a precise JSON extractor.
            Extract the following fields from the user's text and return ONLY valid JSON (no explanations, no extra text).

            Rules:
            1. action:
                - "buy" if the user intends to purchase, acquire, or go long.
                - "sell" if the user intends to dispose, offload, or go short.
                - Always lowercase ("buy" or "sell").

            2. share_name:
                - Extract the stock, ticker, or company symbol (e.g., NBK, AAPL, TSLA).
                - Use uppercase letters only.
                - If multiple shares are mentioned, extract only the first one.
                - This field can’t be null.

            3. order_type:
                - "limit" if the user explicitly says "limit" or mentions a price.
                - "market" if the user explicitly says "market" or no price is mentioned.

            4. price:
                - Extract the numeric price (float) if mentioned.
                - Use null if no price is mentioned or if order_type is "market".

            5. quantity:
                - Extract the integer number of units, shares, or items.
                - This field can’t be null.

            6. order_duration:
                - Infer from the user’s language:
                    • "today" if they imply a short-term action (e.g., "today", "right now", "execute immediately").
                    • "gtc" (good till cancelled) if they imply persistence (e.g., "keep it", "until canceled", "open until executed").
                    • "gtd" (good till date) if they specify a date or phrase like "until Friday" (Don't extract the date).
                - If unclear, use null.

            7. Always output clean JSON in this format:
            {
                "action": "buy or sell",
                "share_name": "string",
                "order_type": "market or limit",
                "price": float or null,
                "quantity": integer,
                "order_duration": "today" | "gtc" | "gtd" | null
                                        }
            """
        ]

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(executor, lambda: client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        ))

        raw_text = getattr(response, "text", "")
        result = extract_json(raw_text)

        if validate_order_json(result):
            return result

        # Retry
        correction_prompt = f"""
        The previous extraction was invalid.
        Problem details: {result}
        Rules reminder:
        - order_type = "limit" if price is mentioned, else "market"
        - price must be float or null
        - quantity must be integer > 0
        - order_duration = today | gtc | gtd | null
        Correct only the invalid fields and return valid JSON.
        """

        retry = await loop.run_in_executor(executor, lambda: client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=correction_prompt
        ))

        retry_json = extract_json(getattr(retry, "text", ""))
        if validate_order_json(retry_json):
            return retry_json

        return {"error": "Validation failed", "raw_output": getattr(retry, "text", "")}

    finally:
        os.remove(temp_path)
