from crewai import LLM
from django.conf import settings

basic_llm = LLM(
    model=settings.OPENAI_MODEL,
    temperature=settings.OPENAI_DEFAULT_TEMPERATURE,
    api_key=settings.OPENAI_API_KEY,
)
