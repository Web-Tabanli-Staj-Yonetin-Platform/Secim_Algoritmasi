"""import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Veri setlerini yükleme
ilan_df = pd.read_csv('./datasets/ilan.csv')
intern_df = pd.read_csv('./datasets/intern.csv')

# Skill seviyelerini puanlandırma
def skill_level_score(skill):
    if "ileri seviye" in skill:
        return 3
    elif "orta seviye" in skill:
        return 2
    elif "başlangıç seviye" in skill:
        return 1
    return 0


# Eşleşme skoru hesaplama fonksiyonu
def calculate_match_score(ilan, intern):
    score = 0

    # Scope ve Field of Interest eşleşmesi
    if ilan['Scope'].strip().lower() == intern['Field of Interest'].strip().lower():
        score += 1  # Eşleşme varsa 1 puan ekle

    # Wanted ve Skills eşleşmesi
    wanted_skills = re.findall(r'\b[\w\+#.]+\b', ilan['Wanted'].lower())
    intern_skills = re.findall(r'([\w\+#.]+)\s*\((.*?)\)', intern['Skills'].lower())

    for wanted_skill in wanted_skills:
        for intern_skill, level in intern_skills:
            if wanted_skill == intern_skill:
                score += skill_level_score(level)

    return score


# Eşleştirme süreci
match_scores = []

for idx, intern in intern_df.iterrows():
    scores = []

    for index, ilan in ilan_df.iterrows():
        score = calculate_match_score(ilan, intern)
        scores.append((ilan['Company Name'], score))

    # En yüksek skoru alan 3 ilanı seç
    top_matches = sorted(scores, key=lambda x: x[1], reverse=True)[:3]

    intern_name = f"{intern['Firstname']} {intern['Lastname']}"

    for match in top_matches:
        match_scores.append({
            'intern_name': intern_name,
            'ilan_name': match[0],
            'score': match[1]
        })

# Sonuçları DataFrame'e dönüştürme
matches_df = pd.DataFrame(match_scores)

# En iyi eşleşmeleri bulma ve görüntüleme
best_matches = matches_df.sort_values(by=['intern_name', 'score'], ascending=[True, False])

# Her intern için eşleşen ilanları gruplayarak çıktı oluşturma
output = best_matches.groupby('intern_name').apply(lambda x: x[['ilan_name', 'score']].values.tolist()).reset_index()
output.columns = ['Intern', 'Matches']
output['Matches'] = output['Matches'].apply(lambda x: [{'ilan_name': m[0], 'score': m[1]} for m in x])

# Çıktıyı görüntüleme
for idx, row in output.iterrows():
    print(f"Intern: {row['Intern']}")
    for match in row['Matches']:
        print(f"  Ilan: {match['ilan_name']}, Score: {match['score']}")
    print("\n")"""

"""import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Intern ve ilan veri setlerini oku
intern_data = pd.read_csv('./datasets/intern.csv')
ilan_data = pd.read_csv('./datasets/ilan.csv')

# "Skills", "Field of Interest", "Job Description" ve "Wanted" sütunlarını string türüne dönüştür
intern_data["Skills"] = intern_data["Skills"].astype(str)
intern_data["Field of Interest"] = intern_data["Field of Interest"].astype(str)
ilan_data["Job Description"] = ilan_data["Job Description"].astype(str)
ilan_data["Wanted"] = ilan_data["Wanted"].astype(str)


# Eşleştirme işlemi için fonksiyon tanımla
def match_intern_to_ilan(intern_row, ilan_data):
    intern_field_of_interest = intern_row["Field of Interest"]
    intern_department = intern_row["Department"]
    intern_average_grade = intern_row["Average Grade"]
    intern_skills = {re.sub(r'[^a-zA-Z0-9\s]', '', skill.split('(')[0].strip()): skill.split('(')[1].strip(')') for
                     skill in intern_row["Skills"].split(", ") if '(' in skill}

    ilan_data_copy = ilan_data.copy()  # ilan_data'nın bir kopyasını oluştur

    # ilan_data_copy veri çerçevesinde "Match Score" sütununu oluştururken float türünü belirt
    ilan_data_copy["Match Score"] = 0.0

    for index, ilan_row in ilan_data_copy.iterrows():
        ilan_job_description = ilan_row["Job Description"]
        ilan_department = ilan_row["Department"]
        ilan_wanted = ilan_row["Wanted"]

        # Field of Interest and Job Description similarity
        tfidf = TfidfVectorizer().fit_transform([intern_field_of_interest, ilan_job_description])
        field_job_similarity = cosine_similarity(tfidf[0], tfidf[1])[0][0]

        # Department matching
        department_match = 1 if intern_department == ilan_department else 0

        # Average Grade and Wanted matching
        try:
            wanted_min_grade_match = re.search(r'\d+\.\d+', str(ilan_wanted))  # Use search instead of findall
            if wanted_min_grade_match:
                wanted_min_grade = float(wanted_min_grade_match.group())
            else:
                wanted_min_grade = None  # Handle cases with no minimum grade
        except AttributeError:
            # Handle potential errors during regex search
            wanted_min_grade = None

        average_grade_match = 1 if intern_average_grade >= wanted_min_grade else 0

        # Skills and Wanted matching
        wanted_skills_list = {re.sub(r'[^a-zA-Z0-9\s]', '', skill.split('(')[0].strip()): skill.split('(')[1].strip(')')
                              for skill in ilan_wanted.split(", ") if '(' in skill}
        skill_match_score = 0
        if wanted_skills_list:
            for skill, level in intern_skills.items():
                if skill in wanted_skills_list:
                    wanted_level = wanted_skills_list[skill]
                    if wanted_level == level:
                        skill_match_score += 3  # Beceri seviyesi aynı ise 3 puan
                    elif (wanted_level == "İleri Seviye" and level == "Orta Seviye") or (
                            wanted_level == "Orta Seviye" and level == "Başlangıç Seviye"):
                        skill_match_score += 2  # İstenen seviye ile intern'in seviyesi bir seviye düşükse 2 puan
                    elif wanted_level == "İleri Seviye" and level == "Başlangıç Seviye":
                        skill_match_score += 1  # İstenen seviye ile intern'in seviyesi iki seviye düşükse 1 puan

            # Handle potential division by zero
            if len(wanted_skills_list) > 0:
                skill_match_score /= len(wanted_skills_list)
            else:
                skill_match_score = 0  # Assign a default value

        # Calculate match score with weighted sum
        match_score = field_job_similarity * 0.3 + department_match * 0.3 + average_grade_match * 0.2 + skill_match_score * 0.2

        # Assign match score to the ilan_data_copy dataframe
        ilan_data_copy.loc[index, "Match Score"] = match_score

    # Sort ilan_data_copy by Match Score in descending order and return top 3 matches
    top_matches = ilan_data_copy.sort_values(by="Match Score", ascending=False).head(3)
    return top_matches


# Yeni intern ve staj ilanı eklenirse, bu fonksiyonu çağırarak eşleştirme işlemini yeniden yapabiliriz
def update_matches():
    for index, intern_row in intern_data.iterrows():
        print("Eşleştirme sonuçları for:", intern_row["Firstname"], intern_row["Lastname"])
        matched_ilans = match_intern_to_ilan(intern_row, ilan_data)
        print(matched_ilans)


# Güncellenmiş eşleştirmeleri yap
update_matches()"""

import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Intern ve ilan veri setlerini oku
intern_data = pd.read_csv('./datasets/intern.csv')
ilan_data = pd.read_csv('./datasets/ilan.csv')

# Beceri seviyelerine göre katsayılar
skill_levels = {
    "İleri Seviye": 1.0,
    "Orta Seviye": 0.7,
    "Başlangıç Seviye": 0.4
}

# Takım Çalışması, İletişim ve Analitik Beceriler seviyelerine göre katsayılar
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
        grade_match = 1  # Eğer "Wanted" içinde not ortalaması belirtilmemişse eşleşme yapılıyor

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
                        language_match_score = 1  # Eğer bir eşleşme varsa, skoru 1 olarak ayarla
                        break
            if language_match_score == 1:
                break

    # Toplam match score (Field match'in ağırlığı artırılmış)
    total_score = (field_match * 2 + department_match + grade_match + skill_match_score + teamwork_match_score + communication_match_score + analytical_match_score + language_match_score) / 9
    return total_score

# Her bir intern için ilan verilerini eşleştir
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