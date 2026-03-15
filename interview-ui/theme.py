"""Gradio theme and custom CSS constants for the interview UI."""
from __future__ import annotations

import gradio as gr

THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.slate,
)

CUSTOM_CSS = """
/* ── Layout ──────────────────────────────────────────────────────────── */
#interview-container {
    max-width: 840px;
    margin: 0 auto;
    padding: 0 16px;
}

/* ── Cards ───────────────────────────────────────────────────────────── */
.question-card, .eval-card {
    background: var(--block-background-fill);
    border: 1px solid var(--border-color-primary);
    border-radius: var(--radius-lg);
    padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    margin-bottom: 12px;
}

/* ── Score ───────────────────────────────────────────────────────────── */
.score-value p {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.5px;
}

/* ── Evaluating spinner ──────────────────────────────────────────────── */
.evaluating-spinner p {
    color: var(--body-text-color-subdued);
    font-style: italic;
    font-size: 0.9rem;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.5; }
}

/* ── Error text ──────────────────────────────────────────────────────── */
.error-md p {
    color: var(--error-text-color, #dc2626);
}

/* ── Nav row ─────────────────────────────────────────────────────────── */
.position-label {
    display: flex;
    align-items: center;
    justify-content: center;
}

/* ── Mobile ──────────────────────────────────────────────────────────── */
@media (max-width: 640px) {
    #interview-container {
        padding: 0 8px;
    }
    .question-card, .eval-card {
        padding: 14px 16px;
    }
}
"""
