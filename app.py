"""Swad Yatra Python backend.

Run locally with:  python app.py
Deploy with:       gunicorn app:app
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
SUBMISSIONS_FILE = DATA_DIR / "submissions.json"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder="public", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 150 * 1024 * 1024
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "webm", "m4v"}

IMAGE = "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=1400&q=85"


def recipe(slug, name, region, locality, community, about, ingredients, procedure,
           benefits, calories, protein, restaurant, *, image=IMAGE, time_to_make="45 min",
           difficulty="Home kitchen"):
    """Keep the heritage collection readable while giving every dish a complete page."""
    return {
        "id": slug, "name": name, "region": region, "locality": locality,
        "community": community, "about": about, "ingredients": ingredients,
        "procedure": procedure, "benefits": benefits, "calories": calories,
        "protein": protein, "restaurant": restaurant, "map": locality,
        "image": image, "videoQuery": f"{name} {region} recipe", "videoUrl": None,
        "time": time_to_make, "difficulty": difficulty,
    }


RECIPES = [
    recipe("bhatt-ki-churkani", "Bhatt ki Churkani", "Uttarakhand", "Almora, Kumaon", "Kumaoni", "An earthy slow-cooked black soybean curry once central to Kumaoni winter kitchens.", ["Bhatt / black soybeans", "Jakhya or cumin", "Tomato", "Garlic", "Turmeric", "Mustard oil"], ["Soak bhatt overnight and pressure-cook until tender.", "Temper jakhya, garlic and tomato in mustard oil.", "Crush a handful of beans for body and simmer with spices."], "Warming, high-fibre mountain food rich in plant protein and iron.", "286 kcal", "21 g", "Kumaoni Kothi", image="https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=1400&q=85"),
    recipe("patrode", "Patrode", "Karnataka", "Udupi, Coastal Karnataka", "Tuluva", "Colocasia leaves folded around a spiced rice-and-lentil paste, treasured during the coastal monsoon.", ["Colocasia leaves", "Rice", "Toor dal", "Coconut", "Tamarind", "Byadgi chilli"], ["Soak rice and dal, then grind with coconut and tamarind.", "Spread paste over washed leaves and stack them.", "Roll, steam, slice and temper."], "Leafy, filling and naturally gluten-free.", "224 kcal", "7 g", "Mitra Samaj, Udupi", time_to_make="1 hr 10 min", difficulty="Patient steaming"),
    recipe("bhanjari", "Bhanjari Ghosht", "Rajasthan", "Nagaur, Marwar", "Banjara", "A rustic travelling-community mutton curry seasoned simply and cooked patiently over embers.", ["Mutton", "Dried red chillies", "Onion", "Garlic", "Coriander seed", "Ghee"], ["Brown mutton in ghee with spices.", "Add onions, garlic and chillies.", "Add minimal water and braise until tender."], "Protein-dense and sustaining for desert evenings.", "412 kcal", "29 g", "Bhanwar Niwas Kitchen, Nagaur", time_to_make="1 hr 30 min", difficulty="Slow braise"),
    recipe("kodbel", "Kodbel", "Odisha", "Kandhamal", "Kondh", "A gentle tribal millet porridge made with forest greens, once a daily source of strength in hill villages.", ["Finger millet", "Forest greens or spinach", "Pumpkin", "Garlic", "Salt"], ["Cook millet in water until soft.", "Add pumpkin and greens.", "Finish with pounded garlic and salt."], "Calcium-rich, high in fibre and gentle on blood sugar.", "198 kcal", "6 g", "Desia Kitchen, Koraput", time_to_make="40 min", difficulty="One-pot"),
    recipe("tungrymbai", "Tungrymbai", "Meghalaya", "Shillong, Khasi Hills", "Khasi", "Fermented soybean is cooked with black sesame and local herbs—an intensely savoury Khasi comfort food.", ["Fermented soybean", "Pork optional", "Black sesame", "Ginger", "Garlic", "Green chilli"], ["Pound fermented beans to a coarse paste.", "Render pork with ginger, garlic and chilli.", "Stir in beans and sesame, then cook gently."], "Fermented soy brings protein, fibre and a deep food tradition.", "310 kcal", "18 g", "Tribal Kitchen, Shillong", time_to_make="50 min", difficulty="Fermented flavours"),
    recipe("gudila", "Gudila", "Chhattisgarh", "Bastar", "Maria Gond", "Soft hand-rolled rice dumplings cooked with greens, a quiet Bastar household recipe.", ["Rice flour", "Amaranth greens", "Onion", "Green chilli", "Coriander"], ["Knead rice flour with warm water.", "Stuff discs with chopped seasoned greens.", "Steam until tender and translucent."], "A low-fat steamed meal with greens and complex carbohydrates.", "205 kcal", "5 g", "Bastar Art Cafe, Jagdalpur", time_to_make="35 min", difficulty="Easy"),
    recipe("chilra", "Chilra", "Bihar", "Mithila, Darbhanga", "Maithil", "A humble fermented rice-and-urad pancake, traditionally served with sharp tomato chutney.", ["Rice", "Urad dal", "Ginger", "Green chilli", "Mustard oil"], ["Soak and grind rice and dal into a batter.", "Rest with ginger and chilli.", "Cook on an iron griddle until crisp at the edges."], "Rice and lentils together provide complete amino acids.", "165 kcal", "6 g", "Mithila Haat Kitchen, Darbhanga", time_to_make="25 min", difficulty="Quick griddle"),
    recipe("gahat-rasmi", "Gahat Rasmi Badi", "Himachal Pradesh", "Kullu Valley", "Pahari", "Sun-dried horsegram dumplings in a tangy yoghurt gravy—an old way to preserve protein for snowy months.", ["Horsegram badi", "Yoghurt", "Coriander seed", "Turmeric", "Ghee", "Mint"], ["Rinse dried badis and lightly fry in ghee.", "Whisk yoghurt with spices.", "Simmer badis in gravy and finish with mint."], "Horsegram is prized for fibre, iron and slow-release energy.", "248 kcal", "14 g", "Himachali Rasoi, Manali", time_to_make="55 min", difficulty="Comforting"),
    recipe("koldil-bhaji", "Koldil Bhaji", "Assam", "Majuli", "Mishing", "Banana flower sautéed with roasted sesame and potato, a low-waste river-island dish.", ["Banana flower", "Potato", "Black sesame", "Mustard oil", "Green chilli", "Lime"], ["Clean and finely chop banana flower.", "Cook potato, then add flower.", "Fold through pounded sesame and finish with lime."], "Banana flower is fibre-rich; sesame adds calcium.", "176 kcal", "5 g", "La Maison de Ananda, Majuli", time_to_make="35 min", difficulty="Everyday"),
    recipe("saanp-kharta", "Saanp Kharta", "Goa", "Canacona", "Kunbi", "A smoky brinjal-and-coconut mash with kokum, recalling pre-tourism Goan village kitchens.", ["Brinjal", "Fresh coconut", "Kokum", "Green chilli", "Onion", "Coconut oil"], ["Roast whole brinjal until charred.", "Peel and mash with coconut, chilli and onion.", "Stir in kokum and coconut oil."], "Plant-based, fibre-rich and full of protective anthocyanins.", "190 kcal", "4 g", "The Village, Cavelossim", time_to_make="30 min", difficulty="Rustic mash"),
    recipe("dubu", "Dubu", "Jharkhand", "Ranchi Plateau", "Munda", "A thick, nourishing rice-and-lentil stew made for communal Munda meals.", ["Rice", "Mixed lentils", "Pumpkin", "Spinach", "Turmeric", "Mustard oil"], ["Wash rice and lentils together.", "Cook with pumpkin and turmeric until soft.", "Add greens and a mustard-oil tempering."], "Balanced grains and lentils make a protein-rich complete meal.", "272 kcal", "11 g", "Aadivasi Kitchen, Ranchi", time_to_make="50 min", difficulty="One-pot"),
    recipe("khambir", "Khambir", "Ladakh", "Leh", "Ladakhi", "A thick, fermented whole-wheat bread with a crisp hearth and soft centre, built for high-altitude days.", ["Whole wheat flour", "Yeast or starter", "Salt", "Water", "Wheat bran"], ["Mix a slack whole-wheat dough and let it rise.", "Shape a thick round and prick it.", "Bake on a hot griddle or stone."], "Whole grains offer lasting energy, fibre and B vitamins.", "230 kcal", "8 g", "Lamayuru Restaurant, Leh", time_to_make="2 hr", difficulty="Baking"),
    recipe("paaya-shorba", "Paaya Shorba", "Telangana", "Hyderabad Old City", "Deccani", "An old Deccani bone broth simmered overnight with wheat and fragrant spices.", ["Lamb trotters", "Wheat", "Onion", "Ginger", "Cinnamon", "Coriander"], ["Clean trotters and cook until gelatinous.", "Cook wheat until soft.", "Combine with fried onion, spices and broth."], "Naturally rich in collagen and protein.", "335 kcal", "24 g", "Shadab, Hyderabad", time_to_make="4 hr", difficulty="Slow simmer"),
    recipe("hareli-bhaji", "Hareli Bhaji", "Madhya Pradesh", "Mandla", "Baiga", "A foraged mixed-green stir fry celebrating the Hareli monsoon festival.", ["Mixed seasonal greens", "Garlic", "Red chilli", "Mustard oil", "Roasted peanuts"], ["Wash and chop tender greens.", "Bloom garlic and chilli in mustard oil.", "Toss greens briefly and top with peanuts."], "A concentrated source of micronutrients, fibre and antioxidants.", "132 kcal", "6 g", "Baiga Rasoi, Mandla", time_to_make="28 min", difficulty="Seasonal"),
    recipe("phagshapa", "Phagshapa", "Sikkim", "Gangtok", "Bhutia", "Pork belly braised with daikon and dried red chillies, a soulful Himalayan winter dish.", ["Pork belly", "Daikon radish", "Dried red chillies", "Ginger", "Salt"], ["Blanch and cut pork.", "Simmer with ginger and whole chillies.", "Add daikon and cook until tender."], "Protein and iron from pork are balanced by vitamin-C-rich daikon.", "398 kcal", "25 g", "Taste of Tibet, Gangtok", time_to_make="1 hr", difficulty="Slow stew"),
    recipe("puchakaai-kootu", "Puchakaai Kootu", "Tamil Nadu", "Chettinad, Karaikudi", "Nagarathar", "A forgotten ash-gourd and lentil kootu scented with coconut, mild and elegant beside Chettinad heat.", ["Ash gourd", "Moong dal", "Coconut", "Cumin", "Curry leaves", "Turmeric"], ["Cook moong dal and ash gourd.", "Grind coconut and cumin.", "Fold into the pot and temper with curry leaves."], "Hydrating ash gourd and light moong are easy to digest.", "168 kcal", "8 g", "The Bangala, Karaikudi", time_to_make="45 min", difficulty="Gentle simmer"),
    recipe("chak-hao-kheer", "Chak-Hao Kheer", "Manipur", "Imphal Valley", "Meitei", "Purple-black aromatic rice slowly sweetened with milk, a ceremonial Meitei dessert.", ["Chak-hao black rice", "Milk", "Jaggery", "Cardamom", "Nuts"], ["Soak black rice and simmer in milk.", "Stir until grains bloom and milk reduces.", "Sweeten with jaggery and finish with cardamom."], "Black rice contains anthocyanin antioxidants and extra fibre.", "268 kcal", "7 g", "Luxmi Kitchen, Imphal", time_to_make="55 min", difficulty="Festive"),
    recipe("kappa-puzhukku", "Kappa Puzhukku", "Kerala", "Wayanad", "Kurichiya", "Tapioca mashed with coconut, turmeric and curry leaves, a forest-edge Wayanad staple.", ["Tapioca", "Coconut", "Turmeric", "Green chilli", "Curry leaves", "Coconut oil"], ["Boil cubed tapioca until tender.", "Grind coconut, chilli and turmeric.", "Mash together and temper with curry leaves."], "A satisfying gluten-free energy source with potassium.", "245 kcal", "3 g", "Udupi Pure Veg, Kalpetta", time_to_make="40 min", difficulty="Comfort mash"),
    recipe("sattu-paratha", "Sattu ka Paratha", "Uttar Pradesh", "Varanasi", "Purvanchali", "Roasted gram flour, sharp with mustard oil and pickle spice, sealed in whole-wheat flatbread.", ["Whole wheat flour", "Sattu", "Mustard oil", "Onion", "Ajwain", "Mango pickle"], ["Knead a soft wheat dough.", "Mix sattu with onion, ajwain and mustard oil.", "Stuff, roll and cook on a tawa."], "Sattu is an affordable source of protein, fibre and slow-burning energy.", "290 kcal", "12 g", "Kashi Chaat Bhandar, Varanasi", time_to_make="35 min", difficulty="Tawa craft"),
    recipe("malaaiyo", "Nimish (Malaaiyo)", "Uttar Pradesh", "Varanasi", "Bhojpuri", "A cloud-like saffron milk froth gathered from winter dew, sold at dawn in earthen cups.", ["Full-fat milk", "Saffron", "Pistachio", "Sugar", "Cardamom"], ["Reduce and sweeten milk.", "Chill overnight in a broad vessel.", "Whisk into fragile foam at dawn and garnish."], "A celebratory dairy dessert offering calcium and protein in a small serving.", "220 kcal", "7 g", "Shri Rajbandhu, Varanasi", time_to_make="Overnight", difficulty="Winter craft"),
]


def load_submissions():
    try:
        return json.loads(SUBMISSIONS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_submissions(items):
    SUBMISSIONS_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def all_recipes():
    return load_submissions() + RECIPES


def clean(value):
    return str(value or "").strip()


def allowed_video(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


@app.get("/api/recipes")
def get_recipes():
    term = clean(request.args.get("q")).lower()
    region = clean(request.args.get("region")).lower()
    community = clean(request.args.get("community")).lower()

    def matches(item):
        searchable = " ".join([item["name"], item["region"], item["locality"], item["community"], item["about"]]).lower()
        return ((not term or term in searchable) and
                (not region or item["region"].lower() == region) and
                (not community or item["community"].lower() == community))

    return jsonify([item for item in all_recipes() if matches(item)])


@app.get("/api/meta")
def get_meta():
    items = all_recipes()
    return jsonify({
        "regions": sorted({item["region"] for item in items}),
        "communities": sorted({item["community"] for item in items}),
    })


@app.get("/api/recipes/<recipe_id>")
def get_recipe(recipe_id):
    item = next((item for item in all_recipes() if item["id"] == recipe_id), None)
    return (jsonify(item), 200) if item else (jsonify({"error": "Recipe not found"}), 404)


@app.post("/api/submit")
def submit_recipe():
    fields = {key: clean(request.form.get(key)) for key in [
        "name", "region", "locality", "community", "about", "ingredients", "procedure",
        "benefits", "calories", "protein", "restaurant",
    ]}
    required = ["name", "region", "locality", "community", "about", "ingredients", "procedure"]
    if any(not fields[key] for key in required):
        return jsonify({"error": "Please complete all required recipe details."}), 400

    video = request.files.get("video")
    video_url = None
    if video and video.filename:
        if not allowed_video(video.filename):
            return jsonify({"error": "Please upload an MP4, MOV, WebM, or M4V video."}), 400
        filename = f"{int(time.time())}-{uuid4().hex[:8]}-{secure_filename(video.filename)}"
        video.save(UPLOAD_DIR / filename)
        video_url = f"/uploads/{filename}"

    slug = re.sub(r"[^a-z0-9]+", "-", fields["name"].lower()).strip("-")
    item = {
        "id": f"{slug}-{int(time.time())}", "name": fields["name"], "region": fields["region"],
        "locality": fields["locality"], "community": fields["community"], "about": fields["about"],
        "ingredients": [x.strip() for x in re.split(r"[\n,]", fields["ingredients"]) if x.strip()],
        "procedure": [x.strip() for x in fields["procedure"].splitlines() if x.strip()],
        "benefits": fields["benefits"] or "Community-submitted heritage recipe.",
        "calories": fields["calories"] or "—", "protein": fields["protein"] or "—",
        "restaurant": fields["restaurant"] or "Ask locally for this heritage dish",
        "map": fields["locality"], "image": IMAGE, "videoQuery": None if video_url else f"{fields['name']} recipe",
        "videoUrl": video_url, "time": "Community recipe", "difficulty": "Shared tradition", "isSubmission": True,
    }
    submissions = load_submissions()
    submissions.insert(0, item)
    save_submissions(submissions)
    return jsonify({"message": "Your recipe has been received and saved.", "recipe": item}), 201


@app.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.get("/recipe/<recipe_id>")
def recipe_page(recipe_id):
    return app.send_static_file("recipe.html")


@app.get("/submit")
def submit_page():
    return app.send_static_file("submit.html")


@app.get("/")
def home_page():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3000")), debug=True)
