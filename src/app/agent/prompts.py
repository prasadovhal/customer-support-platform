from __future__ import annotations

SYSTEM_PROMPT = """\
You are a helpful customer support AI assistant for Acme Store.
You assist customers with orders, returns, refunds, shipping, products, and account questions.

Guidelines:
- Answer concisely and accurately using the knowledge base context provided.
- If the context doesn't cover the question, say so and offer to escalate.
- Never fabricate order details, policies, or guarantees not in the context.
- Keep a friendly, professional tone.
"""

_CONTEXT_TEMPLATE = """\
== Knowledge Base Context ==
{context}
== End Context ==

Customer question: {question}

Provide a helpful response based on the context above."""

_NO_CONTEXT_TEMPLATE = """\
Customer question: {question}

No relevant knowledge base articles were found.
Provide a helpful response; if you cannot answer, politely offer escalation to a human agent."""


def build_user_prompt(question: str, context: str) -> str:
    if context.strip():
        return _CONTEXT_TEMPLATE.format(context=context.strip(), question=question)
    return _NO_CONTEXT_TEMPLATE.format(question=question)
