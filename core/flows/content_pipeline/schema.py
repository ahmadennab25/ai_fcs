from typing import Dict, List, Optional

from pydantic import BaseModel


class ContentPipelineState(BaseModel):
    """Shared state passed between steps of the content pipeline flow."""

    # Identifier — set when the flow loads its inputs from the database.
    campaign_id: Optional[int] = None

    # Inputs (supplied directly in "raw" mode, or loaded from the DB).
    topic: str = ""
    campaign_objective: str = ""
    target_audience: str = ""
    tone: str = ""
    brand_voice: str = ""
    keywords: List[str] = []

    # Outputs
    post_output: Dict = {}
    image_output: Optional[Dict] = None
    final_output: Dict = {}
