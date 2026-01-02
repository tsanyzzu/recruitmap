import fitz  # PyMuPDF

def extract_text_from_pdf(uploaded_file):
    """
    Mengambil file object dari Streamlit dan mengembalikan string teks.
    """
    try:
        # Membaca file dari memory (stream)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return f"Error extracting text: {e}"