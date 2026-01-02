from pydantic import BaseModel, Field
from typing import List

class ScreeningAnalysis(BaseModel):
    candidate_name: str = Field(description="Nama lengkap kandidat")
    match_score: int = Field(description="Skor kecocokan 0-100 berdasarkan JD")
    summary: str = Field(description="Ringkasan profil profesional kandidat singkat")
    must_have_check: List[str] = Field(description="Daftar skill wajib yang DIMILIKI kandidat")
    missing_critical_skills: List[str] = Field(description="Skill wajib yang TIDAK ditemukan/kurang")
    cultural_fit_analysis: str = Field(description="Analisa soft skill dan culture fit berdasarkan keywords di CV")
    interview_questions: List[str] = Field(description="3-5 pertanyaan teknis spesifik untuk memverifikasi skill yang diklaim")
    hiring_decision: str = Field(description="Saran keputusan: 'Shortlist', 'Potential', atau 'Reject'")