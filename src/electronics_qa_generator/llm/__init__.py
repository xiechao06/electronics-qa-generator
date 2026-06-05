"""Optional LLM layer: paraphrase, explanation, distractor polish, tags.

The LLM never creates truth. It only rewords questions, writes explanations,
improves distractor wording, and assigns topic/difficulty tags *after* the
deterministic answer is fixed.
"""
