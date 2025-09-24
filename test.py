# Quick local test: process first JD in /jobs against all files in /resumes
import os, csv
from types import SimpleNamespace

from resume_utils import (
    extract_text_from_file,
    get_match_score,
    detect_role_from_jd,
    role_skill_map,
    compute_ats_score,
    compute_experience_match,
    extract_experience_years,
    compute_role_scores,
)

job_folder, resume_folder = "jobs", "resumes"
job_files = [f for f in os.listdir(job_folder) if f.endswith(".txt")]
if not job_files:
    print("❌ No JD found in /jobs")
    raise SystemExit

with open(os.path.join(job_folder, job_files[0]), "r", encoding="utf-8") as f:
    jd_text = f.read()

detected_role = detect_role_from_jd(jd_text, role_skill_map)
print("Detected role:", detected_role)

results = []
for fn in os.listdir(resume_folder):
    if not (fn.endswith(".txt") or fn.endswith(".pdf")):
        continue
    with open(os.path.join(resume_folder, fn), "rb") as f:
        buf = f.read()
    up = SimpleNamespace(name=fn, getvalue=lambda b=buf: b)
    txt = extract_text_from_file(up)
    score, missing = get_match_score(txt, jd_text)
    ats = compute_ats_score(txt)
    expm = compute_experience_match(txt, jd_text)
    yrs = extract_experience_years(txt)
    roles = compute_role_scores(txt, role_skill_map)[:3]
    print(f"{fn}: score={score:.2f}%, ATS={ats:.1f}%, ExpMatch={expm:.1f}% ({yrs:.1f} yrs), roles={[r for r, _ in roles]}")
    results.append((fn, score))

if results:
    results.sort(key=lambda x: x[1], reverse=True)
    print("Best:", results[0])

with open("match_results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Resume", "Match Score"])
    w.writerows(results)
    print("✅ match_results.csv written")
