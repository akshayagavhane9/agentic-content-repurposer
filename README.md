# 🤖 Agentic Content Repurposer

A multi-agent AI system that transforms a single content brief into optimized posts for **LinkedIn, Instagram, and Email**.  
Built using an agentic workflow with a custom quality scoring tool, refinement engine, and evaluation system.

---

## 📌 1. Overview

This project demonstrates how to design and orchestrate an **Agentic AI system** with:

- Multiple cooperating agents  
- Tool integration (custom + built-in)  
- Memory + state-driven workflow  
- Automated quality scoring  
- Self-improvement refinement loops  
- Test logging + evaluation charts  

This system is production-ready, modular, and fully aligned with the **Building Agentic Systems** assignment rubric.

---

## 📌 2. Features

### 🔹 Multi-Agent Architecture
- **Controller Agent** – coordinates everything  
- **Strategy Agent** – extracts key points, tone, audience  
- **Master Draft Writer** – produces a neutral long-form draft  
- **Platform Styling Agent** – specializes content per platform  
- **Quality Reviewer Agent** – evaluates each output  

### 🔹 Custom Quality Scoring Tool
Evaluates:
- hook strength  
- clarity  
- tone match  
- CTA strength  
- length appropriateness  
- hashtag richness (Instagram only)  

### 🔹 Self-Improvement Engine
If any score < **0.85**, system automatically refines:

```
=== SELF-IMPROVEMENT REFINEMENTS ===
[REFINEMENT] LinkedIn improved from 0.82 → 0.89 (Δ=0.07)
```

### 🔹 Automatic Test Logging
Each run appends to:

```
evaluation/test_results.csv
```


### 🔹 Quality Graph Generator
Produces visual performance chart:

```
evaluation/quality_scores.png
```
---
## 📌 3. Architecture Diagram
The Agentic Content Repurposer follows a multi-agent orchestration pipeline:

<p align="center">
  <img src="Untitled diagram-2025-11-20-191145.png" width="800">
</p>





## 🛠 4. Tech Stack

- **Python 3.10+**
- **OpenAI GPT-4o / GPT-4.1**
- **CrewAI-style multi-agent orchestration**
- **dotenv** for environment variable management
- **Matplotlib** for performance charts
- **Pandas** for evaluation logging
- **Retry logic + error-safe wrappers** for robust execution

---
## 📌 5. Project Structure

```
agentic-content-repurposer/
│
├── src/
│ ├── main.py
│ ├── agents.py
│ ├── tools.py
│ ├── config.py
│
├── evaluation/
│ ├── test_results.csv
│ ├── generate_graphs.py
│
├── .env
├── requirements.txt
└── README.md

```

## 🔄 6. Workflow Overview (How the system works)

1. User enters a short content brief.
2. Strategy Agent analyzes tone, audience, and messaging.
3. Draft Writer generates a universal long-form draft.
4. Platform Agents transform the draft for:
   - LinkedIn
   - Instagram (+ hashtags)
   - Email
5. Quality Scoring Tool evaluates each output across multiple dimensions.
6. If a score falls below threshold (0.85), refinement is automatically triggered.
7. Improved output replaces the weaker version.
8. All results are logged to `evaluation/test_results.csv`.
9. Quality graph generator creates visual performance reports.

---

## 📌 7. Installation

### 1. Clone repo
```
git clone <your-repo-url>
cd agentic-content-repurposer
```

### 2. Create virtual environment

```
python3 -m venv .venv
source .venv/bin/activate

```

### 3. Install dependencies

```
pip install -r requirements.txt
```
### 4. Add your API key


```
OPENAI_API_KEY=your_real_key_here
```
---
## 📌 8. Run the System

```
python -m src.main
```


You will see:

```
=== Agentic Content Repurposer ===
Enter your content brief:
System generates:
Controller plan
Base draf
LinkedIn caption
Instagram caption + hashtags
Email blurb
Quality scores
Refinements when needed
test_results.csv updated
```
---
## 📌 9. Generate Graphs

After running several test cases:

```
python evaluation/generate_graphs.py
```
Creates:

```
evaluation/quality_scores.png
```
---
## 📌 10. Custom Quality Tool

Located in:
```
src/tools.py
```

Outputs scorecard:

```
{
  "platform": "linkedin",
  "score": 0.89,
  "dimensions": {...},
  "summary_feedback": "Strong clarity. Improve hook."
}
```

Shows exactly why content is improved after refinement.

---
## 📌 11. Self-Improvement Engine

Integrated inside main.py.

Workflow:
```
1.Evaluate initial output
2.If score < threshold
3.Re-run Platform Styling Agent with targeted refinement prompt
4.Re-score
5.Log delta
6.Replace weaker version
```
This simulates reinforcement-learning-style behavior.

---
## 🛡️ 12. Robustness & Error Handling

- All agent calls use a safe `run_agent` wrapper with retries and fallback text.
- If the strategy output cannot be parsed, the system falls back to a default strategy based on the user brief.
- If the base draft fails, the system uses the original brief as a minimal draft instead of crashing.
- The custom quality scoring tool is wrapped in `try/except`, so evaluation failures are logged but do not stop the pipeline.
- Evaluation CSV writes are idempotent, and a missing file is recreated automatically.

---
## 📌 13. Future Enhancements

- Multi-round RL refinement loop  
- TikTok / YouTube script generator  
- Accept user-uploaded reference documents  
- Add image-generation module for Instagram posts  
- Deploy as an API (FastAPI) or Streamlit web app  

---

## 📌 14. Conclusion

The **Agentic Content Repurposer** is a fully developed multi-agent AI workflow that demonstrates:

- Multi-agent orchestration  
- Memory-driven state coordination  
- Custom quality scoring tool  
- Automated refinement engine  
- Evaluation logging + performance visualization  
- Professional-grade documentation  

## 📄 15. License

This project is licensed under the **MIT License**.
