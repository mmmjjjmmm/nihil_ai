import json
from openai import OpenAI

from app.core.config import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


def generate_answer_suggestions(question: str, num: int = 3) -> list[str]:
    """
    Generate diverse answer suggestions using ChatGPT.

    Args:
        question: The question to generate answers for
        num: Number of suggestions to generate (default: 3)

    Returns:
        List of suggested answers
    """
    try:
        response = client.chat.completions.create(
            model=settings.chatgpt_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that generates concise, engaging social media responses. "
                        "Each answer should be under 250 characters, friendly, and informative. "
                        "Generate diverse answers with different tones or perspectives."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate {num} diverse, concise answers for this question: {question}\n\n"
                        f"Return ONLY a JSON array of strings, like this: "
                        f'["answer1", "answer2", "answer3"]'
                    )
                }
            ],
            temperature=0.8,
            max_tokens=500
        )

        # Parse the response
        content = response.choices[0].message.content.strip()

        # Try to parse as JSON
        try:
            suggestions = json.loads(content)
            if isinstance(suggestions, list) and len(suggestions) >= num:
                return suggestions[:num]
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract answers from text
            # Split by newlines and clean up
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            # Remove numbering and quotes
            cleaned = []
            for line in lines:
                # Remove leading numbers and punctuation
                cleaned_line = line.lstrip('0123456789.-) ').strip('"\'')
                if cleaned_line:
                    cleaned.append(cleaned_line)

            if len(cleaned) >= num:
                return cleaned[:num]

        # If we still don't have enough suggestions, return what we have
        # or generate a fallback
        if not suggestions or len(suggestions) < num:
            suggestions = [
                f"Great question! Let me think about that...",
                f"I'd be happy to help with this!",
                f"That's an interesting topic to explore."
            ]

        return suggestions[:num]

    except Exception as e:
        print(f"Error generating answer suggestions: {e}")
        # Return fallback suggestions
        return [
            "I'd love to help answer this!",
            "That's a great question.",
            "Let me share my thoughts on this."
        ]
