from deep_translator import GoogleTranslator

def translate_text(text: str, dest_lang: str = "en"):
    """Translate text to the target language (default = English)."""
    if not text:
        return {"error": "No text provided"}
    
    try:
        translated = GoogleTranslator(source="auto", target=dest_lang).translate(text)
        return {
            "original": text,
            "translated": translated,
            "dest_lang": dest_lang
        }
    except Exception as e:
        return {"error": str(e)}