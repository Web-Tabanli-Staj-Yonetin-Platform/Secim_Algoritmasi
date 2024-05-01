import pandas as pd
import numpy as np
import scipy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# Veri setlerini oku
intern_data = pd.read_csv("./datasets/intern.csv")
ilan_data = pd.read_csv("./datasets/ilan.csv")

# Boş değerleri uygun şekilde doldur
#intern_data.fillna("", inplace=True)
intern_data.fillna(np.nan, inplace=True)
ilan_data.fillna("", inplace=True)

# Intern ve ilan verilerini birleştir
intern_ilan_pairs = []
for _, intern_row in intern_data.iterrows():
    for _, ilan_row in ilan_data.iterrows():
        features = [intern_row["Field of Interest"], intern_row["Department"], intern_row["Skills"], intern_row["Average Grade"], ilan_row["Scope"], ilan_row["Wanted"], ilan_row["Department"]]
        intern_ilan_pairs.append(features)

# Özellikleri vektörleştir
tfidf_vectorizer = TfidfVectorizer()
X = tfidf_vectorizer.fit_transform([" ".join(map(str, x)) for x in intern_ilan_pairs])

# Eğitim etiketlerini oluştur
y = [1 if intern_row["Field of Interest"] == ilan_row["Scope"] else 0 for _, intern_row in intern_data.iterrows() for _, ilan_row in ilan_data.iterrows()]

# Modeli eğit
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Modeli değerlendir
#y_pred = model.predict(X)
#print(classification_report(y, y_pred))

# Her bir intern için en iyi 3 eşleşmeyi bul
interns = intern_data["Firstname"] + " " + intern_data["Lastname"]
ilan_names = ilan_data["Company Name"]
intern_matches = {}

for intern in interns:
    intern_matches[intern] = []

for i, intern in enumerate(interns):
    ilan_scores = model.predict_proba(X[i*len(ilan_data):(i+1)*len(ilan_data)])[:, 1]
    for j, ilan in enumerate(ilan_names):
        intern_matches[intern].append((ilan, ilan_scores[j]))

for intern, matches in intern_matches.items():
    print(f"\n{intern}:")
    top_matches = sorted(matches, key=lambda x: x[1], reverse=True)[:3]
    for match in top_matches:
        print(f"{match[0]}: Match Score = {match[1]:.2f}")