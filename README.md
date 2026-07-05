# fortisil/ai-cmo v1.0

AI Executive Operating System foundation for ChatBot2U. The AI CMO is the first executive.

This version generates a structured daily executive report, renders an English CEO brief from it, sends it through Resend, and stores memory for learning. The first production KPI is booked demos; the ultimate KPI is paying customers.

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

For now, all marketing performance inputs are mocked until Instagram, WhatsApp Bot, Meta Ads, and Calendar integrations are added.

## Architecture

The daily run is:

```text
Company Knowledge + Objectives + MetricsProvider(s)
    -> DecisionEngine
    -> Structured DailyReport
    -> Hebrew brief
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
ExecutiveBrain -> ChiefOfStaff -> Execution
```

The ExecutiveBrain defines initiatives. The Chief of Staff chooses what runs today, what can wait, and what conflicts with delegated authority. Every autonomous action records what it did, why it did it, which policy authorized it, the expected outcome, and the actual outcome.

## v1.0 Foundation

This repository is now the foundation of an AI Executive Operating System. ChatBot2U's AI CMO is the first executive implementation.

Core executive layers:

- CEO Constitution: `knowledge/ceo_constitution.md`
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
- The CEO brief must separate recommended actions, prepared actions, and executed actions.
- If there is no verified data, the brief must say `No verified data available yet`.

## Operator Execution Queue

The AI Executive OS should operate the business, not only report on it.

Every daily report includes an internal `execution_queue` with:

- `initiative`: the business initiative for the day.
- `today_mission`: the concrete outcome the AI CMO is trying to create.
- `currently_working_on`: tasks ready to execute under delegated authority.
- `internal_tasks`: AI-owned work such as Meta sync, WhatsApp tracking, CTA review, content preparation, competitor/ICP research, and repository review.
- `pending_escalations`: decisions that exceed delegated authority.

Internal tasks are not user tasks. They should not clutter the CEO brief.

The CEO brief should stay to one page and include only:

- Executive summary.
- What changed.
- Today's initiative.
- What was executed.
- What is currently in progress.
- Decisions requiring escalation.

If `executed_actions_today` is `none`, the AI CMO must still produce a useful execution queue for itself.

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
python -m src.main --send-now
```

The workflow runs daily at `05:00 UTC`, which is `08:00` in Israel during UTC+3 daylight time, and also supports manual runs through `workflow_dispatch`.

Configure these GitHub repository secrets before enabling the scheduled run:

```text
OPENAI_API_KEY
RESEND_API_KEY
EMAIL_FROM
EMAIL_TO
```

`EMAIL_TO` should normally be `rami@gateco.ai`. If it is not configured, the workflow falls back to `rami@gateco.ai`.

Optional GitHub repository variable:

```text
OPENAI_MODEL
```

If `OPENAI_MODEL` is not set, the workflow uses `gpt-4o-mini`.

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
