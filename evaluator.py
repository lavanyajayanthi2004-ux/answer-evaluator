import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader
import re

# ---------------- CONFIG ----------------
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    st.error("❌ GROQ_API_KEY not found")
    st.stop()

client = Groq(api_key=API_KEY)

st.set_page_config(page_title="Evaluator", layout="wide")
st.title("Answer Evaluator")
st.caption("View Questions • Correct Answers • Student Answers • Then Evaluate")

# ---------------- HELPERS ----------------
def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text.strip()

def clean_and_split(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Remove title line if it looks like a heading
    if lines[0].lower() in [
        "questions",
        "correct answers",
        "answers given by user",
        "student answers"
    ]:
        lines = lines[1:]

    cleaned_text = "\n".join(lines)

    parts = re.split(r"\n?\s*\d+\.\s*", cleaned_text)
    return [p.strip() for p in parts if p.strip()]


def evaluate_llm(q, ca, sa, q_no):
    prompt = f"""
You are an exam evaluator.
Always address the user as 'you'.

Question {q_no}:
{q}

Correct Answer:
{ca}

Student Answer:
{sa}

TASK:
- Decide if the answer is correct or incorrect
- If incorrect, explain WHY clearly
- Explain the correct concept simply
- Give marks out of 2

FORMAT:
Evaluation:
Explanation:
Marks:
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# ---------------- UI: Upload ----------------
st.subheader("📤 Upload PDFs")

col1, col2, col3 = st.columns(3)

with col1:
    q_pdf = st.file_uploader("📘 Questions PDF", type="pdf")

with col2:
    ca_pdf = st.file_uploader("✅ Correct Answers PDF", type="pdf")

with col3:
    sa_pdf = st.file_uploader("✍️ Student Answers PDF", type="pdf")

# ---------------- PROCESS ----------------
if q_pdf and ca_pdf and sa_pdf:
    questions = clean_and_split(read_pdf(q_pdf))
    correct_answers = clean_and_split(read_pdf(ca_pdf))
    student_answers = clean_and_split(read_pdf(sa_pdf))


    st.markdown("---")
    st.subheader("👀 Preview Before Evaluation")

    min_len = min(len(questions), len(correct_answers), len(student_answers))

    for i in range(min_len):
        with st.expander(f"Question {i+1}"):
            st.markdown(f"**Question:** {questions[i]}")
            st.markdown(f"**Correct Answer:** {correct_answers[i]}")
            st.markdown(f"**Student Answer:** {student_answers[i]}")

    st.markdown("---")

    if st.button("🧠 Evaluate Answers"):
        st.subheader("📊 Evaluation Result")

        total_marks = 0
        max_marks = min_len * 2

        for i in range(min_len):
            with st.spinner(f"Evaluating Question {i+1}..."):
                result = evaluate_llm(
                    questions[i],
                    correct_answers[i],
                    student_answers[i],
                    i + 1
                )

            st.markdown(f"### Question {i+1}")
            st.markdown(f"**Question:** {questions[i]}")
            st.markdown(f"**Correct Answer:** {correct_answers[i]}")
            st.markdown(f"**Student Answer:** {student_answers[i]}")
            st.markdown(result)

            # Extract marks
            try:
                marks_line = [l for l in result.splitlines() if "Marks" in l][0]
                marks = int(re.findall(r"\d+", marks_line)[0])
            except:
                marks = 0

            total_marks += marks
            st.markdown("---")

        st.markdown(
            f"## ✅ TOTAL MARKS: **{total_marks} / {max_marks}**"
        )
