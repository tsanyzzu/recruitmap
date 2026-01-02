import streamlit as st
import pandas as pd
import json
from modules.pdf_loader import extract_text_from_pdf
from modules.ai_engine import analyze_candidate

# Setup Halaman
st.set_page_config(page_title="RecruitMap AI", layout="wide")

st.title("RecruitMap: AI-Powered Talent Screening")
st.markdown("Automating Analysis and Shortlisting of Talent Acquisition Workflow.")

# SIDEBAR: INPUT 
st.sidebar.header("1. Define Role")
with open("data/job_desc.txt", "r") as f: # Default value (data/job_desc.txt)
    default_jd = f.read()

job_desc = st.sidebar.text_area("Job Description (Must-haves & Soft Skills)", value=default_jd, height=300)

st.sidebar.header("2. Upload Candidates ")
uploaded_files = st.sidebar.file_uploader("Upload CV (PDF)", type=["pdf"], accept_multiple_files=True)

process_btn = st.sidebar.button("Analyze Candidates 🔍")

# OUTPUT 
if process_btn and uploaded_files and job_desc:
    st.divider()
    st.subheader("Screening Results & Shortlist")
    
    results_list = []
    progress_bar = st.progress(0)
    
    for i, pdf_file in enumerate(uploaded_files):
        text_cv = extract_text_from_pdf(pdf_file)
        try:
            json_response = analyze_candidate(text_cv, job_desc)
            data = json.loads(json_response) # Convert JSON string to Dict
            
            # Status visual untuk tabel
            data['filename'] = pdf_file.name
            results_list.append(data)
            
        except Exception as e:
            st.error(f"Error processing {pdf_file.name}: {e}")
        progress_bar.progress((i + 1) / len(uploaded_files)) # Update progress bar

    if results_list:
        # Konversi ke Pandas DataFrame untuk tabel ringkasan
        df = pd.DataFrame(results_list)
        
        # Filtering kolom untuk tabel utama 
        summary_df = df[['candidate_name', 'match_score', 'hiring_decision', 'missing_critical_skills']]
        
        # Sort berdasarkan Score tertinggi
        summary_df = summary_df.sort_values(by='match_score', ascending=False)
        
        # Tampilkan Dataframe dengan highlight
        def highlight_decision(val):
            color = 'green' if val == 'Shortlist' else 'orange' if val == 'Potential' else 'red'
            return f'color: {color}; font-weight: bold'
        
        st.dataframe(
            summary_df.style.map(highlight_decision, subset=['hiring_decision']), 
            use_container_width=True 
        )

        # DETAIL VIEW & EXPORT 
        st.subheader("Detailed Screening Notes")
        
        for candidate in results_list:
            # Expander untuk setiap kandidat
            with st.expander(f"{candidate['candidate_name']} (Score: {candidate['match_score']}) - {candidate['hiring_decision']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Summary:**")
                    st.info(candidate['summary'])
                    st.markdown("**Cultural Fit Analysis:**")
                    st.write(candidate['cultural_fit_analysis'])
                    
                with col2:
                    st.markdown("**Missing Critical Skills:**")
                    for skill in candidate['missing_critical_skills']:
                        st.error(f"- {skill}")
                    
                    st.markdown("**Suggested Interview Questions (STAR Method Prep):**")
                    for q in candidate['interview_questions']:
                        st.write(f"- {q}")

        # Download Report Button 
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Recruitment Report (CSV)",
            data=csv,
            file_name='recruitmap_screening_report.csv',
            mime='text/csv',
        )