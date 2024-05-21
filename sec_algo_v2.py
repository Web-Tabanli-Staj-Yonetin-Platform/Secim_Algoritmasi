import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Intern ve ilan veri setlerini okumak için
intern_data = pd.read_csv('./datasets/intern.csv')
ilan_data = pd.read_csv('./datasets/ilan.csv')

# Beceri seviyelerine, Dil seviyelerine, Takım Çalışması, İletişim ve Analitik Becerilerine göre katsayıları ayarlamak için
skill_levels = {
    "İleri Seviye": 1.0,
    "Orta Seviye": 0.7,
    "Başlangıç Seviye": 0.4
}

teamwork_levels = {
    "Çok İyi": 1.0,
    "İyi": 0.7,
    "Orta": 0.4
}

communication_levels = {
    "Çok İyi": 1.0,
    "İyi": 0.7,
    "Orta": 0.4
}

analytical_levels = {
    "Çok İyi": 1.0,
    "İyi": 0.7,
    "Orta": 0.4
}

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
                          ilan_wanted, intern_skills, intern_teamwork, intern_communication, intern_analytical, intern_language, ilan_language):
    # Field of Interest ve Scope eşleşme kontrolü
    tfidf = TfidfVectorizer().fit_transform([intern_interest, ilan_scope])
    similarity = cosine_similarity(tfidf[0], tfidf[1])[0][0]
    field_match = 1 if similarity > 0.5 else 0

    # Department eşleştirme kontrolü
    ilan_departments_list = ilan_departments.split(', ')
    department_match = 1 if "Herhangi" in ilan_departments_list or intern_department in ilan_departments_list else 0

    # Average Grade eşleştirme kontrolü
    match = re.search(r"En az (\d+\.\d+) not ortalamasına", ilan_wanted)
    if match:
        wanted_min_grade = float(match.group(1))
        grade_match = 1 if intern_avg_grade >= wanted_min_grade else 0.5
    else:
        grade_match = 1  # Eğer "Wanted" içinde not ortalaması belirtilmemişse eşleşme yapılması için

    # Skills eşleştirme kontrolü
    skill_match_score = 0
    intern_skills_list = intern_skills.split(', ')
    for skill in intern_skills_list:
        if '(' in skill and ')' in skill:
            skill_name, skill_level = skill.rsplit('(', 1)
            skill_name = skill_name.strip()
            skill_level = skill_level.strip(') ')
            if skill_name in ilan_wanted:
                skill_match_score += skill_levels.get(skill_level, 0)

    skill_match_score /= len(intern_skills_list)  # Normalizasyon

    # Takım Çalışması eşleştirme kontrolü
    teamwork_match_score = teamwork_levels.get(intern_teamwork, 0)

    # İletişim eşleştirme kontrolü
    communication_match_score = communication_levels.get(intern_communication, 0)

    # Analitik Beceri eşleştirme kontrolü
    analytical_match_score = analytical_levels.get(intern_analytical, 0)

    # Dil (Language) eşleştirme kontrolü
    language_match_score = 0
    intern_language = str(intern_language) if pd.notna(intern_language) else ""
    ilan_language = str(ilan_language) if pd.notna(ilan_language) else ""
    intern_language_list = intern_language.split(', ')
    ilan_language_list = ilan_language.split(', ')
    for intern_lang in intern_language_list:
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
                        language_match_score = 1  # Eğer bir eşleşme varsa, skoru 1 olarak ayarlandı
                        break
            if language_match_score == 1:
                break

    # Toplam match score hesabı
    total_score = (field_match * 2 + department_match + grade_match + skill_match_score + teamwork_match_score + communication_match_score + analytical_match_score + language_match_score) / 9
    return total_score

# Her bir intern için ilan verilerini eşleştirmek için
for _, intern_row in intern_data.iterrows():
    print("Intern:", intern_row["Firstname"], intern_row["Lastname"])
    top_matches = []
    for _, ilan_row in ilan_data.iterrows():
        match_score = calculate_match_score(
            intern_row["Field of Interest"],
            ilan_row["Scope"],
            intern_row["Department"],
            ilan_row["Department"],
            intern_row["Average Grade"],
            ilan_row["Wanted"],
            intern_row["Skills"],
            intern_row["Teamwork"],
            intern_row["Communication"],
            intern_row["Analytical Skill"],
            intern_row["Language"],
            ilan_row["Language"]
        )
        top_matches.append((ilan_row["Company Name"], match_score))
    top_matches.sort(key=lambda x: x[1], reverse=True)
    for i in range(min(3, len(top_matches))):
        print("İlan:", top_matches[i][0], "| Match Score:", top_matches[i][1])
    print()
