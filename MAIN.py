import streamlit as st
import json
import os
import re
import random
import requests
import quiz_app
from dotenv import load_dotenv
from openai import OpenAI



load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print("API KEY:", api_key)

client = OpenAI(api_key=api_key)

JSON_FILE = "Users.json"
LEGACY_JSON_FILE = "users.json"
WORDS_FILE = "words.json"
QUIZ_FILE = "quiz.json"

SPONGEBOB_CSS = """
<style>
    body {
        background: linear-gradient(135deg, #8B4513 0%, #A0522D 50%, #8B4513 100%);
        background-attachment: fixed;
    }
    .main {
        background: linear-gradient(135deg, #8B4513 0%, #A0522D 50%, #8B4513 100%);
    }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #8B4513 0%, #A0522D 50%, #8B4513 100%);
    }
    .krusty-krab-header {
        background: linear-gradient(135deg, #DC143C 0%, #8B0000 100%);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        border: 8px solid #DAA520;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        margin-bottom: 30px;
    }
    .krusty-sign {
        color: #FFD700;
        font-size: 60px;
        font-weight: bold;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
        margin: 0;
        letter-spacing: 2px;
    }
    .spongebob-guide {
        background: linear-gradient(135deg, #FFFF00 0%, #FFD700 100%);
        padding: 25px;
        border-radius: 15px;
        border: 4px solid #FF6B00;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .spongebob-speech {
        color: #4B0082;
        font-size: 18px;
        font-weight: bold;
        margin: 10px 0;
    }
    .spongebob-instructions {
        background: linear-gradient(135deg, #FFE135 0%, #FFD700 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #FF6B00;
        margin: 15px 0;
        color: #4B0082;
    }
    .form-container {
        background: linear-gradient(135deg, #FFF8DC 0%, #FFFACD 100%);
        padding: 30px;
        border-radius: 15px;
        border: 4px solid #DAA520;
        margin-top: 20px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #FF6B00 0%, #FF8C00 100%);
        color: white;
        border: 3px solid #4B0082;
        font-weight: bold;
        border-radius: 15px;
        padding: 12px 30px;
        font-size: 16px;
    }
</style>
"""


def get_user_file_path():
    return JSON_FILE if os.path.exists(JSON_FILE) else LEGACY_JSON_FILE

def load_users():
    path = get_user_file_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        users = {}
        for username, user_data in data.items():
            if isinstance(user_data, dict) and "password" in user_data:
                users[username] = user_data
            else:
                users[username] = {"password": user_data}
        return users
    return {}

def save_users(users_data):
    with open(get_user_file_path(), "w", encoding="utf-8") as f:
        json.dump(users_data, f, indent=4)


def load_words(username):
    if not os.path.exists(WORDS_FILE):
        return []
    try:
        with open(WORDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
    raw = data.get(username, []) if isinstance(data, dict) else []
    words = []
    for item in raw:
        if isinstance(item, dict) and "word" in item:
            words.append({
                "word": str(item.get("word", "")).strip(),
                "definition": str(item.get("definition", "")).strip(),
            })
    return [w for w in words if w["word"]]

def save_words(username, words):
    data = {}
    if os.path.exists(WORDS_FILE):
        try:
            with open(WORDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {}
    if not isinstance(data, dict):
        data = {}
    data[username] = words
    with open(WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_quiz(questions):
    with open(QUIZ_FILE, "w", encoding="utf-8") as f:
        json.dump({"questions": questions}, f, indent=2, ensure_ascii=False)


DIFFICULTY_PROMPTS = {
    "easy": """You are generating an EASY vocabulary quiz for young students.
- Fill-in-the-blank sentences should be simple and give lots of context clues.
- Multiple choice distractors should be obviously wrong (very different meanings).
- Use simple, everyday sentence contexts.""",

    "medium": """You are generating a MEDIUM difficulty vocabulary quiz.
- Fill-in-the-blank sentences should give moderate context clues.
- Multiple choice distractors should be plausible but clearly distinguishable.
- Use varied sentence contexts.""",

    "hard": """You are generating the HARDEST POSSIBLE vocabulary quiz. Make it extremely challenging:
- Fill-in-the-blank sentences must give MINIMAL context clues. The sentence should work with multiple words but only be truly correct with the target word.
- Multiple choice distractors must be VERY similar in meaning (near-synonyms, related concepts) — never obviously wrong words.
- Use advanced, complex sentence structures with academic or literary contexts.
- The correct answer should require deep understanding of the precise meaning, not just a vague idea.
- Every question should feel genuinely difficult even for someone who studied.
- RULE: 1 WORD HINTS FOR THE WORD AND THERE IS 2 QUESTIONS FOR EACH WORD, 1 IS A FILL IN THE BLANK, ANOTHER IS A MULTIPLE CHOICE"""
}

def generate_quiz_with_ai(words, difficulty="medium"):
    all_words = [w["word"] for w in words]
    
    difficulty_key = "medium"
    if "Easy" in difficulty:
        difficulty_key = "easy"
    elif "Hard" in difficulty:
        difficulty_key = "hard"

    system_prompt = DIFFICULTY_PROMPTS[difficulty_key]

    word_list_str = "\n".join([f'- {w["word"]}: {w["definition"]}' for w in words])
    
    
    seed_phrases = [
        "Use completely fresh sentences never seen before.",
        "Invent brand new contexts for every question.",
        "Create novel scenarios for each sentence.",
        "Generate unique examples unlike any standard textbook.",
        "Use original, creative sentences throughout.",
    ]
    seed = random.choice(seed_phrases)

    user_prompt = f"""{seed}

Here are the vocabulary words and their definitions:
{word_list_str}

Generate one quiz question per word. Return ONLY a valid JSON object with this exact structure:
{{
  "questions": [
    {{
      "word": "the word",
      "definition": "the definition",
      "fill_in_blank": "A sentence with ____ where the word belongs.",
      "fill_in_blank_answer": "the word",
      "multiple_choice_question": "A question asking which word fits a description or context?",
      "choices": ["correct_word", "distractor1", "distractor2", "distractor3"],
      "correct_choice_index": 0
    }}
  ]
}}

Rules:
- choices array must always have exactly 4 items
- correct_choice_index is always 0 (shuffle order randomly yourself)
- fill_in_blank must contain exactly one ____
- Return ONLY the JSON, no markdown, no explanation"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=1.0,  
            max_tokens=2000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        text = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"```$", "", text.strip())

        parsed = json.loads(text)
        questions = parsed.get("questions", [])

        for q in questions:
            choices = q.get("choices", [])
            correct = choices[q.get("correct_choice_index", 0)]
            random.shuffle(choices)
            q["choices"] = choices
            q["correct_choice_index"] = choices.index(correct)

        random.shuffle(questions)

        return questions, None

    except (json.JSONDecodeError, KeyError) as e:
        return None, f"Could not parse AI response: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


for key, default in [
    ("logged_in", False),
    ("username", ""),
    ("page_state", "entrance"),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def show_entrance_page():
    st.markdown(SPONGEBOB_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class='krusty-krab-header'>
        <p style='margin: 0; font-size: 30px;'>⚓ Welcome to ⚓</p>
        <p class='krusty-sign'>Krusty's Learning Center</p>
        <p style='margin: 0; font-size: 20px; color: #FFD700;'>Est. 1986 • Bikini Bottom's Finest Establishment</p>
    </div>
    """, unsafe_allow_html=True)




    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Your Adventure!", use_container_width=True, key="start_btn"):
            st.session_state.page_state = "login"
            st.rerun()


def show_login_page():
    st.markdown(SPONGEBOB_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class='krusty-krab-header'>
        <p style='margin: 0; font-size: 30px;'>⚓ Krusty's Learning Center ⚓</p>
        <p style='margin: 10px 0; font-size: 18px; color: #FFD700;'>Bikini Bottom's Most Original and Complex Establishment</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Back"):
        st.session_state.page_state = "entrance"
        st.rerun()

    st.markdown("""
    <div class='spongebob-guide'>
        <div style='font-size: 50px; margin-bottom: 10px;'>🧽</div>
        <p class='spongebob-speech'>Let's Get Started!</p>
        <p style='color: #4B0082; font-size: 16px;'>Login or Create a Account to Get Started!!!</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='form-container'>
        <h3 style='color: #DC143C; text-align: center;'> LOGIN </h3>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        submit_button = st.form_submit_button("Login", use_container_width=True)
        if submit_button:
            users = load_users()
            if username in users and users[username].get("password") == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page_state = "words"
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Hmm... that username or password isn't right.")

    st.markdown("---")

    st.markdown("""
    <div class='spongebob-guide' style='margin-top: 30px;'>
        <div style='font-size: 40px; margin-bottom: 10px;'>✨</div>
        <p class='spongebob-speech'>Don't have an account yet?</p>
    </div>
    <div class='form-container'>
        <h3 style='color: #DC143C; text-align: center;'>⭐ CREATE NEW ACCOUNT ⭐</h3>
    </div>
    """, unsafe_allow_html=True)

    with st.form("signup_form"):
        new_username = st.text_input("Choose a Username", placeholder="Your awesome username", key="signup_user")
        new_password = st.text_input("Choose a Password", type="password", placeholder="Your secret password", key="signup_pass")
        signup_button = st.form_submit_button("⭐ Create My Account", use_container_width=True)
        if signup_button:
            users = load_users()
            if not new_username.strip() or not new_password.strip():
                st.error("❌ Username and password cannot be blank!")
            elif new_username in users:
                st.error("❌ That username is already taken!")
            else:
                users[new_username] = {"password": new_password}
                save_users(users)
                st.success(" Account created! Please log in above.")


def show_words_page():
    st.markdown(SPONGEBOB_CSS, unsafe_allow_html=True)
    username = st.session_state.username

    st.markdown("""
    <div class='krusty-krab-header'>
        <p style='margin: 0; font-size: 30px;'>📝 WORD LEARNING 📝</p>
        <p style='margin: 10px 0; font-size: 18px; color: #FFD700;'>Add your vocabulary words & definitions</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='spongebob-guide'>
        <div style='font-size: 40px; margin-bottom: 10px;'>🧽</div>
        <p class='spongebob-speech'>Welcome, {username}! Let's add some words!</p>
        <p style='color: #4B0082; font-size: 14px;'>Add all your vocabulary words and definitions below. When ready, pick a difficulty and generate your quiz!</p>
    </div>
    """, unsafe_allow_html=True)

    words = load_words(username)

    st.markdown("""
    <div class='form-container'>
        <h3 style='color: #DC143C; text-align: center;'>Add Word</h3>
    </div>
    """, unsafe_allow_html=True)

    with st.form("add_word_form", clear_on_submit=True):
        new_word = st.text_input("Word", placeholder="Enter vocabulary word")
        new_definition = st.text_area("Definition", placeholder="Enter the definition", height=80)
        add_button = st.form_submit_button("Add Word", use_container_width=True)

        if add_button:
            word_text = new_word.strip()
            definition_text = new_definition.strip()
            if not word_text:
                st.error("❌ Please enter a word!")
            elif not definition_text:
                st.error("❌ Please enter a definition!")
            elif any(w["word"].lower() == word_text.lower() for w in words):
                st.warning("⚠️ That word is already in your list!")
            else:
                words.append({"word": word_text, "definition": definition_text})
                save_words(username, words)
                st.success(f"✅ '{word_text}' added!")
                st.rerun()

    if words:
        st.markdown("---")
        st.markdown("""
        <div class='spongebob-instructions'>
            <h3 style='color: #FF6B00; margin-top: 0;'>Your Word List</h3>
        </div>
        """, unsafe_allow_html=True)

        for i, word_item in enumerate(words):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{i+1}. {word_item['word']}** — {word_item['definition']}")
            with col2:
                if st.button("🗑️", key=f"delete_{i}"):
                    words.pop(i)
                    save_words(username, words)
                    st.rerun()

        st.markdown("---")

        st.markdown("""
        <div style='background: linear-gradient(135deg, #FFE135 0%, #FFD700 100%);
                    padding: 20px; border-radius: 15px; border: 3px solid #4B0082; text-align: center;'>
            <h3 style='color: #4B0082; margin: 0;'>🎯 Choose Your Difficulty</h3>
            <p style='color: #FF6B00; margin: 5px 0 0 0;'>AI generates unique questions every time!</p>
        </div>
        """, unsafe_allow_html=True)

        difficulty = st.radio(
            "Select difficulty:",
            ["🟢 Easy ", "🟡 Medium ", "🔴 Hard "],
            index=1,
            label_visibility="collapsed"
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Generate Quiz & Start!", use_container_width=True):
                with st.spinner("🧽 SpongeBob is cooking up your questions..."):
                    questions, error = generate_quiz_with_ai(words, difficulty)
                if error:
                    st.error(f"❌ Could not generate quiz: {error}")
                elif questions:
                    save_quiz(questions)
                    # Reset quiz state so it starts fresh
                    for key in ["difficulty_selected", "difficulty", "current_question", "quiz_submitted"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.difficulty_selected = True
                    st.session_state.difficulty = difficulty
                    st.session_state.page_state = "quiz"
                    st.rerun()
                else:
                    st.error("❌ No questions were returned. Please try again.")
    else:
        st.info("No words yet! Add Words!!!")

    st.markdown("---")
    if st.button("Log Out 🥺🤞🥀"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.page_state = "entrance"
        st.rerun()



def main():
    st.set_page_config(
        page_title="🍍 Krusty's Learning Center 🍍",
        page_icon="🍍",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    if st.session_state.page_state == "entrance":
        show_entrance_page()
    elif st.session_state.page_state == "login":
        show_login_page()
    elif st.session_state.page_state == "words":
        show_words_page()
    elif st.session_state.page_state == "quiz":
        quiz_app.main()



if __name__ == "__main__":
    main()