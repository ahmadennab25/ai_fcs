# Brand Voice & Image Prompt Guidelines

These notes describe the writing/visual guidelines the two agents are
expected to follow. They are not loaded programmatically — they document
the conventions baked into `core/crews/*/config/agents.yaml` and
`tasks.yaml`, and are the reference for anyone adjusting those prompts.

## Post Writer Agent (Agent 1)
- Write in the brand's `voice_guidelines`, never invent unsupported claims.
- Caption must fit the campaign `tone` and speak to the `target_audience`.
- Always include a clear call to action.
- Always produce exactly one `image_prompt` describing a single scene
  (subject, setting, style, mood, colours) — this is handed to Agent 2.

## Image Generation Agent (Agent 2)
- Refine Agent 1's `image_prompt` for a Facebook feed: one clear focal
  point, brand-safe style, an aspect ratio that reads well in-feed.
- Must call the image generation tool to actually produce the asset —
  never return a result without calling it.
