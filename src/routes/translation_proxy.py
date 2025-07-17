from flask import Blueprint, request, jsonify
from easygoogletranslate import EasyGoogleTranslate
import logging

translation_proxy_bp = Blueprint('translation_proxy', __name__)

@translation_proxy_bp.route('/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    text = data.get('text')
    target_lang = data.get('target_lang')

    logging.info(f"Received translation request: text='{text}', target_lang='{target_lang}'")

    if not text or not target_lang:
        logging.error("Missing text or target_lang in request")
        return jsonify({"error": "Text and target_lang are required"}), 400

    try:
        translator = EasyGoogleTranslate(target_lang)
        translated_text = translator.translate(text)
        logging.info(f"Translation successful: {translated_text}")
        return jsonify({"translatedText": translated_text})
    except Exception as e:
        logging.error(f"Translation API error: {str(e)}")
        return jsonify({"error": f"Translation API error: {str(e)}"}), 502
