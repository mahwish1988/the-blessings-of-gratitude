import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
from PyPDF2 import PdfReader
import pandas as pd
from datetime import datetime
import openpyxl  # Required for Excel writing

# Load environment variables and API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Clean and preprocess text
def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    except Exception as e:
        return f"Error reading PDF: {e}"
    return clean_text(text)

# Gemini Q&A generation
def generate_answers(content, query):
    prompt = f"""
You are a helpful assistant trained to answer ONLY from the following content:

\"\"\" 
{content} 
\"\"\"

👋 I'm here to help only with what's inside The Blessings of Gratitude by Dawat-e-Islami. Could you please ask something related to thankfulness, Islamic teachings, or the topics covered in this booklet?
When answering, use the following clear format if possible:

📌 Topic:
[Short summary of the topic or section from the booklet]

📚 Key Islamic Teachings:
[Core points based on the content, with references to hadith or Quran if available]

🕌 Spiritual Reflection or Advice:
[Practical takeaway, spiritual advice, or moral action based on Islamic guidance]
**{query}**
"""
    try:
        response = model.generate_content(prompt)
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                parts = getattr(candidate.content, 'parts', [])
                return parts[0].text if parts else candidate.content.text
        return "No answer generated."
    except Exception as e:
        return f"Error: {str(e)}"

# Save feedback from radio buttons (helpful or not)
def save_feedback(rating, suggestion):
    feedback_file = "feedback.xlsx"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback_data = {
        "Timestamp": [now],
        "Helpful": [rating],
        "Suggestion": [suggestion]
    }
    df_new = pd.DataFrame(feedback_data)
    try:
        if os.path.exists(feedback_file):
            df_existing = pd.read_excel(feedback_file)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_excel(feedback_file, index=False)
        st.success(f"✅ Feedback saved successfully!\n📁 Saved at: `{os.path.abspath(feedback_file)}`")
    except PermissionError:
        st.error("❌ Permission denied: Please close the feedback Excel file if it is open.")
    except Exception as e:
        st.error(f"❌ Error saving feedback: {e}")

# Save open-form textual feedback
def save_open_feedback(feedback):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([[now, feedback]], columns=["Timestamp", "Feedback"])
    feedback_file = "feedback_data.xlsx"
    try:
        if os.path.exists(feedback_file):
            old_df = pd.read_excel(feedback_file)
            df = pd.concat([old_df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_excel(feedback_file, index=False)
        st.success("✅ Feedback saved successfully! Thank you for your input.")
    except PermissionError:
        st.error("❌ Permission denied: Please close the feedback Excel file if it is open.")
    except Exception as e:
        st.error(f"❌ Error saving feedback: {e}")

# Set up Streamlit
st.set_page_config(page_title="Preprimary Syllabus Assistant")

# Sidebar Contact Info
with st.sidebar:
    st.header("📬 Get in Touch")
    st.markdown("""
**Mahwish Kiran**  
📧 [mahwishpy@gmail.com](mailto:mahwishpy@gmail.com)  
🔗 [Facebook](https://www.facebook.com/share/1BBXjgbXPS/)  
🔗 [LinkedIn](https://www.linkedin.com/in/mahwish-kiran-842945353)  

_Made with ❤️ for every child's first step._
    """)

# Main Title & Intro
st.title("🕌📖The-blessings-of-gratitude by Dawat-e-islami")

# Load PDF content
PDF_FILE_PATH = r"the-blessings-of-gratitude.pdf"

if 'pdf_content' not in st.session_state:
    st.session_state['pdf_content'] = extract_text_from_pdf(PDF_FILE_PATH)

if st.session_state['pdf_content'].startswith("Error"):
    st.error(st.session_state['pdf_content'])

# User query
user_query = st.text_input("💬 What would you like to know?")

# Store feedback radio choice in session state to avoid re-selection after rerun
if 'helpful_feedback' not in st.session_state:
    st.session_state['helpful_feedback'] = None

# Q&A Answer Section
if st.button("🔍 Get Answer") and st.session_state['pdf_content']:
    if user_query.strip() == "":
        st.warning("Oops! Please type your question before clicking.")
    else:
        answer = generate_answers(st.session_state['pdf_content'], user_query)
        st.subheader("📘 Here's what I found:")
        st.markdown(answer)

        # Feedback radio
        st.markdown("### 😊 Was this helpful for you?")
        helpful = st.radio("Please choose an option:", ("👍 Yes, it was super helpful!", "👎 Hmm, not really."), index=0, key="helpful_feedback")

        # Save feedback button for radio feedback
        if st.button("Submit Feedback on Answer"):
            save_feedback(helpful, user_query)

# ------------------------------------
# 📝 Additional Feedback Section (open-form)
# ------------------------------------
st.markdown("## 📝 Additional Feedback Section")

st.subheader("✍️ Feedback")
feedback = st.text_area("Tell us what you think (max 500 words):", height=150)

if st.button("Submit Additional Feedback"):
    if feedback.strip():
        save_open_feedback(feedback)
    else:
        st.warning("⚠️ Please enter feedback before submitting.")

# Clear all session state and inputs
if st.button("Clear All Inputs"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("All inputs cleared.")
