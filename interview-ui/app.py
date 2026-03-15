"""Gradio interview UI -- thin client over the FastAPI backend.

Run locally:
    uv run interview-ui/app.py

Environment variables:
    BACKEND_URL  Base URL for the FastAPI backend (default: http://localhost:8000)
    UI_HOST      Binding host (default: 0.0.0.0)
    UI_PORT      Binding port (default: 7860)
"""
from __future__ import annotations

import copy
import os

import gradio as gr

from client import APIError, client
from state import (
    EMPTY_SESSION,
    AnswerData,
    all_answers_terminal,
    get_next_unanswered_idx,
    get_non_terminal_answer_ids,
)
from theme import CUSTOM_CSS, THEME

# ---------------------------------------------------------------------------
# Helpers -- pure functions, no component references
# ---------------------------------------------------------------------------


def _fmt_type(q_type: str | None) -> str:
    if not q_type:
        return ""
    return f"*{q_type.replace('_', ' ').title()}*"


def _fmt_eval_text(ev: dict | None) -> tuple[str, str, str, str, str]:
    """Return (score_md, feedback_md, strengths_md, improvements_md, audit_md)."""
    if not ev:
        return "", "", "", "", ""
    score = ev.get("score")
    score_text = f"### Score: **{score:.1f} / 10**" if score is not None else "### Score: --"
    feedback_text = (
        f"**Feedback**\n\n{ev['feedback']}" if ev.get("feedback") else ""
    )
    strengths = ev.get("strengths") or []
    strengths_text = (
        "**Strengths**\n\n" + "\n".join(f"- {s}" for s in strengths) if strengths else ""
    )
    improvements = ev.get("improvements") or []
    improvements_text = (
        "**Areas for Improvement**\n\n" + "\n".join(f"- {i}" for i in improvements)
        if improvements
        else ""
    )
    audit_text = (
        f"Schema: `{ev.get('schema_version', '?')}` | "
        f"Rubric: `{ev.get('rubric_version', '?')}` | "
        f"Prompt: `{ev.get('prompt_version', '?')}` | "
        f"Model: `{ev.get('model_name', '?')}`"
    )
    return score_text, feedback_text, strengths_text, improvements_text, audit_text


def _fmt_summary(summary: dict) -> str:
    """Render session summary as Markdown."""
    lines = [
        "## Session Complete",
        f"**Role**: {summary.get('role', '--')}  |  "
        f"**Level**: {summary.get('difficulty', '--')}",
        "",
    ]
    for entry in summary.get("questions", []):
        q = entry.get("question", {})
        answers = entry.get("answers", [])
        lines.append(f"### Q{q.get('sequenceNumber', '?')}: {q.get('text', '')}")
        if not answers:
            lines.append("*No answer submitted.*")
        else:
            a = answers[-1]
            lines.append(f"> {a.get('answerText', '')}")
            ev = a.get("evaluation")
            if ev and ev.get("score") is not None:
                lines.append(f"\n**Score**: {ev['score']:.1f} / 10")
                if ev.get("feedback"):
                    lines.append(f"\n{ev['feedback']}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Build the Gradio app
# ---------------------------------------------------------------------------

with gr.Blocks(title="AI Interview") as demo:

    session_state = gr.State(value=copy.deepcopy(EMPTY_SESSION))

    # -- Start Panel --------------------------------------------------------
    with gr.Column(visible=True, elem_id="start-panel") as start_panel:
        gr.Markdown("## Start Your Interview")
        gr.Markdown(
            "Enter your details below and click **Start Interview** to begin "
            "an AI-powered mock interview session."
        )
        with gr.Row():
            role_tb = gr.Textbox(
                label="Job Role",
                placeholder="e.g. Backend Engineer",
                scale=3,
            )
            difficulty_dd = gr.Dropdown(
                choices=["junior", "mid", "senior"],
                value="mid",
                label="Level",
                scale=1,
            )
        qcount_sl = gr.Slider(
            minimum=1, maximum=10, step=1, value=5, label="Number of Questions"
        )
        start_btn = gr.Button("Start Interview", variant="primary")
        start_loading = gr.Markdown("Creating your session...", visible=False)
        start_error = gr.Markdown("", visible=False, elem_classes=["error-md"])

    # -- Interview Panel ----------------------------------------------------
    with gr.Column(visible=False, elem_id="interview-panel") as interview_panel:
        with gr.Column(elem_id="interview-container"):

            # Navigation row
            with gr.Row(equal_height=True):
                prev_btn = gr.Button("Prev", size="sm", interactive=False, scale=1)
                position_md = gr.Markdown(
                    "**Question 1 of 1**",
                    elem_classes=["position-label"],
                )
                next_btn = gr.Button("Next", size="sm", interactive=False, scale=1)

            # Question card
            with gr.Column(elem_classes=["question-card"]):
                type_badge_md = gr.Markdown("")
                q_text_md = gr.Markdown("")

            # Answer section
            answer_tb = gr.Textbox(
                label="Your Answer",
                placeholder="Type your answer here...",
                lines=6,
                max_lines=20,
                interactive=True,
            )
            with gr.Row():
                submit_btn = gr.Button("Submit Answer", variant="primary", scale=2)
                submit_status_md = gr.Markdown(
                    "", visible=False, elem_classes=["submit-status"]
                )
            session_error_md = gr.Markdown("", visible=False, elem_classes=["error-md"])

            # Evaluation card
            with gr.Column(elem_classes=["eval-card"], visible=False) as eval_card:
                evaluating_md = gr.Markdown(
                    "Evaluating your answer...",
                    visible=False,
                    elem_classes=["evaluating-spinner"],
                )
                with gr.Column(visible=False) as eval_result_col:
                    score_md = gr.Markdown("", elem_classes=["score-value"])
                    feedback_md = gr.Markdown("")
                    strengths_md = gr.Markdown("")
                    improvements_md = gr.Markdown("")
                    with gr.Accordion("Details", open=False):
                        audit_md = gr.Markdown("")

    # -- Summary Panel ------------------------------------------------------
    with gr.Column(visible=False, elem_id="summary-panel") as summary_panel:
        summary_md = gr.Markdown("")

    # -- Timer (always ticking; short-circuits when no active session) ------
    timer = gr.Timer(value=5)

    # -----------------------------------------------------------------------
    # Helper -- build question-view updates dict from state
    # -----------------------------------------------------------------------

    def _q_view(state: dict) -> dict:
        """Return a {component: gr.update()} dict for the question view."""
        questions = state["questions"]
        current_idx = state["current_idx"]
        answers = state["answers"]
        n = len(questions)

        if not questions:
            return {}

        q = questions[current_idx]
        q_id = q["question_id"]
        answer: AnswerData | None = answers.get(q_id)

        pos_text = f"**Question {current_idx + 1} of {n}**"
        prev_on = current_idx > 0
        next_on = current_idx < n - 1

        base: dict = {
            position_md: gr.update(value=pos_text),
            type_badge_md: gr.update(value=_fmt_type(q.get("type"))),
            q_text_md: gr.update(value=f"### {q['text']}"),
            prev_btn: gr.update(interactive=prev_on),
            next_btn: gr.update(interactive=next_on),
            session_error_md: gr.update(visible=False, value=""),
        }

        if answer is None:
            return {
                **base,
                answer_tb: gr.update(value="", interactive=True),
                submit_btn: gr.update(value="Submit Answer", interactive=True),
                submit_status_md: gr.update(visible=False, value=""),
                eval_card: gr.update(visible=False),
                evaluating_md: gr.update(visible=False),
                eval_result_col: gr.update(visible=False),
                score_md: gr.update(value=""),
                feedback_md: gr.update(value=""),
                strengths_md: gr.update(value=""),
                improvements_md: gr.update(value=""),
                audit_md: gr.update(value=""),
            }

        status = answer["status"]
        submitted_text = answer["answer_text"]

        if status in ("pending_evaluation", "in_progress"):
            return {
                **base,
                answer_tb: gr.update(value=submitted_text, interactive=False),
                submit_btn: gr.update(value="Submitted", interactive=False),
                submit_status_md: gr.update(
                    visible=True, value="Answer submitted -- evaluation in progress"
                ),
                eval_card: gr.update(visible=True),
                evaluating_md: gr.update(visible=True),
                eval_result_col: gr.update(visible=False),
                score_md: gr.update(value=""),
                feedback_md: gr.update(value=""),
                strengths_md: gr.update(value=""),
                improvements_md: gr.update(value=""),
                audit_md: gr.update(value=""),
            }

        ev = answer.get("evaluation") or {}
        if status == "completed":
            score_t, fb_t, str_t, imp_t, audit_t = _fmt_eval_text(ev)
            return {
                **base,
                answer_tb: gr.update(value=submitted_text, interactive=False),
                submit_btn: gr.update(value="Submitted", interactive=False),
                submit_status_md: gr.update(visible=True, value="Evaluation complete"),
                eval_card: gr.update(visible=True),
                evaluating_md: gr.update(visible=False),
                eval_result_col: gr.update(visible=True),
                score_md: gr.update(value=score_t),
                feedback_md: gr.update(value=fb_t),
                strengths_md: gr.update(value=str_t),
                improvements_md: gr.update(value=imp_t),
                audit_md: gr.update(value=audit_t),
            }

        # status == "failed"
        return {
            **base,
            answer_tb: gr.update(value=submitted_text, interactive=False),
            submit_btn: gr.update(value="Submitted", interactive=False),
            submit_status_md: gr.update(visible=False),
            eval_card: gr.update(visible=True),
            evaluating_md: gr.update(visible=False),
            eval_result_col: gr.update(visible=True),
            score_md: gr.update(value="### Evaluation Failed"),
            feedback_md: gr.update(
                value=f"Reason: {answer.get('failure_reason') or 'unknown error'}"
            ),
            strengths_md: gr.update(value=""),
            improvements_md: gr.update(value=""),
            audit_md: gr.update(value=""),
        }

    # -----------------------------------------------------------------------
    # Shared outputs list for question-view handlers
    # -----------------------------------------------------------------------

    QV_OUTPUTS = [
        session_state,
        position_md, type_badge_md, q_text_md,
        answer_tb, submit_btn, submit_status_md,
        eval_card, evaluating_md, eval_result_col,
        score_md, feedback_md, strengths_md, improvements_md, audit_md,
        prev_btn, next_btn, session_error_md,
    ]

    # -----------------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------------

    # -- US1: Start interview -----------------------------------------------

    async def on_start(role: str, difficulty: str, question_count: int, state: dict):
        if not role or not role.strip():
            return {
                start_error: gr.update(visible=True, value="Please enter a job role."),
            }

        try:
            result = await client.create_session(
                role.strip(), difficulty, int(question_count)
            )
        except APIError as exc:
            return {
                start_error: gr.update(visible=True, value=f"Error: {exc.message}"),
                start_loading: gr.update(visible=False),
                start_btn: gr.update(interactive=True),
            }

        new_state = copy.deepcopy(EMPTY_SESSION)
        new_state["session_id"] = result["session_id"]
        new_state["role"] = role.strip()
        new_state["difficulty"] = difficulty
        new_state["questions"] = result["questions"]
        new_state["current_idx"] = 0

        return {
            session_state: new_state,
            start_panel: gr.update(visible=False),
            interview_panel: gr.update(visible=True),
            start_error: gr.update(visible=False),
            start_loading: gr.update(visible=False),
            **_q_view(new_state),
        }

    START_OUTPUTS = [
        session_state,
        start_panel, interview_panel,
        start_error, start_loading, start_btn,
        position_md, type_badge_md, q_text_md,
        answer_tb, submit_btn, submit_status_md,
        eval_card, evaluating_md, eval_result_col,
        score_md, feedback_md, strengths_md, improvements_md, audit_md,
        prev_btn, next_btn, session_error_md,
    ]

    start_btn.click(
        fn=on_start,
        inputs=[role_tb, difficulty_dd, qcount_sl, session_state],
        outputs=START_OUTPUTS,
    )

    # -- US2: Navigate between questions ------------------------------------

    async def on_prev(state: dict):
        if not state["questions"] or state["current_idx"] <= 0:
            return {}
        new_state = copy.deepcopy(state)
        new_state["current_idx"] -= 1
        return {session_state: new_state, **_q_view(new_state)}

    async def on_next(state: dict):
        questions = state["questions"]
        if not questions or state["current_idx"] >= len(questions) - 1:
            return {}
        new_state = copy.deepcopy(state)
        new_state["current_idx"] += 1
        return {session_state: new_state, **_q_view(new_state)}

    prev_btn.click(fn=on_prev, inputs=[session_state], outputs=QV_OUTPUTS)
    next_btn.click(fn=on_next, inputs=[session_state], outputs=QV_OUTPUTS)

    # -- US2: Submit answer -------------------------------------------------

    async def on_submit(answer_text: str, state: dict):
        if not state.get("session_id"):
            return {}
        if not answer_text or not answer_text.strip():
            return {
                session_error_md: gr.update(
                    visible=True, value="Please type an answer before submitting."
                )
            }

        questions = state["questions"]
        current_idx = state["current_idx"]
        q = questions[current_idx]
        q_id = q["question_id"]

        if q_id in state["answers"]:
            return {}

        try:
            accepted = await client.submit_answer(
                session_id=state["session_id"],
                question_id=q_id,
                answer_text=answer_text.strip(),
            )
        except APIError as exc:
            return {
                session_error_md: gr.update(visible=True, value=f"Error: {exc.message}"),
            }

        new_state = copy.deepcopy(state)
        new_state["answers"][q_id] = {
            "answer_id": accepted["answer_id"],
            "question_id": q_id,
            "answer_text": answer_text.strip(),
            "status": "pending_evaluation",
            "evaluation": None,
            "failure_reason": None,
        }

        # Non-blocking advance: move to next unanswered question when possible
        if len(questions) > 1:
            next_idx = get_next_unanswered_idx(new_state)
            if next_idx is not None:
                new_state["current_idx"] = next_idx

        return {session_state: new_state, **_q_view(new_state)}

    submit_btn.click(fn=on_submit, inputs=[answer_tb, session_state], outputs=QV_OUTPUTS)

    # -- US2: Poll tick (gr.Timer every 5 s) --------------------------------

    POLL_OUTPUTS = [
        *QV_OUTPUTS,
        interview_panel, summary_panel, summary_md,
    ]

    async def on_poll_tick(state: dict):
        if not state.get("session_id"):
            return {}

        non_terminal_ids = get_non_terminal_answer_ids(state)
        if not non_terminal_ids:
            return {}

        new_state = copy.deepcopy(state)
        session_id = state["session_id"]

        for answer_id in non_terminal_ids:
            try:
                result = await client.get_answer_result(
                    session_id=session_id, answer_id=answer_id
                )
            except APIError:
                continue  # transient error -- retry on next tick

            q_id = result["question_id"]
            if q_id not in new_state["answers"]:
                continue

            new_state["answers"][q_id]["status"] = result["status"]
            if result["evaluation"]:
                new_state["answers"][q_id]["evaluation"] = result["evaluation"]
            if result["failure_reason"]:
                new_state["answers"][q_id]["failure_reason"] = result["failure_reason"]

        updates: dict = {session_state: new_state, **_q_view(new_state)}

        # Show summary when all answers have reached a terminal state
        if all_answers_terminal(new_state):
            try:
                summary_data = await client.get_session_summary(session_id)
                updates[summary_panel] = gr.update(visible=True)
                updates[summary_md] = gr.update(value=_fmt_summary(summary_data))
                updates[interview_panel] = gr.update(visible=False)
            except APIError:
                pass  # leave interview panel visible if summary fetch fails

        return updates

    timer.tick(fn=on_poll_tick, inputs=[session_state], outputs=POLL_OUTPUTS)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo.launch(
        server_name=os.getenv("UI_HOST", "0.0.0.0"),
        server_port=int(os.getenv("UI_PORT", "7860")),
        theme=THEME,
        css=CUSTOM_CSS,
    )
