import re
import PyPDF2
import json
import os

# ===== Load Roles and Skills from JSON =====
def load_role_skill_map(json_path="role_skill_map.json"):
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

role_skill_map = load_role_skill_map()

# ===== Extract text from PDF/TXT =====
def extract_text_from_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(uploaded_file)
        text = "".join([page.extract_text() or "" for page in reader.pages])
        return text
    elif name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")
    return ""

# ===== Basic keyword match =====
def get_match_score(resume_text, jd_text):
    r = resume_text.lower()
    words = [w for w in jd_text.lower().split() if len(w) > 2]
    if not words:
        return 0.0, []
    found = [w for w in words if w in r]
    missing = list(set(words) - set(found))
    return (len(found) / len(words)) * 100, missing

# ===== Role suggestions (top-3) from resume =====
def get_role_suggestions(resume_text):
    r = resume_text.lower()
    scored = []
    for role, skills in role_skill_map.items():
        score = sum(1 for s in skills if s in r)
        if score:
            pct = round((score / max(len(skills), 1)) * 100, 2)
            scored.append((role, pct))
    return sorted(scored, key=lambda x: x[1], reverse=True)[:3]

# ===== Suggestions for improvement (missing role skills) =====
def improvement_suggestions(resume_text, role, role_skill_map_input=None):
    r = resume_text.lower()
    skills = (role_skill_map_input or role_skill_map).get(role, [])
    return [s for s in skills if s not in r]

# ===== Suitability check for a role (thresholded) =====
def is_resume_suitable(resume_text, role, role_skill_map_input=None, threshold=30):
    skills_text = " ".join((role_skill_map_input or role_skill_map).get(role, []))
    score, missing = get_match_score(resume_text, skills_text)
    return (score >= threshold, missing)
