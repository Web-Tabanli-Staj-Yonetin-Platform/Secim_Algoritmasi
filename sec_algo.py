from pymongo import MongoClient
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

client = MongoClient("mongodb+srv://omerfaruk:12345@stajyonetim.0lqminl.mongodb.net/")
db = client["test"]
intern_collection = db["interns"]
ilan_collection = db["adverts"]
matched_content_collection = db["matches"]

# Beceri seviyelerine göre katsayılar
skill_levels = {
    "ileri": 1.0,
    "orta": 0.7,
    "başlangıç": 0.4
}

# Takım Çalışması, İletişim ve Analitik Beceriler seviyelerine göre katsayılar
teamwork_levels = {
    "Very Good": 1.0,
    "Good": 0.7,
    "Medium": 0.4
}

communication_levels = {
    "Very Good": 1.0,
    "Good": 0.7,
    "Medium": 0.4
}

analytical_levels = {
    "Very Good": 1.0,
    "Good": 0.7,
    "Medium": 0.4
}

# Dil seviyelerine göre katsayılar
language_levels = {
    "A1": "Başlangıç Seviye",
    "A2": "Başlangıç Seviye",
    "B1": "Orta Seviye",
    "B2": "Orta Seviye",
    "C1": "İleri Seviye",
    "C2": "İleri Seviye"
}


# Match score hesaplama fonksiyonu
def calculate_match_score(intern_interest, ilan_scope, intern_department, ilan_departments, intern_avg_grade,
                          ilan_wanted, intern_skills, intern_teamwork, intern_communication, intern_analytical,
                          intern_languages, ilan_language):
    # Field of Interest ve Scope eşleşme kontrolü
    tfidf = TfidfVectorizer().fit_transform([intern_interest, ilan_scope])
    similarity = cosine_similarity(tfidf[0], tfidf[1])[0][0]
    field_match = 1 if similarity > 0.5 else 0

    # Department eşleştirme kontrolü
    ilan_departments_list = ilan_departments.split(', ')
    department_match = 1 if "Herhangi" in ilan_departments_list or intern_department in ilan_departments_list else 0

    # Average Grade eşleştirme kontrolü
    try:
        intern_avg_grade = float(intern_avg_grade)
    except ValueError:
        intern_avg_grade = 0.0  # Elde edilemeyen veya hatalı veri durumunda varsayılan değer

    match = re.search(r"En az (\d+\.\d+) not ortalamasına", ilan_wanted)
    if match:
        wanted_min_grade = float(match.group(1))
        grade_match = 1 if intern_avg_grade >= wanted_min_grade else 0.5
    else:
        grade_match = 1  # Eğer "Wanted" içinde not ortalaması belirtilmemişse eşleşme yapılıyor

    # Skills eşleştirme kontrolü
    skill_match_score = 0
    total_wanted_skills = 0
    for skill in intern_skills:
        if '(' in skill and ')' in skill:
            skill_name, skill_level = skill.rsplit('(', 1)
            skill_name = skill_name.strip()
            skill_level = skill_level.strip(') ')
            if skill_name in ilan_wanted:
                skill_match_score += skill_levels.get(skill_level, 0)
                total_wanted_skills += 1

    if total_wanted_skills > 0:
        total_skill_match_score = skill_match_score / total_wanted_skills
    else:
        total_skill_match_score = skill_match_score

    # Takım Çalışması eşleştirme kontrolü
    teamwork_match_score = teamwork_levels.get(intern_teamwork, 0)

    # İletişim eşleştirme kontrolü
    communication_match_score = communication_levels.get(intern_communication, 0)

    # Analitik Beceri eşleştirme kontrolü
    analytical_match_score = analytical_levels.get(intern_analytical, 0)

    # Dil (Language) eşleştirme kontrolü
    language_match_score = 0
    ilan_language_list = ilan_language.split(', ')
    for intern_lang in intern_languages:
        if '(' in intern_lang and ')' in intern_lang:
            intern_lang_name, intern_lang_level = intern_lang.rsplit('(', 1)
            intern_lang_name = intern_lang_name.strip()
            intern_lang_level = intern_lang_level.strip(') ')
            for ilan_lang in ilan_language_list:
                if '(' in ilan_lang and ')' in ilan_lang:
                    ilan_lang_name, ilan_lang_level = ilan_lang.rsplit('(', 1)
                    ilan_lang_name = ilan_lang_name.strip()
                    ilan_lang_level = ilan_lang_level.strip(') ')
                    if (intern_lang_name == ilan_lang_name and
                            language_levels.get(intern_lang_level) == ilan_lang_level):
                        language_match_score = 1  # Eğer bir eşleşme varsa, skoru 1 olarak ayarla
                        break
            if language_match_score == 1:
                break

    # Toplam match score (Field match'in ağırlığı artırılmış)
    total_score = (
                          field_match * 2
                          + department_match
                          + grade_match
                          + total_skill_match_score
                          + teamwork_match_score
                          + communication_match_score
                          + analytical_match_score
                          + language_match_score
                  ) / 8
    r_total_score = round(total_score, 2)
    return r_total_score


# Her bir intern için ilan verilerini eşleştir ve MongoDB'ye kaydet
for intern in intern_collection.find():
    first_name = intern.get("firstName", "N/A")
    last_name = intern.get("lastName", "N/A")
    print("Intern:", first_name, last_name)
    top_matches = []
    for ilan in ilan_collection.find():
        match_score = calculate_match_score(
            intern.get("desiredField", ""),
            ilan.get("field", ""),
            intern.get("department", ""),
            ilan.get("department", ""),
            intern.get("average", "0.0"),
            ilan.get("requirements", ""),
            intern.get("skills", []),
            intern.get("teamWorkSkill", ""),
            intern.get("communicationSkill", ""),
            intern.get("analyticalSkill", ""),
            intern.get("languages", []),
            ilan.get("foreignLanguages", "")
        )
        top_matches.append({"advert_id": ilan["_id"], "match_score": match_score})

    top_matches.sort(key=lambda x: x["match_score"], reverse=True)
    matched_content = {
        "intern_id": intern["_id"],
        "matches": top_matches[:3]  # İlk 3 eşleşmeyi al
    }

    # Mevcut kayıt olup olmadığını kontrol et ve güncelle veya ekle
    existing_record = matched_content_collection.find_one({"intern_id": intern["_id"]})
    if existing_record:
        matched_content_collection.update_one(
            {"intern_id": intern["_id"]},
            {"$set": matched_content}
        )
    else:
        matched_content_collection.insert_one(matched_content)

    print("Matched content saved for intern:", intern["_id"])
