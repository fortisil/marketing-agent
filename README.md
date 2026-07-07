# fortisil/ai-cmo v1.0

AI Executive Operating System foundation for ChatBot2U. The AI CMO is the first executive.

This version generates a structured daily executive report, renders an English CEO brief from it, sends it through Resend, and stores memory for learning. The north-star KPI is paying customers; booked demos remain an important conversion signal.

The master operating contract is [`AUTONOMOUS_EXECUTIVE_OS_SPECIFICATION_v1.0.md`](/Users/rami/Documents/Codex/2026-07-03/chrome-plugin-chrome-openai-bundled-file-2/AUTONOMOUS_EXECUTIVE_OS_SPECIFICATION_v1.0.md). The permanent definition of done remains [`AUTONOMOUS_CMO_ACCEPTANCE.md`](/Users/rami/Documents/Codex/2026-07-03/chrome-plugin-chrome-openai-bundled-file-2/AUTONOMOUS_CMO_ACCEPTANCE.md). The architecture is frozen; future sprints should close the gap between autonomous marketing execution and autonomous business growth.

## What It Does

- Loads company rules from `config/companies/chatbot2u.yaml`
- Loads company knowledge from `knowledge/chatbot2u.md`
- Supports English CEO briefs by default, with Hebrew style rules available for Hebrew-specific variants
- Loads objectives from `config/objectives/chatbot2u.yaml`
- Loads business assets from `config/companies/chatbot2u.yaml`, including website repo, Instagram, Meta ad account, and WhatsApp
- Loads secrets and runtime settings from `.env`
- Collects metrics through a `MetricsProvider` contract
- Collects real Meta Ads and Instagram metrics when credentials are configured
- Collects WhatsApp bot funnel metrics from a webhook/event log file when configured
- Uses a state-aware `DecisionEngine` to separate business reasoning from data collection
- Generates actionable tasks with priority, due date, estimated impact, confidence, and dependencies
- Generates an English CEO brief with the OpenAI API
- Stores daily structured reports, briefs, decisions, and run history under `memory/`
- Exposes saved Markdown and JSON artifacts for external delivery
- Runs daily at 08:00 Asia/Jerusalem with APScheduler
- Supports preview, generate, and send-now CLI commands

For production, mock marketing performance inputs are forbidden unless explicitly enabled. The system must report unavailable data instead of inventing numbers.

## Architecture

The daily run is:

```text
Company Knowledge + Objectives + MetricsProvider(s)
    -> DecisionEngine
    -> ChiefOfStaff
    -> MarketingDepartment agents
    -> Structured DailyReport
    -> English CEO brief
    -> OutputChannel
    -> File artifacts for external delivery
```

The core reasoning loop asks:

1. What happened yesterday?
2. Why?
3. What should we change?
4. What is today's highest ROI activity?
5. What prediction am I making, and when will I evaluate it?

Future providers should implement the same provider contract as `src/providers/mock.py`.

## Website Repo Awareness

ChatBot2U website/product repo awareness is provided by `src/providers/website_repo.py`.

Set this when the website repo exists locally:

```bash
CHATBOT2U_REPO_PATH=/path/to/ChatBot2U
```

For v0.3, the provider does not call the GitHub API. It reads local files only and analyzes:

- package and app structure
- landing pages
- README content
- recent git commits when the local path is a git repo
- page and component text where practical
- product claims, detected features, CTAs, WhatsApp links, weak CTAs, opportunities, content ideas, and website risks

If `CHATBOT2U_REPO_PATH` is unset or invalid, the provider emits mock website intelligence so the rest of the CMO loop keeps working.

## Meta Data Strategy

Meta/Instagram metrics are routed through `src/providers/marketing_platform.py`.

Preferred strategy:

- `meta_mcp`: use ChatGPT/orchestrator Meta MCP tools as the execution layer.
- The local Python run emits required MCP actions into the daily report.
- A ChatGPT automation or orchestrator can execute those MCP calls and feed the resulting metrics back into the CMO loop in a later phase.

Optional fallback:

- `meta_graph`: use direct Meta Graph API calls from Python when `META_ACCESS_TOKEN` is configured.
- This is an optional fallback, not the preferred long-term provider model.

Local Python cannot directly invoke ChatGPT MCP tools unless we add an MCP client/runtime later.

Configure provider selection in `config/companies/chatbot2u.yaml`:

```yaml
marketing_platform:
  provider: meta_mcp
  fallback_provider: meta_graph
  meta_ad_account_id: "1011149454836521"
  instagram_username: chatbot2u
```

Configure optional Graph API fallback credentials in `.env`:

```bash
META_ACCESS_TOKEN=
META_AD_ACCOUNT_ID=1011149454836521
META_IG_ACCOUNT_ID=
META_API_VERSION=v23.0
```

When credentials and permissions are available, the provider collects:

- ad account basic info
- campaigns, ad sets, and ads summary
- spend today and last 7 days
- impressions, reach, clicks, CTR, and cost per result where available
- active and paused campaigns
- delivery errors where available
- recent Instagram media, captions, permalinks, media type, comments, likes, and insights where permissions allow

If MCP execution is required, the local run returns structured required actions instead of calling Meta directly. If Graph API fallback credentials are missing or permissions fail, the provider returns a structured fallback status. The daily brief continues to run.

Budget rules remain enforced in the decision engine:

- no paid spend on Saturday
- no new or increased paid spend after 13:00 Israel time on Friday
- default budget cap is ₪20/day
- if no real campaign exists, prepare the first campaign inside delegated budget limits

## WhatsApp Bot Funnel Metrics

WhatsApp bot funnel metrics are provided by `src/providers/whatsapp_bot.py`.

Configure:

```bash
FUNNEL_CONFIG_PATH=config/funnels/chatbot2u.yaml
WHATSAPP_PROVIDER=mock
WHATSAPP_EVENTS_PATH=/path/to/whatsapp_events.jsonl
WHATSAPP_WEBHOOK_URL=https://example.com/bot/events
```

For Phase 0.7, the provider supports three modes:

- `mock`: default local funnel data for development
- `json_events`: reads JSONL or a JSON array from `WHATSAPP_EVENTS_PATH`
- `webhook`: fetches JSONL or a JSON array from `WHATSAPP_WEBHOOK_URL`

Event schema:

```json
{
  "timestamp": "2026-07-03T08:10:00+03:00",
  "conversation_id": "conv_123",
  "phone_hash": "hashed_phone",
  "event": "conversation_started",
  "metadata": {
    "response_time_seconds": 4
  }
}
```

Supported `event` values:

- `conversation_started`
- `qualified_lead`
- `demo_requested`
- `demo_booked`
- `proposal_sent`
- `customer`
- `human_handoff`

The provider calculates:

- conversations today and last 7 days
- qualified leads
- demo requests
- demo bookings
- customers
- average response time when available
- conversion rates from conversation to qualified lead, qualified lead to demo, demo to customer, and conversation to customer
- Funnel Health Score from 0 to 100

The decision engine prioritizes WhatsApp bottlenecks:

- many conversations but few qualified leads: improve opening questions
- many qualified leads but few booked demos: improve scheduling flow
- many demos but few customers: review demo quality and follow-up
- few conversations: improve Instagram, ads, and website CTA into WhatsApp

If `WHATSAPP_PROVIDER=json_events` or `WHATSAPP_PROVIDER=webhook` is missing its required source, the provider returns a structured unavailable status and the daily brief continues to run. In `mock` mode, the AI CMO always has a safe development fallback.

The operating loop is:

```text
Observe -> Analyze -> Decide -> Execute -> Measure -> Learn
```

Every feature should answer one question: did it help ChatBot2U book more demos?

The AI CMO should never wait for work. When no obvious task exists, it should proactively review the website, repository, marketing, competitors, SEO opportunities, sales funnel, WhatsApp conversations, hypotheses, and experiments. The intended behavior is an autonomous executive constantly looking for the next revenue opportunity, not an automation waiting for instructions.

The AI CMO operates under delegated authority, not continuous approval. It executes within configured limits, remains accountable for outcomes, documents every significant decision, and escalates only when a decision exceeds its delegated limits.

The operating model is:

```text
ExecutiveBrain -> ChiefOfStaff -> Task Queue -> Workers -> Execution Connectors
```

The ExecutiveBrain defines initiatives. The Chief of Staff decomposes initiatives into work. Persistent workers own tasks until completion. Execution connectors receive only execution tasks, never business decisions. Every autonomous action records what it did, why it did it, which policy authorized it, the expected outcome, and the actual outcome.

## Department Roadmap

The Executive Layer is frozen except for bug fixes. New capabilities should be implemented as autonomous execution departments, not as more executive-brain logic.

Every execution connector must have:

- One responsibility
- Task input
- Success/failure result
- Execution log
- Artifact IDs
- Proof fields
- Retry support
- Delegated-authority checks
- Dry-run support

## Workforce Runtime

The AI Executive OS is modeled as an organization, not a collection of transient agents.

Runtime package:

```text
src/workforce/
  worker.py
  workforce.py
  queue.py
  task.py
  scheduler.py
```

Every worker has:

- `worker_id`
- `department`
- `capabilities`
- `current_task`
- `status`
- `last_execution`
- `retry_count`
- `execution_history`
- `kpis`

Worker states:

- `IDLE`
- `WORKING`
- `WAITING_FOR_CONNECTOR`
- `BLOCKED`
- `FAILED`
- `COMPLETED`

Task lifecycle:

```text
Created -> Assigned -> Executing -> Completed -> Verified -> Archived
```

The persistent queue is stored under:

```text
memory/workforce/tasks.json
memory/workforce/workers.json
```

It survives restarts, supports retries, priorities, deadlines, dependencies, and blocked-task ownership. Workers do not disappear after a task. If Buffer or Image generation is unavailable, the assigned worker keeps ownership and retries on the next execution window.

Marketing Operations is the first department and includes:

- Content Agent
- Design Agent
- Video Agent
- Social Agent
- Ads Agent
- Analytics Agent
- Website Agent
- Outreach Agent

## Brand Brain Rules

ChatBot2U separates internal reporting language from market-facing language:

- CEO brief language: English.
- Internal operating language: English.
- Marketing language: Hebrew.
- Default social post language: Hebrew.
- Target country: Israel.
- Target audience: Israeli law firms.

These rules live in:

```text
config/companies/chatbot2u.yaml
knowledge/companies/chatbot2u/brand/brand.yaml
```

Every published social post must include a WhatsApp action path unless a future Content Analyst records a specific exception. The default CTA is:

```text
רוצים לראות איך זה עובד? שלחו הודעה ל-WhatsApp: https://wa.me/972559720244
```

Image generation is also configuration-driven. The current Brand Brain image config is:

```yaml
image_generation:
  provider: openai
  model: gpt-image-1
  style: chatbot2u
  text_policy: no_model_rendered_text
  language_policy: Hebrew captions only; no generated Hebrew text inside images
video_generation:
  provider: heygen
  format: Instagram Reels
  aspect_ratio: "9:16"
  resolution: "1080x1920"
  subtitles: false
```

The runtime still reads the active image model from `OPENAI_IMAGE_MODEL`, so model upgrades should be configuration changes, not executor code changes.

Still images must be generated by OpenAI image generation, not HeyGen. Hebrew is mandatory for market-facing copy, but generated image pixels must not contain model-rendered Hebrew letters, words, CTAs, subtitles, or numbers because image models can misspell text. Hebrew CTA copy belongs in the Buffer caption, or in a future deterministic approved overlay system. Videos are rendered by HeyGen only, without subtitles, in Instagram Reels 9:16 format.

The daily CEO brief is an Executive Decision Brief, not an activity log. It should answer one question:

```text
Are we closer to another paying customer than we were yesterday?
```

The first line must be one of:

```text
Yesterday the business became healthier because ...
Yesterday the business did not improve because ...
```

If measurable customer-acquisition improvement cannot be proven, the brief must say that directly and make the highest priority discovering why.

The AI CMO must never leave the CEO with a bare `Unavailable` row. Missing data must be converted into executive measurement:

- Why the signal is missing.
- Business impact of the missing signal.
- Automatic action the AI is taking.
- Expected review or completion time.
- Confidence level.

The system uses three evidence levels:

1. Verified internal data: WhatsApp, Meta, CRM, website analytics, and revenue systems.
2. Public platform signals: published post proof, engagement, competitor activity, search trends.
3. Clearly labeled hypotheses: low-confidence decisions used to keep operating while measurement improves.

If internal data is missing, the AI CMO must keep operating with the best available evidence, label confidence, and improve instrumentation. It must not become a passive reporter whose main message is `Unavailable`.

The Executive OS is now evaluated by one management question:

```text
Did it manage the business today?
```

It is not evaluated by reports, completed tasks, generated content, or activity volume.

Every department manager permanently owns business assets:

- Social Manager owns Instagram and Facebook.
- Ads Manager owns Meta Ads, Budget, and Campaigns.
- Analytics Manager owns GA4, website analytics, attribution, and business KPIs.
- Website Manager owns homepage, landing pages, SEO, CTA, and conversion.
- Creative Director owns creative quality, images, videos, copy, and brand consistency.
- Growth Manager owns funnel, Business Value Score, experiment backlog, and opportunity ranking.

These managers never finish. They continuously manage assets, create work when no work exists, remove blockers when blocked, and escalate only when impossible to resolve inside delegated authority.

The runtime persists management state under:

```text
memory/executive_os/
```

That directory contains the internal budget ledger, campaign registry, content registry, competitor registry, WhatsApp intelligence, website management, executive memory, and latest operating-executive state.

The first operating KPI is:

```text
Autonomous Work Completion Rate =
completed connector-facing work / completed + blocked + failed connector-facing work
```

The brief should show:

- Tasks planned
- Completed automatically
- Blocked
- Failed
- Success rate

The target is 95%. Internal memory tasks and prepared payloads do not count as completed autonomous work unless a connector returns verified execution proof.

The second operating KPI is:

```text
Revenue Influence Score
```

It traces completed AI actions to qualified leads, booked demos, and paying customers. If WhatsApp/customer attribution is not connected, the score is unavailable rather than guessed.

The third operating KPI is:

```text
Business Autonomy Index
```

It reports Planning, Execution, Learning, Revenue Influence, and Overall autonomy. When Execution reaches 90%+, the system is crossing from smart software into autonomous operator.

The 14-day acceptance criterion is: the AI Executive OS should come back with more content published, more experiments run, a better website, a complete audit trail, and more paying customers than when it started.

Department actions are written to:

```text
memory/actions/YYYY-MM-DD.json
```

Connector execution results are written to:

```text
memory/executions/YYYY-MM-DD.json
```

Each action includes timestamp, initiative, department, agent, action, expected business impact, delegated authority used, status, result, next step, retry, and error. Each connector execution includes task id, connector, status, worker ID, artifact IDs, proof, error, and next retry.

Publishing and campaign execution are never implied. If there is no evidence, the action did not happen. If the AI says it published an Instagram post or Reel, the log must include Buffer update ID, Instagram URL, timestamp, caption hash, image hash, and worker ID. If it says it generated an image, the log must include image path, SHA256 hash, brand validation result, timestamp, and worker ID. If it says it started a campaign, the log must include campaign ID, budget, status, and verified Meta proof.

Connector completion rule:

```text
business artifact + evidence + execution log = completed
anything less = blocked or failed
```

CEO briefs must never talk about infrastructure existence. They should say only:

- Completed
- Blocked
- Failed
- Next automatic retry

## v1.0 Foundation

This repository is now the foundation of an AI Executive Operating System. ChatBot2U's AI CMO is the first executive implementation.

Core executive layers:

- CEO Constitution: `knowledge/ceo_constitution.md`
- Autonomous CMO Acceptance Specification: `AUTONOMOUS_CMO_ACCEPTANCE.md`
- Executive Brain: prioritizes mission, OKRs, initiatives, and tradeoffs
- Board of Advisors: Growth, Product, Finance, and Customer Success perspectives
- Chief of Staff: selects what runs today, what waits, and what exceeds delegated authority
- Brand Brain: loads company-specific brand rules before repository fallback
- Design System Agent: rejects or requests regeneration for off-brand creative
- Executive Journal: evening reflection and learning loop

Brand Brain company structure:

```text
knowledge/companies/chatbot2u/brand/
  brand.yaml
  colors.yaml
  design_rules.md
  logo/

assets/companies/chatbot2u/
  logos/
  screenshots/
  hero-images/
  product-images/
  heygen/
  videos/
  icons/
  templates/
  social/
```

Write the evening journal after a daily report exists:

```bash
python -m src.main --write-evening-journal
```

## Brief Language Quality

The CEO brief defaults to English via `BRIEF_LANGUAGE=en` and `company.brief_language: en`.

Hebrew generation remains available for Israeli-audience variants. When Hebrew is selected, the generator uses `knowledge/hebrew_style_guide.md` to keep the copy in professional Israeli business Hebrew. It explicitly avoids bad phrasing such as `נגנבו לידים`, preserves `WhatsApp` spelling, and prefers terms such as `פניות חדשות`, `לידים כשירים`, `פגישות הדגמה שנקבעו`, `המלצה לפעולה`, and `משימה מרכזית להיום`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Python 3.11+ is required. Python 3.12 is preferred.

Fill in `.env` with your local values. Do not commit `.env`.

## Production Data Rules

Production runs default to:

```bash
APP_ENV=production
ALLOW_MOCK_DATA=false
BRIEF_LANGUAGE=en
```

Rules:

- Never trust mock data in production.
- Mock data is only for local development and must be explicitly enabled with `ALLOW_MOCK_DATA=true`.
- If WhatsApp events are not connected, the report must say `No verified WhatsApp event data available.` and must not show fake conversation, lead, or demo counts.
- If Meta MCP cannot be invoked by the runner and Graph credentials are not configured, the report must say `No verified Meta campaign data available.`
- Campaign execution requires a real Meta execution provider. A campaign is not active unless verified by Meta data.
- WhatsApp lead tracking requires bot event integration through `WHATSAPP_EVENTS_PATH` or `WHATSAPP_WEBHOOK_URL`.
- Every KPI used for decisions should carry source attribution such as `source: unavailable|mock|json_events|webhook|meta_graph` and `verified: true|false`.
- The CEO brief must separate completed execution, blocked execution, failed execution, and next automatic retry.
- If there is no verified data, the brief must say `No verified data available yet`.

## Operator Execution Queue

The AI Executive OS should operate the business, not only report on it.

Every daily report includes an internal `execution_queue` with:

- `initiative`: the business initiative for the day.
- `today_mission`: the concrete outcome the AI CMO is trying to create.
- `currently_working_on`: internal tasks selected by delegated authority.
- `internal_tasks`: AI-owned work such as Meta sync, WhatsApp tracking, CTA review, content preparation, competitor/ICP research, and repository review.
- `pending_escalations`: decisions that exceed delegated authority.

Internal tasks are not user tasks. They should not clutter the CEO brief.

The CEO brief should be readable in under 90 seconds and include only executive-decision content:

- Executive Decision: one short paragraph explaining whether business performance improved, why, what decision comes next, when the AI will decide, and the biggest blocker.
- Executive Scoreboard: business health, marketing health, revenue momentum, pipeline, booked demos, new customers, revenue, ROI, confidence, and business autonomy.
- Manager Performance: each persistent manager reports status, objective, KPI, trend, risk, decision, and next review.
- Executive Summary: maximum five bullets focused on business outcome.
- Yesterday: completed work only when evidence exists.
- Results: Instagram, WhatsApp, website, demos, customers, revenue, and comparisons only when verified.
- Business Funnel: Reach -> Clicks -> WhatsApp -> Qualified -> Demo -> Customer, with bottleneck.
- Content, Campaign, Website, Competitor, and WhatsApp Intelligence.
- Decision Ledger: important decisions, reasons, expected outcome, and success metric.
- Currently Working: real work in progress only, with no fake progress language.
- Self Evaluation and Business Memory: verified learning only.
- Budget, Opportunity Ranking, Risks, Executive Calendar, Proof, and one CEO focus sentence.

If `executed_actions_today` is `none`, the CEO brief should say that no external execution completed and report only blocked/failed execution that matters. The brief must never start with `I published`, `I prepared`, or infrastructure status. It must never use `ready`, `prepared`, or `queued` as CEO-facing accomplishment language.

The Executive OS is not evaluated by activities. It is evaluated by measurable business improvement. Every morning the AI must prove that the probability of acquiring another paying customer increased. If it cannot prove that, its highest priority is discovering why.

Budget is owned internally. The internal budget ledger is authoritative; Meta only reconciles it. The brief must never say the budget is unavailable. It should report monthly budget, reserved, committed, spent, forecast, remaining, and per-campaign/experiment/asset allocations from the internal ledger.

Campaigns and content are persistent registries, not one-off outputs. Every campaign has owner, objective, status, budget, start, end, spend, expected ROI, actual ROI, evidence, and recommendation. Every content asset has owner, lifecycle, published/measured/ranked/promoted/retired state, learning, and Business Value Score.

Every brief must also answer:

- What improved?
- Why?
- What got worse?
- What are we changing?
- What do we expect tomorrow?
- How will we know if we were right?

## Marketing Department Executors

Marketing Operations can create internal task payloads without external credentials, but the CEO brief must not report them as accomplishments. Accomplishments require execution proof from a connector.

Sprint 1 execution connector:

- `BufferExecutor`: accepts a social publishing task, calls Buffer's current GraphQL API, requires a Buffer post/update ID, requires public media URL proof for Instagram, records the returned Buffer/social URL, and logs completion/failure.
- `ImageExecutor`: accepts a branded image task, validates Brand Brain inputs, generates a PNG with OpenAI image generation when enabled, rejects prompts that ask the image model to render Hebrew text or CTA copy, stores the asset under `assets/companies/chatbot2u/social/YYYY-MM-DD/`, uploads it to Cloudinary when configured, records the image path, SHA-256, public URL, provider, model, text policy, and upload provider, and blocks Buffer publishing until public image proof exists.

### Buffer credential setup

Buffer's current publishing API is GraphQL at `https://api.buffer.com`. Do not use the legacy REST endpoint `https://api.bufferapp.com/1/`; current Buffer API keys are rejected there with `Public API tokens are not accepted for REST API access`.

For ChatBot2U production publishing:

1. In Buffer, go to `Settings -> API` and create an API key for the account that owns the `@chatbot2u` Instagram channel, or use a Buffer OAuth access token with `posts:write`, `posts:read`, and `account:read`.
2. Set `BUFFER_ACCESS_TOKEN` to that Buffer API key/access token.
3. Find the Instagram Buffer channel ID using the Buffer API:

```bash
curl -X POST 'https://api.buffer.com' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $BUFFER_ACCESS_TOKEN" \
  -d '{"query":"query { account { organizations { id name } } }"}'
```

Then list channels for the organization:

```bash
curl -X POST 'https://api.buffer.com' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $BUFFER_ACCESS_TOKEN" \
  -d '{"query":"query GetChannels($organizationId: OrganizationId!) { channels(input: { organizationId: $organizationId }) { id name displayName service isQueuePaused } }","variables":{"organizationId":"YOUR_ORGANIZATION_ID"}}'
```

4. Set `BUFFER_PROFILE_ID` to the Instagram channel ID. The env name is kept for compatibility, but the value must be the current Buffer channel ID, not a legacy REST profile ID.
5. Validate before attempting a real publish:

```bash
python -m src.main --check-connectors
```

The connector check verifies the token, verifies that `BUFFER_PROFILE_ID` is accessible, and creates a Buffer draft validation post with `saveToDraft: true` so `posts:write` is proven without publishing publicly.

Actual publishing requires:

```bash
SOCIAL_PUBLISHING_ENABLED=true
BUFFER_ACCESS_TOKEN=
BUFFER_PROFILE_ID=
EXECUTION_DRY_RUN=false
IMAGE_GENERATION_ENABLED=true
OPENAI_IMAGE_MODEL=gpt-image-1
ASSET_UPLOAD_PROVIDER=cloudinary
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

Run the execution-only acceptance command:

```bash
python -m src.main --preflight
python -m src.main --check-connectors
python -m src.main --execute-marketing --require-business-artifact
```

These commands do not send the CEO brief. The preflight command prints clean readiness JSON for tomorrow's production run. The connector check prints clean connector JSON and exits non-zero if Buffer auth/channel/draft validation fails. The execution command runs the persistent workforce, writes `memory/actions/YYYY-MM-DD.json` and `memory/executions/YYYY-MM-DD.json`, prints clean execution JSON, and exits non-zero unless at least one verified business artifact was created.

The GitHub Actions acceptance workflow is:

```text
.github/workflows/autonomous-marketing.yml
```

Configure the CMO environment before using it as a real publishing run:

- Secrets: `OPENAI_API_KEY`, `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_TO`, `BUFFER_ACCESS_TOKEN`, `BUFFER_PROFILE_ID`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- Variables: `APP_ENV=production`, `SOCIAL_PUBLISHING_ENABLED=true`, `EXECUTION_DRY_RUN=false`, `IMAGE_GENERATION_ENABLED=true`, `ASSET_UPLOAD_PROVIDER=cloudinary`, `OPENAI_IMAGE_MODEL=gpt-image-1`

`ASSET_PUBLIC_BASE_URL` is optional when `ASSET_UPLOAD_PROVIDER=cloudinary` because Cloudinary returns the public image URL used by Buffer.

Actual campaign creation requires a real Meta execution provider:

```bash
META_EXECUTION_ENABLED=true
```

These flags do not make the repo pretend execution happened. A post is published only when the execution log contains Buffer post/update ID, Buffer/social URL, timestamp, caption hash, image SHA-256, public image URL, and worker ID. A campaign is active only when verified Meta data confirms it.

## Delivery Model

The AI CMO produces the brief and can send it independently through Resend.

Current model:

- `FileOutputChannel` saves the Markdown brief and structured JSON report.
- `--generate-brief` creates delivery-ready artifacts under `memory/`.
- `--send-now` generates the brief, saves Markdown/JSON, and sends via Resend when `RESEND_API_KEY` and `EMAIL_FROM` are configured.
- If Resend is not configured, `--send-now` saves the brief, marks delivery as `skipped` in the report, and prints setup instructions.
- Production daily delivery should run outside Codex, using the GitHub Actions workflow in `.github/workflows/daily-brief.yml`.
- The ChatGPT/Gmail connector is only a manual fallback. Codex is for development, not production daily delivery.

Resend settings:

```bash
RESEND_API_KEY=
EMAIL_FROM=AI CMO <briefs@yourdomain.com>
EMAIL_TO=rami@gateco.ai
```

Delivery status is stored in the daily JSON report:

```yaml
delivery:
  channel: resend
  status: sent
  recipient: rami@gateco.ai
  timestamp: "2026-07-03T08:00:00+03:00"
```

Standalone Gmail OAuth can be added later if needed. It is intentionally not required for Phase 0.4.

Optional standalone Gmail settings, currently disabled by default:

```bash
EMAIL_CHANNEL_ENABLED=false
GMAIL_CREDENTIALS_FILE=secrets/gmail_credentials.json
GMAIL_TOKEN_FILE=secrets/gmail_token.json
GMAIL_SENDER=your-sending-account@gmail.com
```

## CLI

Preview without saving:

```bash
python -m src.main --dry-run
```

Generate and save Markdown plus JSON report:

```bash
python -m src.main --generate-brief
```

Generate a clean JSON payload for ChatGPT/Gmail delivery:

```bash
python -m src.main --generate-email-body
```

Generate, save, and send now through Resend when configured:

```bash
python -m src.main --send-now
```

Run the scheduler:

```bash
python -m src.main
```

Optional health API:

```bash
python -m src.main --serve
```

## Memory

Daily runs write:

```text
memory/briefs/YYYY-MM-DD.md
memory/decisions/YYYY-MM-DD.json
memory/reports/YYYY-MM-DD.json
memory/runs/YYYYMMDD-HHMMSS.json
memory/actions/YYYY-MM-DD.json
memory/executions/YYYY-MM-DD.json
```

`memory/reports/YYYY-MM-DD.json` is the source of truth. The Markdown brief is only one view. Later, the same record can power email, dashboard, WhatsApp summary, weekly report, and monthly report.

## Judgment And Calibration

The operating principle is: we are no longer building features; we are building judgment.

Each daily report includes:

- A CEO scorecard for Judgment, Business Impact, Proactivity, Signal vs. Noise, and Learning.
- A measurable prediction tied to the day's highest-impact action.
- A pending prediction evaluation window, usually seven days.
- A Friday red-team challenge that questions one assumption.
- A 90-day success definition focused on publishing consistency, qualified demos, prediction quality, and measurable funnel improvement.

CEO scores are intentionally left blank in the JSON until Rami reviews the brief.

## Company State

ChatBot2U starts in `Validation`, configured in `config/objectives/chatbot2u.yaml`.

In Validation, the CMO prioritizes customer interviews, qualified demo bookings, WhatsApp conversion learning, and rapid iteration over scaling ad spend.

## Budget Rules

The ChatBot2U config encodes:

- Primary KPI: booked demos
- Budget: ₪20/day
- Saturday: no spend
- Friday: morning only
- CTA: WhatsApp +972559720244

## Environment

See `.env.example` for all supported variables.

## Production Daily Delivery

The production path is GitHub Actions plus Resend. The scheduled workflow runs:

```bash
python -m src.main --preflight
python -m src.main --send-now
```

The workflow runs daily at `05:00 UTC`, which is `08:00` in Israel during UTC+3 daylight time, and also supports manual runs through `workflow_dispatch`. `--send-now` executes the Marketing Workforce before generating the email, so the CEO brief reports Completed, Blocked, or Failed execution from that run.

Configure these GitHub CMO environment secrets before enabling the scheduled run:

```text
OPENAI_API_KEY
RESEND_API_KEY
EMAIL_FROM
EMAIL_TO
BUFFER_ACCESS_TOKEN
BUFFER_PROFILE_ID
CLOUDINARY_CLOUD_NAME
CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET
```

`EMAIL_TO` should normally be `rami@gateco.ai`. If it is not configured, the workflow falls back to `rami@gateco.ai`.

Required GitHub CMO environment variables:

```text
APP_ENV=production
SOCIAL_PUBLISHING_ENABLED=true
EXECUTION_DRY_RUN=false
IMAGE_GENERATION_ENABLED=true
ASSET_UPLOAD_PROVIDER=cloudinary
OPENAI_IMAGE_MODEL=gpt-image-1
```

Optional variables:

```text
OPENAI_MODEL
ASSET_PUBLIC_BASE_URL
META_API_VERSION
```

If `OPENAI_MODEL` is not set, the workflow uses `gpt-4o-mini`. `ASSET_PUBLIC_BASE_URL` is not required when Cloudinary upload is configured.

To send a brief manually:

1. Open the repository in GitHub.
2. Go to Actions.
3. Select `ChatBot2U Daily Brief`.
4. Choose `Run workflow`.

Do not rely on Codex scheduled threads for production daily delivery. Codex sessions can be sandboxed and may block the network calls required for OpenAI and Resend.

## ChatGPT Delivery Instructions

For manual fallback delivery through the ChatGPT/Gmail connector:

1. Run:

```bash
python -m src.main --generate-email-body
```

2. Parse the JSON printed to stdout.
3. Send `body_markdown` to `to` with `subject` using the Gmail connector.

The JSON payload has this shape:

```json
{
  "to": "rami@gateco.ai",
  "subject": "📊 ChatBot2U CEO Daily Brief – YYYY-MM-DD",
  "body_markdown": "...",
  "brief_path": "memory/briefs/YYYY-MM-DD.md",
  "report_path": "memory/reports/YYYY-MM-DD.json"
}
```
