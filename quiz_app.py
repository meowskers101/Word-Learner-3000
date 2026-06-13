import json
import os

import streamlit as st

QUIZ_FILE = "quiz.json"

# SpongeBob Themed CSS Styling
SPONGEBOB_CSS = """
<style>
    /* SpongeBob Yellow Theme */
    .spongebob-header {
        background: linear-gradient(135deg, #FFE135 0%, #FFD700 100%);
        padding: 30px;
        border-radius: 15px;
        border: 3px solid #4B0082;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .spongebob-title {
        color: #4B0082;
        font-size: 36px;
        margin-bottom: 10px;
    }
    
    .spongebob-question {
        background: linear-gradient(135deg, #E0F7FF 0%, #D0E8FF 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #FF6B00;
        margin: 20px 0;
    }
    
    .spongebob-success {
        background: #90EE90;
        color: #2D5016;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #228B22;
        margin: 10px 0;
    }
    
    .spongebob-error {
        background: #FFB6C6;
        color: #8B0000;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #FF1493;
        margin: 10px 0;
    }
</style>
"""


def load_quiz():
    if not os.path.exists(QUIZ_FILE):
        return None

    try:
        with open(QUIZ_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, IOError):
        return None


def normalize_answer(text):
    return text.strip().lower()


def main():
    st.set_page_config(page_title="SpongeBob's Vocabulary Quiz", layout="wide", page_icon="🍍")
    st.markdown(SPONGEBOB_CSS, unsafe_allow_html=True)
    
    # Header with SpongeBob theme
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: #4B0082; font-size: 48px;'>🧽 SpongeBob's Vocabulary Quest 🍍</h1>
        <p style='color: #FF6B00; font-size: 20px;'>Learn words while having fun in Bikini Bottom!</p>
    </div>
    """, unsafe_allow_html=True)
    
    quiz_data = load_quiz()
    if not quiz_data:
        st.warning(
            "❌ No quiz has been generated yet. Run `streamlit run wordsaver.py` and generate a quiz first."
        )
        return

    questions = quiz_data.get("questions", [])
    raw_text = quiz_data.get("raw_text")

    if not questions:
        st.warning("❌ The quiz file is missing structured questions.")
        if raw_text:
            st.markdown("### 📝 Raw quiz text")
            st.code(raw_text, language=None)
        return

    if "difficulty_selected" not in st.session_state:
        st.session_state.difficulty_selected = False
        st.session_state.difficulty = ""

    if not st.session_state.difficulty_selected:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #FFE135 0%, #FFD700 100%); 
                    padding: 30px; border-radius: 15px; border: 3px solid #4B0082; text-align: center;'>
            <h2 style='color: #4B0082;'>Pick Your Challenge Level! 🌊</h2>
            <p style='color: #FF6B00; font-size: 18px;'>SpongeBob is ready to learn with you!</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("difficulty_form"):
            difficulty = st.radio(
                "Select difficulty before loading the quiz:",
                ["🟢 Easy - Sandy's Level", "🟡 Medium - SpongeBob's Level", "🔴 Hard - Squidward's Challenge"],
                index=1,
            )
            start_button = st.form_submit_button("🚀 Load Questions & Start Quiz!")
            if start_button:
                st.session_state.difficulty_selected = True
                st.session_state.difficulty = difficulty

        st.info("📚 Pick a difficulty and click 'Load Questions' to begin your adventure!")
        return

    st.markdown(f"""
    <div style='background: #FFE135; padding: 15px; border-radius: 10px; border: 2px solid #4B0082; text-align: center;'>
        <h3 style='color: #4B0082; margin: 0;'>🎯 Current Level: {st.session_state.difficulty}</h3>
    </div>
    """, unsafe_allow_html=True)

    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    total_questions = len(questions)
    current_index = st.session_state.current_question
    question = questions[current_index]

    word = question.get("word", "")
    definition = question.get("definition", "")
    fill_sentence = question.get("fill_in_blank", "")
    mc_question = question.get("multiple_choice_question", "")
    choices = question.get("choices", [])

    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #E0F7FF 0%, #D0E8FF 100%); 
                padding: 15px; border-radius: 10px; border: 3px solid #4B0082;'>
        <h3 style='color: #4B0082; margin: 0;'>📝 Question {current_index + 1} of {total_questions}</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='spongebob-question'>
        <h3 style='color: #FF6B00;'>🎓 Word: {word}</h3>
    </div>
    """, unsafe_allow_html=True)

    if definition:
        st.markdown(f"""
        <div style='background: #FFF8DC; padding: 15px; border-radius: 10px; border-left: 4px solid #FF6B00;'>
            <p style='color: #4B0082;'><strong>📖 Definition:</strong> {definition}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.write("💭 Enter your own definition for the word, then answer the sentence below.")
        st.text_area(
            "Your definition",
            key=f"definition_answer_{current_index}",
            height=100,
        )

    if fill_sentence:
        st.markdown(f"""
        <div style='background: #FFFACD; padding: 15px; border-radius: 10px;'>
            <p style='color: #4B0082;'><strong>📚 Sentence:</strong> {fill_sentence}</p>
        </div>
        """, unsafe_allow_html=True)
        st.text_input("Your answer", key=f"fill_answer_{current_index}", placeholder="Type the missing word here...")

    if mc_question and choices:
        st.write(f"**Multiple choice:** {mc_question}")
        st.radio(
            "Select one answer:",
            options=choices,
            key=f"mc_answer_{current_index}",
            index=0 if choices else None,
        )

    nav_cols = st.columns([1, 1, 1])
    with nav_cols[0]:
        if st.button("Previous") and current_index > 0:
            st.session_state.current_question -= 1
    with nav_cols[1]:
        if st.button("Next") and current_index < total_questions - 1:
            st.session_state.current_question += 1
    with nav_cols[2]:
        if st.button("Submit all answers"):
            st.session_state.quiz_submitted = True

    if st.session_state.quiz_submitted:
        st.markdown("## Results")
        correct_count = 0

        for idx, question in enumerate(questions, start=1):
            word = question.get("word", "")
            definition = question.get("definition", "")
            fill_sentence = question.get("fill_in_blank", "")
            expected_fill = normalize_answer(question.get("fill_in_blank_answer", ""))
            mc_question = question.get("multiple_choice_question", "")
            choices = question.get("choices", [])
            mc_index = question.get("correct_choice_index")

            st.markdown(f"#### Question {idx}: {word}")
            user_definition = st.session_state.get(f"definition_answer_{idx - 1}", "")
            if user_definition:
                st.write(f"**Your definition:** {user_definition}")
            else:
                st.write("**Your definition:** _No answer provided._")

            if definition:
                st.write(f"**Expected definition:** {definition}")

            if fill_sentence:
                answer = normalize_answer(st.session_state.get(f"fill_answer_{idx - 1}", ""))
                if expected_fill and answer == expected_fill:
                    st.success("Fill-in answer: Correct")
                    correct_count += 1
                else:
                    st.error(
                        f"Fill-in answer: Incorrect. Correct answer: {question.get('fill_in_blank_answer', 'unknown')}"
                    )

            if mc_question and choices:
                mc_selected = st.session_state.get(f"mc_answer_{idx - 1}")
                correct_choice = None
                if isinstance(mc_index, int) and 0 <= mc_index < len(choices):
                    correct_choice = choices[mc_index]

                if correct_choice and mc_selected == correct_choice:
                    st.success("Multiple choice: Correct")
                    correct_count += 1
                else:
                    st.error(
                        f"Multiple choice: Incorrect. Correct answer: {correct_choice or 'unknown'}"
                    )

            st.markdown("---")

        st.markdown(f"### Score: {correct_count} / {len(questions)}")

    if raw_text:
        with st.expander("Show raw generated quiz text"):
            st.code(raw_text, language=None)


if __name__ == "__main__":
    main()
