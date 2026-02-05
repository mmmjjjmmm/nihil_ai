from openai import OpenAI

from app.core.config import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


def get_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for the given text using OpenAI's embedding model.

    Args:
        text: Text to generate embedding for

    Returns:
        List of floats representing the embedding vector
    """
    response = client.embeddings.create(
        input=text,
        model=settings.embedding_model
    )
    return response.data[0].embedding
