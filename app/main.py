import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
from PIL import Image
import os
from modules.pdf_loader import extract_text_from_pdf
from modules.ai_engine import analyze_candidate

# CONFIGURATION 
icon_path = "assets/icon.png"
icon_image = Image.open(icon_path)
st.set_page_config(
    page_title="RecruitMap Dashboard",
    page_icon=icon_image,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# LOAD CSS 
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

css_path = "app/style.css"
try:
    load_css(css_path)
except FileNotFoundError:
    st.warning("File assets/style.css tidak ditemukan. Styling mungkin tidak muncul.")

# UI LAYOUT

# Header Section
st.markdown("""
<div style="text-align: center; margin-bottom: 40px;">
    <h1 style="font-size: 3.5rem; margin-bottom: 10px;">RecruitMap <span style="color:#1f8cf9">AI</span></h1>
    <p style="font-size: 1.2rem; color: #94a3b8;">
        Intelligent Resume Screening & Candidate Analysis System
    </p>
</div>
""", unsafe_allow_html=True)

# Load Default Job Description
try:
    with open("data/job_desc.txt", "r") as f:
        default_jd = f.read()
except FileNotFoundError:
    default_jd = ""

# MAIN GRID 
with st.container():
    col1, col2 = st.columns([5, 6], gap="large")

    with col1:
        # LEFT CARD: CONTEXT 
        st.markdown('### 💼 Job Context')
        st.markdown('Definisikan kriteria posisi untuk kalibrasi AI.')
    
        # Navigasi Sumber Job Description
        tab_manual, tab_upload = st.tabs(["Manual Input", "Upload File"])
        
        # TAB 1: MANUAL 
        with tab_manual:
            st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
            jd_manual = st.text_area(
                "Job Description Input", 
                value=default_jd, 
                height=400, 
                placeholder="Paste Job Description lengkap di sini...",
                help="Masukkan Hard Skills, Soft Skills, dan persyaratan pengalaman.",
                label_visibility="collapsed"
            )

        # TAB 2: UPLOAD 
        with tab_upload:
            st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
            with st.container():
                jd_file = st.file_uploader(
                    "Upload Job Description (PDF/TXT)", 
                    type=["pdf", "txt"], 
                    key="jd_uploader",
                    label_visibility="visible"
                )

            # Logic Ekstraksi JD
            jd_extracted = None
            if jd_file:
                try:
                    if jd_file.type == "application/pdf":
                        jd_extracted = extract_text_from_pdf(jd_file)
                    else: # Text file
                        jd_extracted = jd_file.read().decode("utf-8")
                    
                    st.success(f"Berhasil memuat: {jd_file.name}")
                    
                    # Preview Konten JD
                    with st.expander("📄 Lihat Preview Konten JD"):
                        st.markdown(f"_{jd_extracted[:300]}..._")
                        
                except Exception as e:
                    st.error(f"Gagal membaca file: {e}")

        # LOGIC PENENTUAN JD 
        # Prioritas: File Upload > Manual Input
        if jd_file and jd_extracted:
            job_desc = jd_extracted
            # indikator File yang digunakan
            st.caption(f"Menggunakan Job Description dari file: **{jd_file.name}**")
        else:
            job_desc = jd_manual

    with col2:
        # RIGHT CARD: UPLOAD 
        st.markdown('### Candidate Hub')
        st.markdown('Upload CV kandidat (PDF) untuk dianalisis.')
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Drop PDF files here", 
            type=["pdf"], 
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        # Info Box
        st.info("""
        **💡 Tips untuk hasil terbaik:**
        - Pastikan format PDF dapat diseleksi teksnya (bukan scan gambar).
        - AI akan memprioritaskan 'Must-Have Skills' yang ada di JD.
        - Kapasitas maksimal: 200MB per file.
        """)

        # Action Button 
        st.markdown("<br>", unsafe_allow_html=True)
        process_btn = st.button("🚀 Start AI Analysis", use_container_width=True)

# RESULTS SECTION 
if process_btn and uploaded_files and job_desc:
    
    # AUTO SCROLL LOGIC  
    st.markdown('<div id="result_anchor"></div>', unsafe_allow_html=True)
    js_scroll = """
        <script>
            var element = window.parent.document.getElementById("result_anchor");
            if (element) {
                // Scroll halus ke elemen jangkar
                element.scrollIntoView({behavior: "smooth", block: "start"});
            }
        </script>
    """
    components.html(js_scroll, height=0) 

    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("Analysis Results")
    
    results_list = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, pdf_file in enumerate(uploaded_files):
        status_text.caption(f"Analyzing: {pdf_file.name}...")
        text_cv = extract_text_from_pdf(pdf_file)
        
        try:
            json_response = analyze_candidate(text_cv, job_desc)
            data = json.loads(json_response)
            data['filename'] = pdf_file.name
            results_list.append(data)
        except Exception as e:
            st.error(f"❌ Error processing {pdf_file.name}: {e}")
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    status_text.empty()
    progress_bar.empty()

    if results_list:
        df = pd.DataFrame(results_list)
        
        # Filtering Kolom
        summary_df = df[['candidate_name', 'match_score', 'hiring_decision', 'missing_critical_skills']]
        
        # Rename kolom 
        summary_df = summary_df.rename(columns={
            'candidate_name': 'Candidate Name',
            'match_score': 'Score',
            'hiring_decision': 'Status',
            'missing_critical_skills': 'Skill Gaps'
        })
        
        # Sort berdasarkan Score tertinggi
        summary_df = summary_df.sort_values(by='Score', ascending=False)
        
        # Styling Warna Status
        def highlight_decision(val):
            if val == 'Shortlist':
                color = '#4CAF50' # Green
            elif val == 'Potential':
                color = '#f59e0b' # Orange
            else:
                color = '#ef4444' # Red
            return f'color: {color}; font-weight: 700'
        
        # Render Table dengan Column Config
        st.dataframe(
            summary_df.style.map(highlight_decision, subset=['Status']), 
            use_container_width=True,
            hide_index=True, 
            column_config={
                "Candidate Name": st.column_config.TextColumn(
                    "Candidate Name",
                    width="medium",
                    help="Nama lengkap kandidat"
                ),
                "Score": st.column_config.ProgressColumn(
                    "Match Score",
                    help="Skor kecocokan (0-100)",
                    format="%d",
                    min_value=0,
                    max_value=100,
                    width="small"
                ),
                "Status": st.column_config.TextColumn(
                    "Decision",
                    width="small"
                ),
                "Skill Gaps": st.column_config.ListColumn(
                    "Missing Critical Skills",
                    width="large",
                    help="Skill wajib yang tidak ditemukan di CV"
                )
            }
        )

        # Personal Insights Section
        st.markdown("<br><h3>Personal Insights</h3>", unsafe_allow_html=True)
        
        # Menggunakan grid 2 kolom untuk kartu hasil agar tidak memanjang ke bawah terus
        for i, candidate in enumerate(results_list):

            # Warna tag expander berdasarkan status
            status_emoji = "🔴"
            if candidate['hiring_decision'] == "Shortlist": status_emoji = "🟢"
            elif candidate['hiring_decision'] == "Potential": status_emoji = "🟡"

            with st.expander(f"{status_emoji} {candidate['candidate_name']} — Score: {candidate['match_score']}/100"):
                c1, c2 = st.columns([1.2, 1.5], gap="large")
            
                # KOLOM KIRI
                with c1:
                    st.markdown("##### Executive Summary")
                    st.info(candidate['summary'])
                    
                    st.markdown("##### Culture Fit Analysis")
                    # Custom HTML Quote Box
                    st.markdown(f"""
                    <div class="culture-box">
                        {candidate['cultural_fit_analysis']}
                    </div>
                    """, unsafe_allow_html=True)

                # KOLOM KANAN
                with c2:
                    # Skill Gaps Pills
                    st.markdown("##### Missing Critical Skills")
                    
                    if candidate['missing_critical_skills']:
                        skills_html = '<div class="skill-pill-container">'
                        for skill in candidate['missing_critical_skills']:
                            skills_html += f"""
<div class="skill-pill">
    <span class="skill-icon">!</span> {skill}
</div>
"""
                        skills_html += '</div>'
                        st.markdown(skills_html, unsafe_allow_html=True)
                    else:
                        st.success("✅ Perfect Match! No critical skills missing.")
                        
                    # Spacer
                    st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)

                    # 2. Interview Prep Cards
                    st.markdown("##### Suggested Interview Questions")
                    
                    questions_html = ""
                    for idx, q in enumerate(candidate['interview_questions']):
                        questions_html += f"""
                        <div class="question-card">
                            <div class="question-header">Question {idx + 1}</div>
                            {q}
                        </div>
                        """
                    st.markdown(questions_html, unsafe_allow_html=True)

        # Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=" Export Report to CSV",
            data=csv,
            file_name='recruitmap_final_report.csv',
            mime='text/csv',
        )