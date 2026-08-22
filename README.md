# AI Facebook Content Studio (AI-FCS)

A Django + Django REST Framework project that lets a social-media team
manage brands and campaigns, and produces Facebook content using two AI
agents built with [CrewAI](https://docs.crewai.com/) (backed by OpenAI):

- **Agent 1 — Post Writer Crew**: takes a campaign + topic and writes a
  ready-to-publish Facebook post (caption, hashtags, call to action) plus a
  vivid image prompt for Agent 2. Stored as a `FacebookPost`.
- **Agent 2 — Image Generation Crew**: takes a post id, reads that post's
  `image_prompt`, generates an image with the OpenAI Images API, and stores
  it as a `PostImage` linked to the post.

## Design note

The project mirrors the reference **AI-HRMS** architecture: a `config`
Django project + a single `core` app, one model per file, "thin views / fat
services", one folder per CrewAI crew (`@CrewBase` + `agents.yaml` +
`tasks.yaml`), a `crewai.flow.Flow` that chains the two agents, and a shared
`core/tools/main_llm.py` LLM instance. Only the domain changed — HR
screening/interview → brand/campaign/post/image.

Error handling is intentionally strict: every expected failure (missing
input, missing API key, agent returned bad JSON, generated file missing on
disk, etc.) raises a `ValueError` that a view turns into a clean `400`.
Every *unexpected* failure is caught, logged with `logger.error(...)`, and
turned into a `500` with a generic message — nothing is ever printed with
`print()`, and no request ever crashes the server or leaks a traceback.

## Architecture

```
ai_fcs/
├── manage.py
├── run_pipeline.py              # Demo: run both agents end-to-end, no DB
├── requirements.txt
├── example.env
├── README.md
├── config/                      # Django project (settings, urls, wsgi, asgi)
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── core/                        # Main app
    ├── models/                  # One file per model
    │   ├── brand.py
    │   ├── campaign.py
    │   ├── facebook_post.py
    │   └── post_image.py
    ├── serializers/              # DRF serializers
    ├── views/                    # Class-based APIViews (CRUD + AI actions)
    ├── services/                 # Business logic (post, image, pipeline)
    ├── crews/                    # The two AI agents (CrewAI)
    │   ├── post_writer_crew/            (Agent 1)
    │   │   ├── crew.py
    │   │   └── config/{agents.yaml,tasks.yaml}
    │   └── image_generation_crew/       (Agent 2)
    │       ├── crew.py
    │       └── config/{agents.yaml,tasks.yaml}
    ├── flows/content_pipeline/   # CrewAI Flow chaining Agent 1 -> Agent 2
    │   ├── flow.py
    │   └── schema.py
    ├── tools/                    # Shared LLM instance + image tool
    │   ├── main_llm.py
    │   └── image_tool.py
    ├── prompts/                  # Prompt/style guideline notes
    ├── migrations/
    ├── admin.py
    ├── apps.py
    └── urls.py
```

## Data model

| Model | Parallels | Purpose |
| --- | --- | --- |
| `Brand` | `Department` | The brand/company content is produced for |
| `Campaign` | `JobPosition` | The context an agent writes a post for |
| `FacebookPost` | `ScreeningResult` | Agent 1's output |
| `PostImage` | `InterviewQuestionSet` | Agent 2's output |

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp example.env .env
# then edit .env: DB credentials + OPENAI_API_KEY at minimum

# 4. Create the PostgreSQL database (must already exist)
createdb ai_fcs                     # or via psql: CREATE DATABASE ai_fcs;

# 5. Apply migrations
python manage.py makemigrations core
python manage.py migrate

# 6. Create an admin user
python manage.py createsuperuser

# 7. Run the server
python manage.py runserver
```

The admin site is at `http://127.0.0.1:8000/admin/`.

## Endpoints (custom `APIView`s only — no ViewSets/routers/generics)

| Ticket | Action | Method | URL |
| --- | --- | --- | --- |
| FCS-103 | Create Brand | POST | `/api/brands/` |
| FCS-104 | Create Campaign | POST | `/api/campaigns/` |
| FCS-111 | **Write Post (Agent 1)** | POST | `/api/posts/write/` |
| FCS-112 | **Generate Image (Agent 2)** | POST | `/api/posts/<int:pk>/image/` |
| FCS-105 | View Post | GET | `/api/posts/<int:pk>/` |
| FCS-106 | View Post Image | GET | `/api/post-images/<int:pk>/` |
| FCS-115 *(optional)* | Run full pipeline | POST | `/api/pipeline/run/` |

Errors are consistent everywhere: `404` with `{"detail": "..."}` for missing
records, `400` with `{"detail": "..."}` for validation errors or a
`ValueError` (bad input, missing `OPENAI_API_KEY`, agent/tooling failure),
and `500` with a generic message (logged server-side) for anything
unexpected.

## Try it — full flow with curl

```bash
BASE=http://127.0.0.1:8000/api

# 1. Create a brand
curl -X POST $BASE/brands/ -H "Content-Type: application/json" -d '{
  "name": "Acme Coffee",
  "description": "A neighbourhood coffee brand.",
  "voice_guidelines": "Warm, upbeat, a little cheeky. Short sentences. Emoji used sparingly."
}'
# -> {"id": 1, ...}

# 2. Create a campaign for that brand
curl -X POST $BASE/campaigns/ -H "Content-Type: application/json" -d '{
  "brand": 1,
  "title": "Fall Pumpkin Spice Launch",
  "objective": "Drive awareness and in-store trial of the new seasonal drink.",
  "target_audience": "Coffee lovers aged 18-30 who follow us on Facebook",
  "tone": "playful",
  "keywords": ["#PumpkinSpice", "#ColdBrew"]
}'
# -> {"id": 1, ...}

# 3. Write a post (Agent 1)
curl -X POST $BASE/posts/write/ -H "Content-Type: application/json" -d '{
  "campaign_id": 1,
  "topic": "Launching our new pumpkin spice cold brew for fall"
}'
# -> {"id": 1, "caption": "...", "hashtags": [...], "image_prompt": "...", ...}

# 4. Generate an image for that post (Agent 2)
curl -X POST $BASE/posts/1/image/
# -> {"id": 1, "post": 1, "prompt_used": "...", "image_file": "/media/post_images/....png", ...}

# 5. Fetch the results
curl $BASE/posts/1/
curl $BASE/post-images/1/

# Optional: run both agents in a single call instead of steps 3+4
curl -X POST $BASE/pipeline/run/ -H "Content-Type: application/json" -d '{
  "campaign_id": 1,
  "topic": "Launching our new pumpkin spice cold brew for fall"
}'
```

## Try the agents without a database

`run_pipeline.py` runs both agents end-to-end on a hard-coded sample
campaign, with **no database access at all**, and logs the results (caption,
hashtags, call to action, image prompt, and the generated image's relative
path). Only `OPENAI_API_KEY` (and network access) is required — no
PostgreSQL setup needed.

```bash
python run_pipeline.py
```

If `OPENAI_API_KEY` is missing or the request fails, the script logs a
clean error via `logger.error(...)` and exits — it never crashes with a raw
traceback and never uses `print()`.

## Notes

- Media files (`ImageField`, generated post images) are served from
  `/media/` in `DEBUG` mode via `config/urls.py`, the same way static files
  are.
- All business logic lives in `core/services/`; views only validate input,
  call a service, and shape the response — no business logic in views.
- All ORM access inside `ContentPipelineFlow` happens in the synchronous
  `kickoff()` wrapper, never inside the async `@start`/`@listen` crew steps.
