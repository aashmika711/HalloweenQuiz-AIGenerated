import json, random
from typing import List, Dict, Any, Tuple, Optional

import gradio as gr
from openai import OpenAI

# ===== Model settings =====
MODEL_NAME = "GPT-5-nano"
TEMPERATURE = 0.7

CATEGORIES = [
    "General Halloween",
    "Horror Movies (Classic)",
    "Horror Movies (Modern)",
    "Urban Legends",
    "Monsters & Creatures",
    "Haunted Places",
    "Witchcraft & Folklore",
    "Kids-Friendly Spooky",
]

def get_openai_client() -> OpenAI:
    return OpenAI()

GEN_SYS_PROMPT = """You are a helpful quiz writer.
Return ONLY JSON that matches this schema exactly (no extra text):

{
  "topic": "string",
  "questions": [
    {
      "question": "string",
      "options": ["optA", "optB", "optC", "optD"],
      "correct_index": 0,
      "explanation": "string"
    }
  ]
}

Rules:
- Produce exactly N multiple-choice questions for the given topic.
- Each question MUST have exactly 4 options.
- correct_index must be 0..3.
- Keep questions fun, Halloween-themed (PG-13 / kid-safe).
"""

def category_to_topic(cat: str) -> str:
    mapping = {
        "General Halloween": "Halloween trivia (symbols, customs, history)",
        "Horror Movies (Classic)": "Classic horror movie trivia (1930s–1990s)",
        "Horror Movies (Modern)": "Modern horror movies (2000s–present) trivia",
        "Urban Legends": "Urban legends and spooky myths",
        "Monsters & Creatures": "famous monsters, vampires, werewolves, zombies, ghosts",
        "Haunted Places": "famous haunted houses and ghost stories",
        "Witchcraft & Folklore": "witches, folklore, rituals (safe content)",
        "Kids-Friendly Spooky": "kid-friendly spooky quiz with lighthearted tone",
    }
    return mapping.get(cat, "Halloween trivia")

def generate_questions_with_gpt(topic: str, n: int) -> Dict[str, Any]:
    client = get_openai_client()
    user_prompt = f"Topic: {topic}\nNumber of questions (N): {n}\nReturn ONLY JSON."
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            messages=[
                {"role": "system", "content": GEN_SYS_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.lower().startswith("json"):
                content = content[4:].strip()
        data = json.loads(content)
        return _validate_payload(data, n)
    except Exception as e:
        return _fallback_questions(topic, n, str(e))

def _validate_payload(data: Dict[str, Any], n: int) -> Dict[str, Any]:
    if not isinstance(data, dict) or "questions" not in data:
        return _fallback_questions("Halloween", n, "bad format")
    fixed = []
    for q in data["questions"]:
        question = str(q.get("question", "")).strip()
        opts = [str(o) for o in q.get("options", [])][:4]
        while len(opts) < 4: opts.append("N/A")
        if not question: continue
        fixed.append({
            "question": question,
            "options": opts,
            "correct_index": int(q.get("correct_index", 0)),
            "explanation": str(q.get("explanation", ""))
        })
    while len(fixed) < n: fixed.append(random.choice(fixed))
    return {"topic": data.get("topic", "Halloween"), "questions": fixed[:n]}

def _fallback_questions(topic: str, n: int, reason: str) -> Dict[str, Any]:
    base = [
        {"question": "Which creature transforms during a full moon?",
         "options": ["Vampire", "Werewolf", "Zombie", "Banshee"], "correct_index": 1,
         "explanation": "Werewolves transform under a full moon."},
        {"question": "Which vegetable was carved before pumpkins?",
         "options": ["Turnip", "Potato", "Beetroot", "Cabbage"], "correct_index": 0,
         "explanation": "Turnips were early jack-o’-lanterns."},
        {"question": "Which item repels vampires?",
         "options": ["Garlic", "Salt", "Rosemary", "Peppermint"], "correct_index": 0,
         "explanation": "Garlic is known to repel vampires."},
        {"question": "What date is Halloween?",
         "options": ["Nov 1", "Oct 31", "Oct 30", "Nov 2"], "correct_index": 1,
         "explanation": "Halloween is on October 31."},
    ]
    while len(base) < n: base.append(random.choice(base))
    return {"topic": topic, "questions": base[:n]}

# ===== Mechanics =====
MAX_FLIPS, MAX_PASSES, MAX_FIFTY = 1, 1, 1

def new_state(payload: Dict[str, Any]) -> Dict[str, Any]:
    qs = payload["questions"]
    idx = list(range(len(qs))); random.shuffle(idx)
    return {"topic": payload["topic"], "questions": qs, "queue": idx,
            "current": None, "score": 0, "asked": 0,
            "used_fifty": 0, "used_flip": 0, "used_pass": 0,
            "eliminated": set(), "last_feedback": "", "game_over": False}

def load_next(st):
    if not st["queue"]:
        st["current"], st["game_over"] = None, True; return None
    st["current"] = st["queue"][0]; st["eliminated"] = set()
    return st["questions"][st["current"]]

def apply_fifty(st):
    if st["used_fifty"] >= MAX_FIFTY: return False, "Already used 50-50."
    q = st["questions"][st["current"]]; c = q["correct_index"]
    wrong = [i for i in range(4) if i != c]; keep_wrong = random.choice(wrong)
    st["eliminated"] = set(i for i in range(4) if i not in {c, keep_wrong})
    st["used_fifty"] += 1; return True, "🍬 50-50 used! Two choices remain."

def apply_flip(st):
    if st["used_flip"] >= MAX_FLIPS: return False, "Already used Flip."
    if len(st["queue"]) <= 1: return False, "No more to flip."
    first = st["queue"].pop(0); st["queue"].append(first)
    st["used_flip"] += 1; load_next(st)
    return True, "🔄 Flipped! New question."

def apply_pass(st):
    if st["used_pass"] >= MAX_PASSES: return False, "Already used Pass."
    st["queue"].pop(0); st["asked"] += 1; st["used_pass"] += 1
    load_next(st); return True, "⏭️ Passed! Next question."

def submit_answer(st, sel):
    if sel is None: return False, "Pick an answer 🧠"
    q = st["questions"][st["current"]]
    mapping = [i for i in range(4) if i not in st["eliminated"]]
    if isinstance(sel, str):  # defensive: label → index among visible
        try: sel = [q["options"][i] for i in mapping].index(sel)
        except Exception: return False, "Invalid choice."
    if not (0 <= sel < len(mapping)): return False, "Invalid choice."
    picked = mapping[sel]; correct = q["correct_index"]

    if picked == correct:
        st["score"] += 1
        fb = f"<div class='badge ok'>✅ Correct! <span>{q['options'][correct]}</span></div>"
    else:
        fb = f"<div class='badge no'>❌ Wrong. <span>Correct: {q['options'][correct]}</span></div>"
    if q.get("explanation"):
        fb += f"<div class='note'>📝 {q['explanation']}</div>"

    st["queue"].pop(0); st["asked"] += 1; st["last_feedback"] = fb
    load_next(st); return True, fb

# ===== Pretty helpers =====
def _title(st):
    return f"🎃 {st['topic']} — Finished" if st["game_over"] else f"🎃 {st['topic']} — Question {st['asked']+1} of {len(st['questions'])}"

def _status(st):
    total = len(st["questions"])
    return f"Score: <b>{st['score']}</b> / {total} &nbsp;•&nbsp; Answered: <b>{st['asked']}</b>"

def _lifelines(st):
    return f"🍭 Lifelines — 50-50: {st['used_fifty']}/{MAX_FIFTY} &nbsp;|&nbsp; Flip: {st['used_flip']}/{MAX_FLIPS} &nbsp;|&nbsp; Pass: {st['used_pass']}/{MAX_PASSES}"

def _progress_html(st):
    total = max(1, len(st["questions"]))
    done = st["asked"]
    pct = int((done / total) * 100)
    pumpkins = "🎃" * min(10, max(1, round(pct/10)))
    return f"""
    <div class="bar"><div class="fill" style="width:{pct}%"></div></div>
    <div class="pumpkins">{pumpkins} <span>{pct}%</span></div>
    """

# ===== UI callbacks =====
def start_game(cat, count):
    topic = category_to_topic(cat)
    payload = generate_questions_with_gpt(topic, int(count))
    st = new_state(payload); q = load_next(st)
    if not q:
        return st, "", "", gr.update(choices=[], value=None), "No questions.", "", "", "", ""
    visible = [q["options"][i] for i in range(4)]
    return (st, _title(st), f"**Q:** {q['question']}",
            gr.update(choices=visible, value=None),
            "<div class='hint'>👻 Let’s play! Pick wisely.</div>",
            _status(st), _lifelines(st), _progress_html(st), "")

def on_submit(sel, st):
    if st is None:
        return None, "", "", gr.update(choices=[], value=None), "Click Start!", "", "", "", ""
    if st["game_over"] or st["current"] is None:
        return st, _title(st), "", gr.update(choices=[], value=None), "<div class='hint'>Game over. Restart!</div>", _status(st), _lifelines(st), _progress_html(st), "🕸️"

    ok, fb = submit_answer(st, sel)
    if not ok:
        q = st["questions"][st["current"]]; visible = [q["options"][i] for i in range(4) if i not in st["eliminated"]]
        return st, _title(st), f"**Q:** {q['question']}", gr.update(choices=visible), fb, _status(st), _lifelines(st), _progress_html(st), ""

    if st["current"] is None:
        return st, _title(st), "", gr.update(choices=[], value=None), fb + "<div class='yay'>🎉 Quiz Complete!</div>", _status(st), _lifelines(st), _progress_html(st), "🎉"

    q2 = st["questions"][st["current"]]; visible = [q2["options"][i] for i in range(4) if i not in st["eliminated"]]
    return st, _title(st), f"**Q:** {q2['question']}", gr.update(choices=visible, value=None), st["last_feedback"], _status(st), _lifelines(st), _progress_html(st), ""

def on_fifty(st):
    if st is None: return None, "", "", gr.update(choices=[], value=None), "Start first!", "", "", "", ""
    if st["game_over"] or st["current"] is None:
        return st, _title(st), "", gr.update(choices=[], value=None), "Game over.", _status(st), _lifelines(st), _progress_html(st), ""
    _, msg = apply_fifty(st)
    q = st["questions"][st["current"]]; visible = [q["options"][i] for i in range(4) if i not in st["eliminated"]]
    return st, _title(st), f"**Q:** {q['question']}", gr.update(choices=visible, value=None), f"<div class='hint'>{msg}</div>", _status(st), _lifelines(st), _progress_html(st), ""

def on_flip(st):
    if st is None: return None, "", "", gr.update(choices=[], value=None), "Start first!", "", "", "", ""
    if st["game_over"] or st["current"] is None:
        return st, _title(st), "", gr.update(choices=[], value=None), "Game over.", _status(st), _lifelines(st), _progress_html(st), ""
    _, msg = apply_flip(st)
    if st["current"] is None:
        return st, _title(st), "", gr.update(choices=[], value=None), msg, _status(st), _lifelines(st), _progress_html(st), ""
    q = st["questions"][st["current"]]; visible = [q["options"][i] for i in range(4)]
    return st, _title(st), f"**Q:** {q['question']}", gr.update(choices=visible, value=None), f"<div class='hint'>{msg}</div>", _status(st), _lifelines(st), _progress_html(st), ""

def on_pass(st):
    if st is None: return None, "", "", gr.update(choices=[], value=None), "Start first!", "", "", "", ""
    if st["game_over"] or st["current"] is None:
        return st, _title(st), "", gr.update(choices=[], value=None), "Game over.", _status(st), _lifelines(st), _progress_html(st), ""
    _, msg = apply_pass(st)
    if st["current"] is None:
        return st, _title(st), "", gr.update(choices=[], value=None), msg + "<div class='yay'>🎉 Done!</div>", _status(st), _lifelines(st), _progress_html(st), ""
    q = st["questions"][st["current"]]; visible = [q["options"][i] for i in range(4)]
    return st, _title(st), f"**Q:** {q['question']}", gr.update(choices=visible, value=None), f"<div class='hint'>{msg}</div>", _status(st), _lifelines(st), _progress_html(st), ""

# ===== UI =====
with gr.Blocks() as demo:
    gr.HTML("""
    <style>
  :root{
    --pumpkin:#ff7a00;
    --plum:#6c4ce6;
    --mint:#d8ffe6;
    --ink:#111;
    --ink2:#333;
    --card:#ffffff;
    --ok:#0fa958;
    --no:#e63946;
    --hint:#4c63d2;
  }

  body {
    background: linear-gradient(180deg, #fff 0%, #f7f7fb 100%);
    color: var(--ink);
  }

  /* ===== FIX: QUESTION VISIBILITY ===== */
  .qtext {
    color: #111111 !important;
    font-weight: 600;
  }

  .card {
    background: #000000 !important;
    border: 2px solid #e0e0e0 !important;
  }

  /* ===== FIX: SCORE / STATUS VISIBILITY ===== */
  .status,
.lifelines {
  color: #ffffff !important;  
  font-weight: 600;
  background: #000000 !important;
  padding: 6px 10px;            
  border-radius: 8px;           
}


  /* ===== RADIO OPTIONS (NO UI CHANGE) ===== */
  .gr-radio .wrap label {
    color: #2b1e5a !important;
    background: #faf7ff;
    border: 1px solid #ece5ff;
  }

  .gr-radio input:checked + label {
    color: #000000 !important;
  }

  /* ===== FEEDBACK ===== */
  .note {
    color: #2f3d4a !important;
  }

  .pumpkins {
    color: #111111 !important;
  }
</style>

    <div class="wrap">
      <div class="float-ghost">👻</div>
      <div class="float-bat">🦇</div>
      <div class="title"><h2>Halloween Quiz — Fun Edition</h2></div>
      <div class="subtitle">Pick a category & test your spooky smarts!</div>
    </div>
    """)

    with gr.Row():
        category = gr.Dropdown(CATEGORIES, value="General Halloween", label="Category")
        count = gr.Slider(5, 20, value=10, step=1, label="# Questions")

    state = gr.State()
    title_md = gr.Markdown()
    question_md = gr.Markdown(elem_classes=["card", "qtext"])
    options = gr.Radio(label="Choose an answer", choices=[], interactive=True, type="index")
    feedback_md = gr.HTML()           # allow colored badges
    status_md = gr.HTML(elem_classes=["status"])
    lifelines_md = gr.HTML(elem_classes=["lifelines"])
    progress_html = gr.HTML()         # pumpkin meter
    end_md = gr.Markdown()

    with gr.Row(elem_classes=["toprow"]):
        start_btn = gr.Button("🎲 Start Game", variant="primary", elem_classes=["primary"])
        submit_btn = gr.Button("Submit", elem_classes=["secondary"])
        fifty_btn = gr.Button("50-50", elem_classes=["secondary"])
        flip_btn = gr.Button("Flip", elem_classes=["secondary"])
        pass_btn = gr.Button("Pass", elem_classes=["secondary"])
        restart_btn = gr.Button("Restart", elem_classes=["secondary"])

    # wire
    start_btn.click(start_game, [category, count],
                    [state, title_md, question_md, options, feedback_md, status_md, lifelines_md, progress_html, end_md])
    restart_btn.click(start_game, [category, count],
                    [state, title_md, question_md, options, feedback_md, status_md, lifelines_md, progress_html, end_md])
    submit_btn.click(on_submit, [options, state],
                    [state, title_md, question_md, options, feedback_md, status_md, lifelines_md, progress_html, end_md])
    fifty_btn.click(on_fifty, [state],
                    [state, title_md, question_md, options, feedback_md, status_md, lifelines_md, progress_html, end_md])
    flip_btn.click(on_flip, [state],
                    [state, title_md, question_md, options, feedback_md, status_md, lifelines_md, progress_html, end_md])
    pass_btn.click(on_pass, [state],
                    [state, title_md, question_md, options, feedback_md, status_md, lifelines_md, progress_html, end_md])

if __name__ == "__main__":
    demo.launch(share=True)
