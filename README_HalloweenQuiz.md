# Halloween Quiz – Fun Edition 🎃

## Project Overview

Halloween Quiz is an interactive, AI-powered multiple-choice quiz application built with **Python, Gradio, and the OpenAI API**. Users can choose a Halloween-related category, select the number of questions, and test their knowledge through a spooky quiz experience.

The application generates questions dynamically using an OpenAI model. It also includes lifelines such as **50-50**, **Flip**, and **Pass**, along with score tracking, answer explanations, and a progress indicator.

## Features

- **Multiple quiz categories:** General Halloween, classic and modern horror movies, urban legends, monsters and creatures, haunted places, witchcraft and folklore, and kid-friendly spooky topics.
- **AI-generated questions:** Generates multiple-choice questions based on the selected category.
- **Custom question count:** Choose between 5 and 20 questions.
- **Four answer choices:** Each question is presented with four options.
- **Instant feedback:** Shows whether the selected answer is correct and displays an explanation when available.
- **Score tracking:** Keeps track of the score and number of questions answered.
- **Lifelines:**
  - **50-50:** Removes two incorrect options.
  - **Flip:** Moves the current question to the end and displays another question.
  - **Pass:** Skips the current question.
- **Progress indicator:** Displays quiz progress with a pumpkin-themed progress meter.
- **Fallback questions:** Provides built-in Halloween questions if AI question generation fails.
- **Restart option:** Start a new quiz with the selected category and question count.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic and quiz mechanics |
| Gradio | Interactive web interface |
| OpenAI API | Dynamic quiz question generation |
| JSON | Structured question and answer data |

## Project Structure

```text
project-halloweenQuiz/
│
├── HalloweenQuiz.py   # Main application: AI question generation, quiz logic, and Gradio UI
└── README.md          # Project documentation
```

## Requirements

- Python 3.9 or later
- An OpenAI API key
- Internet connection for AI question generation

## Installation and Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd project-halloweenQuiz
```

### 2. Install dependencies

```bash
pip install gradio openai
```

### 3. Configure your OpenAI API key

The application uses the OpenAI Python client, which reads the API key from the `OPENAI_API_KEY` environment variable.

**Windows PowerShell:**

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

**macOS / Linux:**

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Keep your API key private. Do not paste it directly into the source code or commit it to GitHub.

### 4. Run the application

```bash
python HalloweenQuiz.py
```

Gradio will start the application and display a local URL in the terminal. Open that URL in your browser to play the quiz.

The script is configured with `share=True`, so Gradio may also generate a temporary public sharing link. Avoid sharing sensitive information through a public demo.

## How to Play

1. Open the application in your browser.
2. Select a Halloween quiz category.
3. Choose the number of questions (5–20).
4. Click **Start Game**.
5. Select one of the four answer options and click **Submit**.
6. Read the feedback and explanation.
7. Use the available lifelines when needed:
   - **50-50** to narrow the choices.
   - **Flip** to move to another question.
   - **Pass** to skip a question.
8. Complete the quiz and review your final score.
9. Click **Restart** to play again.

Each lifeline can be used once per game.

## AI Question Generation

The application sends the selected topic and requested question count to the configured OpenAI model. The model is instructed to return structured JSON containing:

- Quiz topic
- Question text
- Four answer options
- Correct answer index
- Explanation

The response is validated before being used by the quiz. If generation or response parsing fails, the application uses its built-in fallback questions.

## Learning Outcomes

This project demonstrates practical experience with:

- Python application development
- Integrating the OpenAI API
- Prompt engineering for structured AI output
- JSON parsing and response validation
- Managing quiz state and user interactions
- Building interactive interfaces with Gradio
- Implementing game logic, scoring, and lifelines
- Handling API or response-generation failures with fallback data

## Future Improvements

- Add user accounts and a leaderboard.
- Save quiz history and scores.
- Add difficulty levels.
- Support more quiz themes and languages.
- Add a timer and per-question scoring.
- Improve question validation and duplicate-question handling.

## Author

**[Your Name]**

---

*An interactive Halloween quiz project built with Python, Gradio, and the OpenAI API.*
