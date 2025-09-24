import streamlit as st
import re
import pandas as pd
from resume_utils import (
    extract_text_from_file,
    get_match_score,
    get_role_suggestions,
    improvement_suggestions,
    is_resume_suitable,
    role_skill_map
)

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
st.title("📄🧠 AI-Powered Resume Analyzer")
st.write("Analyze resumes against job descriptions to find the best matches and improve your chances of landing that dream job!")

# ---------------- Role Selection with Back Button ----------------
if "role_choice" not in st.session_state:
    st.session_state.role_choice = None

if not st.session_state.role_choice:
    role_choice = st.selectbox(
        "I am a:",
        ["-- Select --", "Job Seeker 🎓", "Recruiter 🧑‍💼"],
        key="role_select"
    )
    if role_choice and role_choice != "-- Select --":
        st.session_state.role_choice = role_choice
        st.rerun()
else:
    if st.button("<< Back"):
        st.session_state.role_choice = None
        st.rerun()

# ---------- Helpers (used in both modes) ----------
def extract_role_from_jd(jd_text):
    jd_text_lower = jd_text.lower()
    for role in role_skill_map.keys():
        if role.lower() in jd_text_lower:
            return role
    return None

def highlight_skills(resume_text, skills):
    highlighted_text = resume_text
    for skill in skills:
        pattern = re.compile(rf'\b{re.escape(skill)}\b', re.IGNORECASE)
        highlighted_text = pattern.sub(f"<span style='color:green'><b>{skill}</b></span>", highlighted_text)
    return highlighted_text

def split_present_missing(resume_text, skills):
    present, missing = [], []
    for skill in skills:
        if re.search(rf'\b{re.escape(skill)}\b', resume_text, re.IGNORECASE):
            present.append(skill)
        else:
            missing.append(skill)
    return present, missing

# ========================== JOB SEEKER MODE ==========================
if st.session_state.role_choice == "Job Seeker 🎓":
    st.subheader(" 📑 Job Seeker Section... ")
    st.success("👋 Welcome Job Seeker! Upload your Resume and a JD to check your match scores and skill gaps.")
    jd_file = st.file_uploader("📑 Upload Company's Job Description (.pdf or .txt)", type=["pdf", "txt"])
    st.markdown(" ")
    resumes = st.file_uploader("📂 Upload Your Resume (.pdf or .txt)", type=["pdf", "txt"], accept_multiple_files=False)

    if jd_file and resumes:
        jd_text = jd_file.read().decode("utf-8", errors="ignore")
        jd_role = extract_role_from_jd(jd_text) 

        st.success(f"✅ Job description uploaded! Detected Role: `{jd_role}`")
        
    # # If job description is need , Comment it out !
    #     st.write("### 🧠 Job Description Preview:")
    #     st.code(jd_text[:500] + ("..." if len(jd_text) > 500 else ""), language="text")

        # Filters
        col_a, col_b = st.columns(2)
        with col_a:
            top_n = st.selectbox("Select Top N Resumes to Show", options=[1, 3, 5, 10, 15, 20, 25, 30], index=2)
        with col_b:
            min_score = st.selectbox("Minimum Match Score (%)", options=[0, 20, 30, 50, 70, 80, 90, 100], index=2)

        # Scores
        resume_scores, resume_texts = [], {}
        for rf in resumes:
            txt = extract_text_from_file(rf)
            score, _ = get_match_score(txt, jd_text)
            resume_scores.append((rf.name, score))
            resume_texts[rf.name] = (rf, txt)

        # Filter + sort
        filtered = [(n, s) for n, s in resume_scores if s >= min_score]
        top_filtered = sorted(filtered, key=lambda x: x[1], reverse=True)[:top_n]

        if not top_filtered:
            st.warning("⚠️ No resumes meet the selected match score threshold.")
        else:
            all_resumes_data = []

            for i, (resume_name, jd_score) in enumerate(top_filtered, 1):
                resume_file, resume_text = resume_texts[resume_name]
                suitable, _ = is_resume_suitable(resume_text, jd_role, role_skill_map)
                missing_keywords = get_match_score(resume_text, jd_text)[1]
                improve = improvement_suggestions(resume_text, jd_role, role_skill_map)

                st.subheader(f"📄 {resume_name}")
                st.markdown(f"**🎯 JD Role Match: `{jd_role}`**")
                st.markdown(f"- **Match Score:** {jd_score:.2f}%")
                st.markdown(f"- **Suitable:** {'✅ Yes' if suitable else '❌ No'}")
                st.markdown(f"- **Missing Keywords:** `{', '.join(missing_keywords[:15])}`")
                st.markdown(f"- **Improvement Suggestions:** `{', '.join(improve[:10])}`")

                # Try other roles
                with st.expander(f"🔍 Try Other Role Matching for {resume_file.name}"):
                    selected_role = st.selectbox(
                        "Select another role to test suitability:",
                        list(role_skill_map.keys()),
                        key=f"student_other_role_{resume_file.name}"
                    )
                    if selected_role:
                        alt_suitable, _ = is_resume_suitable(resume_text, selected_role, role_skill_map)
                        alt_improve = improvement_suggestions(resume_text, selected_role, role_skill_map)
                        alt_score, alt_missing = get_match_score(resume_text, " ".join(role_skill_map[selected_role]))

                        st.markdown(f"### 🧪 Results for Selected Role: `{selected_role}`")
                        st.markdown(f"- **Match Score:** {alt_score:.2f}%")
                        st.markdown(f"- ✅ Suitable: {'Yes' if alt_suitable else 'No'}")
                        st.markdown(f"- 💡 Suggestions: `{', '.join(alt_improve[:10])}`")
                        st.markdown(f"- 🔑 Missing Keywords: `{', '.join(alt_missing[:15])}`")

                # Highlight skills
                with st.expander(f"🧠 Highlight Skills in Resume for `{jd_role}`"):
                    present, missing = split_present_missing(resume_text, role_skill_map.get(jd_role, []))
                    highlighted = highlight_skills(resume_text, present)
                    st.markdown("#### ✅ Present Skills Highlighted in Green")
                    st.markdown(highlighted, unsafe_allow_html=True)
                    st.markdown("#### ❌ Missing Skills:")
                    st.markdown(", ".join(missing[:20]) or "—")

                # Predicted roles + chart
                role_scores = []
                for role in role_skill_map:
                    sc, _ = get_match_score(resume_text, " ".join(role_skill_map[role]))
                    role_scores.append((role, sc))
                role_scores_sorted = sorted(role_scores, key=lambda x: x[1], reverse=True)
                top_roles = role_scores_sorted[:3]

                st.markdown("### 🔮 Top 3 Predicted Roles from Resume:")
                for j, (rname, sc) in enumerate(top_roles, 1):
                    st.markdown(f"{j}. **{rname}** - `{sc:.2f}%`")

                st.markdown("#### 📈 Role Suitability Prediction Chart")
                chart_df_roles = pd.DataFrame(role_scores_sorted, columns=["Role", "Score"])
                st.bar_chart(chart_df_roles.set_index("Role"))

                st.markdown("---")

                all_resumes_data.append({
                    "filename": resume_name,
                    "jd_score": jd_score,
                    "top_roles": top_roles,
                    "missing_keywords": missing_keywords,
                    "improvements": improve,
                    "missing_skills": missing
                })

            # Global comparison chart
            st.markdown("## 📊 Match Score Comparison For All Resumes:")
            st.bar_chart(pd.DataFrame(resume_scores, columns=["Resume", "Score"]).set_index("Resume"))

            # Downloads
            final_csv_data, final_txt_summaries = [], []
            for d in all_resumes_data:
                final_csv_data.append({
                    "Resume": d["filename"],
                    "Match Score (%)": f"{d['jd_score']:.2f}",
                    "Top 3 Predicted Roles": ", ".join([r for r, _ in d["top_roles"]]),
                    "Missing Keywords": ", ".join(d["missing_keywords"][:15]),
                    "Improvement Suggestions": ", ".join(d["improvements"][:10]),
                    "Missing Skills": ", ".join(d["missing_skills"][:20])
                })
                summary = (
                    f"Resume: {d['filename']}\n"
                    f"Match Score: {d['jd_score']:.2f}%\n"
                    f"Top 3 Predicted Roles: {', '.join([r for r, _ in d['top_roles']])}\n"
                    f"Missing Keywords: {', '.join(d['missing_keywords'][:15])}\n"
                    f"Improvement Suggestions: {', '.join(d['improvements'][:10])}\n"
                    f"Missing Skills: {', '.join(d['missing_skills'][:20])}\n"
                    + "-"*50
                )
                final_txt_summaries.append(summary)

            st.download_button("📥 Download Summary (CSV)",
                               data=pd.DataFrame(final_csv_data).to_csv(index=False).encode("utf-8"),
                               file_name="resume_analysis.csv", mime="text/csv")
            st.download_button("📄 Download Summary (TXT)",
                               data="\n\n".join(final_txt_summaries),
                               file_name="summary_report.txt", mime="text/plain")

    st.markdown("---")
    # st.markdown("<div style='text-align: center; color: green;'>Made by <strong>❤️ Murali Krishna</strong> and <strong>Jarvis </strong></div>", unsafe_allow_html=True)

# ========================== RECRUITER MODE ==========================
elif st.session_state.role_choice == "Recruiter 🧑‍💼":
    st.subheader("📑 Recruiter Section...")
    st.success("👋 Welcome Recruiter! Upload Your Company's JD and Candidate Resumes to quickly find the best matches.")
    jd_file = st.file_uploader("📑 Upload Your Organization's Job Description (.pdf or .txt)", type=["pdf", "txt"])
    st.markdown(" ")
    resumes = st.file_uploader("📂 Upload Candidate Resumes (.pdf or .txt)", type=["pdf", "txt"], accept_multiple_files=True)

    if jd_file and resumes:
        jd_text = jd_file.read().decode("utf-8", errors="ignore")
        jd_role = extract_role_from_jd(jd_text) 

        st.success(f"✅ JD uploaded! Detected Role: `{jd_role}`")
        st.write("### 🧠 Job Description Preview:")
        st.code(jd_text[:500] + ("..." if len(jd_text) > 500 else ""), language="text")

        # Controls
        col1, col2 = st.columns(2)
        with col1:
            top_n = st.selectbox("Top N Resumes to Show", [1, 3, 5, 10, 15, 20, 50], index=2)
        with col2:
            min_score = st.selectbox("Minimum Match Score (%)", [0, 20, 30, 40, 50, 60, 70, 80, 90], index=3)

        # Score resumes
        resume_scores, resume_texts = [], {}
        for rf in resumes:
            txt = extract_text_from_file(rf)
            score, _ = get_match_score(txt, jd_text)
            resume_scores.append((rf.name, score))
            resume_texts[rf.name] = (rf, txt)

        # Filter & sort
        filtered = [(n, s) for n, s in resume_scores if s >= min_score]
        ranked = sorted(filtered, key=lambda x: x[1], reverse=True)
        top_ranked = ranked[:top_n]

        if not top_ranked:
            st.warning("⚠️ No resumes meet the selected match score threshold.")
        else:
            overview_rows = []
            for name, score in top_ranked:
                _, txt = resume_texts[name]
                suitable, _ = is_resume_suitable(txt, jd_role, role_skill_map)
                top_roles = get_role_suggestions(txt)
                overview_rows.append({
                    "Resume": name,
                    "Match Score (%)": f"{score:.2f}",
                    "Suitable": "Yes" if suitable else "No",
                    "Top Roles": ", ".join([r for r, _ in top_roles]) or "—",
                })
            st.subheader("🏆 Candidate Ranking (Overview)")
            st.dataframe(pd.DataFrame(overview_rows), use_container_width=True)

            # Comparison chart
            st.markdown("## 📊 Match Score Comparison (Filtered)")
            st.bar_chart(pd.DataFrame(top_ranked, columns=["Resume", "Score"]).set_index("Resume"))

            st.markdown("---")
            st.subheader("🧾 Candidate Details")

            all_resumes_data = []
            for name, score in top_ranked:
                rf, txt = resume_texts[name]
                suitable, _ = is_resume_suitable(txt, jd_role, role_skill_map)
                missing_keywords = get_match_score(txt, jd_text)[1]
                improve = improvement_suggestions(txt, jd_role, role_skill_map)

                st.markdown(f"### 📄 {name}")
                st.markdown(f"**🎯 JD Role Match: `{jd_role}`**")
                st.markdown(f"- **Match Score:** {score:.2f}%")
                st.markdown(f"- **Suitable:** {'✅ Yes' if suitable else '❌ No'}")
                st.markdown(f"- **Missing Keywords:** `{', '.join(missing_keywords[:15])}`")
                st.markdown(f"- **Improvement Suggestions:** `{', '.join(improve[:10])}`")

                with st.expander(f"🔍 Try Other Role Matching for {name}"):
                    selected_role = st.selectbox(
                        "Select another role to test suitability:",
                        list(role_skill_map.keys()),
                        key=f"recruiter_other_role_{name}"
                    )
                    if selected_role:
                        alt_suitable, _ = is_resume_suitable(txt, selected_role, role_skill_map)
                        alt_improve = improvement_suggestions(txt, selected_role, role_skill_map)
                        alt_score, alt_missing = get_match_score(txt, " ".join(role_skill_map[selected_role]))

                        st.markdown(f"#### 🧪 Results for Selected Role: `{selected_role}`")
                        st.markdown(f"- **Match Score:** {alt_score:.2f}%")
                        st.markdown(f"- ✅ Suitable: {'Yes' if alt_suitable else 'No'}")
                        st.markdown(f"- 💡 Suggestions: `{', '.join(alt_improve[:10])}`")
                        st.markdown(f"- 🔑 Missing Keywords: `{', '.join(alt_missing[:15])}`")

                with st.expander(f"🧠 Highlight Skills in Resume for `{jd_role}`"):
                    present, missing = split_present_missing(txt, role_skill_map.get(jd_role, []))
                    highlighted = highlight_skills(txt, present)
                    st.markdown("#### ✅ Present Skills Highlighted in Green")
                    st.markdown(highlighted, unsafe_allow_html=True)
                    st.markdown("#### ❌ Missing Skills:")
                    st.markdown(", ".join(missing[:20]) or "—")

                # Predicted roles
                role_scores = []
                for rname in role_skill_map:
                    sc, _ = get_match_score(txt, " ".join(role_skill_map[rname]))
                    role_scores.append((rname, sc))
                role_scores_sorted = sorted(role_scores, key=lambda x: x[1], reverse=True)
                top_roles = role_scores_sorted[:3]

                st.markdown("#### 🔮 Top 3 Predicted Roles from Resume:")
                for j, (rname, sc) in enumerate(top_roles, 1):
                    st.markdown(f"{j}. **{rname}** - `{sc:.2f}%`")

                st.markdown("##### 📈 Role Suitability Prediction Chart")
                st.bar_chart(pd.DataFrame(role_scores_sorted, columns=["Role", "Score"]).set_index("Role"))

                st.markdown("---")

                all_resumes_data.append({
                    "filename": name,
                    "jd_score": score,
                    "top_roles": top_roles,
                    "missing_keywords": missing_keywords,
                    "improvements": improve,
                    "missing_skills": missing
                })

            # Exports
            final_csv_data, final_txt_summaries = [], []
            for d in all_resumes_data:
                final_csv_data.append({
                    "Resume": d["filename"],
                    "Match Score (%)": f"{d['jd_score']:.2f}",
                    "Top 3 Predicted Roles": ", ".join([r for r, _ in d["top_roles"]]),
                    "Missing Keywords": ", ".join(d["missing_keywords"][:15]),
                    "Improvement Suggestions": ", ".join(d["improvements"][:10]),
                    "Missing Skills": ", ".join(d["missing_skills"][:20])
                })
                summary = (
                    f"Resume: {d['filename']}\n"
                    f"Match Score: {d['jd_score']:.2f}%\n"
                    f"Top 3 Predicted Roles: {', '.join([r for r, _ in d['top_roles']])}\n"
                    f"Missing Keywords: {', '.join(d['missing_keywords'][:15])}\n"
                    f"Improvement Suggestions: {', '.join(d['improvements'][:10])}\n"
                    f"Missing Skills: {', '.join(d['missing_skills'][:20])}\n"
                    + "-"*50
                )
                final_txt_summaries.append(summary)

            st.subheader("📦 Export Results")
            st.download_button("📥 Download CSV",
                               data=pd.DataFrame(final_csv_data).to_csv(index=False).encode("utf-8"),
                               file_name="recruiter_results.csv", mime="text/csv")
            st.download_button("📄 Download TXT",
                               data="\n\n".join(final_txt_summaries),
                               file_name="recruiter_summary.txt", mime="text/plain")


    st.markdown("---")
    # st.markdown("<div style='text-align: center; color: green;'>Made by <strong>❤️ Murali Krishna</strong> and <strong>Jarvis </strong></div>", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("👨‍💻 Crafted by **Murali Krishna** and **Jarvis ...**")

# ===================== FOOTER =====================
st.markdown(" ")
st.markdown(" ")
st.markdown(" ")
st.markdown(" ")
st.markdown(" ")
st.markdown(" ")
st.markdown("""
<style>
.footer {
    background-color: #232c38;
    color: #e7e7e7;
    padding: 30px 0 10px 0;
    font-size: 16px;
    margin-top: 40px;
}
.footer hr {
    border-color: #555;
    margin-top: 18px;
    margin-bottom: 12px;
}
.footer-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 32px;
}
.footer-section {
    flex: 1;
    min-width: 260px;
    margin-bottom: 16px;
}
.footer-section h3 {
    color: #fff;
    margin-bottom: 7px;
}
.footer-icons a {
    color: #44aaff;
    margin-right: 12px;
    font-size: 26px;
    text-decoration: none;
}
.footer-icons img {
    vertical-align: middle;
}
.footer-bottom {
    text-align: center;
    font-size: 15px;
    color: #bbb;
    margin-top: 10px;
}
</style>

<div class="footer">
  <div class="footer-container">
    <div class="footer-section">
      <h3>AI Resume Analyzer</h3>
      <div>
        Empowering careers through advanced AI technology.<br>
        Helping students and recruiters make smarter decisions.
      </div>
    </div>
    <div class="footer-section">
      <h3>Features</h3>
      <div>
        AI-Powered Matching<br>
        Career Guidance<br>
        Market Intelligence<br>
        Predictive Analytics
      </div>
    </div>
    <div class="footer-section">
      <h3>Connect</h3>
      <div class="footer-icons">
        <a href="https://twitter.com/" target="_blank" title="Twitter">
            <img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/twitter.svg" width="24" height="24"/>
        </a>
        <a href="https://www.linkedin.com/in/muralikrishna-banoth/" target="_blank" title="LinkedIn">
            <img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/linkedin.svg" width="24" height="24"/>
        </a>
        <a href="https://github.com/Murali-2569" target="_blank" title="GitHub">
            <img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/github.svg" width="24" height="24"/>
        </a>
      </div>
    </div>
  </div>
  <hr>
  <div class="footer-bottom">
    © 2025 All Rights Reserved ✅ <br>AI-Powered Resume Analyzer.
            Built by Murali Krishna...
  </div>
</div>
""", unsafe_allow_html=True)