import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from modules.schema import ScreeningAnalysis

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("BACKUP_GEMINI_API_KEY")
MODEL_NAME = "gemini-3-flash-preview"

def analyze_candidate(cv_text, job_desc_text):
    """
    fungsi untuk menganalisis CV kandidat terhadap deskripsi pekerjaan menggunakan Google Gemini API.
    
    :param cv_text: text CV dari hasil ekstraksi
    :param job_desc_text: deskripsi pekerjaan dalam bentuk text
    :return: JSON string berisi analisis sesuai schema ScreeningAnalysis
    """ 
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
        You are a Senior Talent Acquisition Specialist.
        
        JOB DESCRIPTION:
        {job_desc_text}
        
        CANDIDATE CV TEXT:
        {cv_text}
        
        INSTRUCTIONS:
        1. Analyze match based on Must-Have skills first.
        2. Provide a strict scoring (0-100).
        3. Determine hiring decision.
        """

        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ScreeningAnalysis
            )
        )

        if response.parsed:
            return response.parsed.model_dump_json()
        else:
            raise ValueError("Empty response from AI")

# Error handling
    except Exception as e:
        error_response = {
            "candidate_name": "System Error",
            "match_score": 0,
            "summary": f"Error Details: {str(e)}",
            "must_have_check": [],
            "missing_critical_skills": [],
            "cultural_fit_analysis": "N/A",
            "interview_questions": [],
            "hiring_decision": "Reject"
        }
        return json.dumps(error_response)