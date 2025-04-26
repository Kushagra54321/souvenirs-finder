from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# Gemini AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")



@app.route('/get_souvenirs', methods=['POST'])
def get_souvenirs():
    data = request.json
    # destination = data.get("destination", "").strip()
    user_input = data.get("destination", "").strip()
    place_match = re.search(r"(?:in|from|at|for)?\s*([a-zA-Z\s]+)", user_input, re.IGNORECASE)
    clean_destination = place_match.group(1).strip() if place_match else user_input
    
    # ❌ Check for numbers, mathematical symbols, or invalid inputs
    # if not destination or re.search(r'\d|\+|\-|\*|\/|=|add|subtract|multiply|divide', destination, re.IGNORECASE):
    #     return jsonify({"error": "❌ I’m designed to help with travel destinations only. Please enter a valid place name."})

    try:
        # ✅ Check with OpenCage API for valid location
        location_url = f"https://api.opencagedata.com/geocode/v1/json?q={clean_destination}&key={OPENCAGE_API_KEY}"
        location_res = requests.get(location_url).json()

        if not location_res["results"]:
            return jsonify({"error": "❌ I couldn’t find this location. Please try another travel destination."})

        # ✅ Location info
        loc_data = location_res["results"][0]
        location_info = {
            "formatted": loc_data["formatted"],
            "lat": loc_data["geometry"]["lat"],
            "lng": loc_data["geometry"]["lng"],
            "map_link": f"https://www.google.com/maps?q={loc_data['geometry']['lat']},{loc_data['geometry']['lng']}"
        }

        # ✅ Souvenir suggestion
        prompt = f"""
            You're an expert travel guide. A user asked: '{user_input}'.
            Give 3 unique and popular souvenir suggestions for this place.
                Also provide cultural relevance or fun facts if available.""".strip()
        ai_response = model.generate_content(prompt)
        souvenirs = ai_response.text.strip()

        # ✅ Get image from Unsplash
        image_url = f"https://api.unsplash.com/search/photos?query={clean_destination }&client_id={UNSPLASH_ACCESS_KEY}&per_page=3"
        image_res = requests.get(image_url).json()
        image_links = [img["urls"]["regular"] for img in image_res.get("results", [])]

        return jsonify({
            "souvenirs": souvenirs,
            "location": location_info,
            "images": image_links
        })

    except Exception as e:
        return jsonify({"error": f"Something went wrong: {str(e)}"})



if __name__ == '__main__':
    app.run(debug=True)
