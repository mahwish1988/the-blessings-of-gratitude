import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
from PyPDF2 import PdfReader
import pandas as pd
from datetime import datetime
import openpyxl  # Required for Excel writing

# ------------------ Load API Key ------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# ------------------ Utility Functions ------------------

def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

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

# Specify your PDF file path here:
PDF_FILE_PATH = "the-blessings-of-gratitude.pdf"

# Extract text from the PDF using the path
pdf_text = extract_text_from_pdf(PDF_FILE_PATH)

def generate_answers(content, query):
    prompt = f"""
You are a helpful assistant trained to answer ONLY from the following content:

\"\"\" 
{content} 
\"\"\"

👋 I'm here to help only with what's inside *The Blessings of Gratitude* by Dawat-e-Islami. Could you please ask something related to thankfulness, Islamic teachings, or the topics covered in this booklet?

When answering, use the following format:

📌 Topic:
[Short summary]

📚 Key Islamic Teachings:
[Main teachings from the booklet, Qur'an, or Hadith]

🕌 Spiritual Reflection or Advice:
[Practical takeaway or spiritual advice based on Islamic guidance]

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

def save_feedback(rating, suggestion):
    feedback_file = "feedback.xlsx"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_new = pd.DataFrame({
        "Timestamp": [now],
        "Helpful": [rating],
        "Suggestion": [suggestion]
    })
    try:
        if os.path.exists(feedback_file):
            df_existing = pd.read_excel(feedback_file)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        df_combined.to_excel(feedback_file, index=False)
        st.success("✅ Feedback saved successfully.")
    except PermissionError:
        st.error("❌ Please close the feedback Excel file first.")
    except Exception as e:
        st.error(f"❌ Error saving feedback: {e}")

def save_open_feedback(feedback):
    feedback_file = "feedback_data.xlsx"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([[now, feedback]], columns=["Timestamp", "Feedback"])
    try:
        if os.path.exists(feedback_file):
            old_df = pd.read_excel(feedback_file)
            df = pd.concat([old_df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_excel(feedback_file, index=False)
        st.success("✅ Feedback saved. JazakAllah!")
    except PermissionError:
        st.error("❌ Please close the feedback Excel file first.")
    except Exception as e:
        st.error(f"❌ Error saving feedback: {e}")

# ------------------ Streamlit UI ------------------

st.set_page_config(page_title="🕌 The Blessings of Gratitude")

# Sidebar
with st.sidebar:
    st.header("📬 Contact")
    st.markdown("""
**Mahwish Kiran**  
📧 [mahwishpy@gmail.com](mailto:mahwishpy@gmail.com)  
🔗 [Facebook](https://www.facebook.com/share/1BBXjgbXPS/)  
🔗 [LinkedIn](https://www.linkedin.com/in/mahwish-kiran-842945353)  
    """)

# Main Title
st.title("🕌📖 The Blessings of Gratitude Chatbot")

# Load PDF Content
PDF_FILE_PATH = "the-blessings-of-gratitude.pdf"

if not os.path.exists(PDF_FILE_PATH):
    st.error("❌ PDF file not found. Please upload or check the filename.")
else:
    if 'pdf_content' not in st.session_state:
        st.session_state['pdf_content'] = extract_text_from_pdf(PDF_FILE_PATH)

    if st.session_state['pdf_content'].startswith("Error"):
        st.error(st.session_state['pdf_content'])
    else:
        user_query = st.text_input("💬 What would you like to ask from the booklet?")

        if 'helpful_feedback' not in st.session_state:
            st.session_state['helpful_feedback'] = None

        if st.button("🔍 Get Answer"):
            if user_query.strip() == "":
                st.warning("⚠️ Please type a question first.")
            else:
                answer = generate_answers(st.session_state['pdf_content'], user_query)
                st.subheader("📘 Answer:")
                st.markdown(answer)

                # Feedback radio
                st.markdown("### 😊 Was this helpful?")
                helpful = st.radio(
                    "Please choose an option:",
                    ("👍 Yes, very helpful", "👎 Not really"),
                    key="helpful_feedback"
                )

                if st.button("Submit Feedback on Answer"):
                    save_feedback(helpful, user_query)

        # Open-ended Feedback Section
        st.markdown("## 📝 Additional Feedback")
        feedback = st.text_area("✍️ Your thoughts:", height=150)
        if st.button("Submit Additional Feedback"):
            if feedback.strip():
                save_open_feedback(feedback)
            else:
                st.warning("⚠️ Please enter some feedback before submitting.")

        # Clear session
        if st.button("🔄 Clear All"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("✅ Session cleared.")

