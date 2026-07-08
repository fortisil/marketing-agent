from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any

from openai import OpenAI

from src.config import Settings
from src.decisions.engine import DecisionContext


FORBIDDEN_TERMS = ("נגנבו", "WattsApp")
EXECUTIVE_DECISION_STARTS = (
    "Yesterday the business became healthier because",
    "Yesterday the business did not improve because",
)
EXECUTIVE_DECISION_REQUIRED_MARKERS = (
    "Executive Decision",
    "EXECUTIVE SCOREBOARD",
    "Revenue CMO",
    "Manager Performance",
    "Executive Summary",
    "Yesterday",
    "Results",
    "Business Funnel",
    "Content Intelligence",
    "Campaign Intelligence",
    "Campaign Decision",
    "Website Intelligence",
    "Competitor Intelligence",
    "WhatsApp Intelligence",
    "Decision Ledger",
    "Currently Working",
    "Self Evaluation",
    "Business Memory",
    "Budget",
    "Opportunity Ranking",
    "Risks",
    "Executive Calendar",
    "Proof",
    "If I were the CEO today",
)
EXECUTIVE_DECISION_FORBIDDEN_PHRASES = (
    "I published",
    "I prepared",
    "ready to publish",
    "ready to execute",
    "prepared for",
    "queued for",
    "publishing path exists",
    "connector runtime exists",
    "execution path is implemented",
)
CAMPAIGN_AUTONOMY_ANSWERS = (
    "Campaign launched.",
    "Campaign intentionally not launched.",
    "Campaign blocked and CEO action required.",
    "Campaign failed and automatic retry scheduled.",
)


def build_prompt(
    company_config: dict[str, Any],
    decision_context: DecisionContext,
    hebrew_style_guide: str,
    brief_language: str = "en",
) -> str:
    company = company_config["company"]
    marketing = company_config["marketing"]
    budget_rule = marketing["budget_rule"]
    cta = marketing["cta"]
    decision_payload = json.dumps(
        _compact_prompt_payload(decision_context),
        ensure_ascii=False,
        sort_keys=True,
    )
    language = (brief_language or company.get("brief_language") or "en").strip().lower()

    if language in {"en", "english"}:
        return f"""
Write a daily CEO brief in English for {company["name"]}.

This is not a generic report. It is an Executive Decision Brief for Rami. It must help him understand whether ChatBot2U is closer to acquiring another paying customer than it was yesterday. Write like an operator who manages business outcomes, not an activity reporter.

Mandatory opening line:
- Start the brief with exactly one of these two sentence patterns:
  - "Yesterday the business became healthier because ..."
  - "Yesterday the business did not improve because ..."
- Never start with "I published", "I prepared", activity narration, or infrastructure status.
- If measurable customer-acquisition improvement cannot be proven, say that directly and make the highest priority discovering why.

Immediately after the mandatory opening line, include the trust banner:
Data confidence:
- High: real data from connected source
- Medium: partial real data
- Low: no verified data / mock disabled

Use the `data_confidence`, `data_status`, `metric_sources`, `execution_reality`, `execution_queue`, `connector_execution`, `autonomous_work_completion_rate`, `revenue_influence_score`, `business_autonomy_index`, `executive_measurement`, `operating_executive`, `revenue_cmo`, `growth_intelligence`, `promotion_brain`, `budget_status`, `budget_guard`, `campaign_decision`, `content_intelligence`, `decision_ledger`, `hypothesis_register`, `business_memory`, `monitoring`, `weekly_executive_review`, `acceptance_criteria`, `final_definition_of_done`, `self_evaluation`, `workforce`, `marketing_department`, `whatsapp_bot`, `meta_ads`, `website_intelligence`, and `brand_intelligence` fields from the DailyReport as source of truth.

Hard rules:
- The active role is Revenue CMO, not social media manager. The primary KPI is: generate qualified law firm demos that convert into paying customers.
- Use `revenue_cmo` as the source of truth for marketing scores, channel review, post scoring, Meta Ads recommendation, highest-impact recommendation, top 3 priorities, risks, and recommended next action.
- Every recommendation must improve one of these metrics: qualified leads, demo bookings, closed customers, cost per qualified lead, customer acquisition cost, or revenue.
- Do not optimize vanity metrics. Followers, impressions, likes, posts, and publishing frequency matter only if they increase qualified demos or customers.
- Never recommend publishing content simply to maintain activity.
- Every published post must be reviewed as a revenue asset, scored 1-10 for hook, trust, professionalism, visual quality, value proposition, CTA, and relevance to Israeli law firms. If below 8/10, explain why and how to improve it.
- The Creative Director must prefer founder content, product screenshots, customer stories, before/after workflows, short demo videos, WhatsApp conversations, real legal examples, testimonials, and ROI proof. Do not recommend generic AI artwork, robots, floating icons, or stock-looking graphics.
- Meta Ads recommendations must be exactly one of: Launch, Pause, Scale, Reduce budget, Change audience, Change creative, Change objective, or Duplicate winning ad. Always explain why.
- Never recommend spending more money unless the creative and landing page are ready.
- Every section must serve one sentence: "This capability increases the probability that ChatBot2U acquires another paying customer." If it does not, omit it.
- The Executive OS is not evaluated by activities. It is evaluated by measurable business improvement.
- Every morning the AI must prove that the probability of acquiring another paying customer increased. If it cannot prove that, its highest priority is discovering why.
- The AI is no longer evaluated by reports, activities, completed tasks, or generated content. It is evaluated by: "Did it manage the business today?"
- Every department manager permanently owns business assets. Never present them as temporary task owners.
- Use `operating_executive.manager_reports` as the management-team source of truth. Every manager must report current status, business objective, current KPI, trend, risk, decision, and next review.
- Use `operating_executive.internal_budget_ledger` as authoritative. Never write that the budget is unavailable. Meta only reconciles the internal ledger.
- Use `operating_executive.campaign_registry`, `content_registry`, `competitor_registry`, `whatsapp_intelligence`, `website_management`, `executive_memory`, and `self_management` to show permanent ownership and continuity.
- Never optimize activity. Always optimize customer acquisition.
- Never invent KPI numbers.
- If a metric has `source: unavailable` or `verified: false`, write "No verified data available yet" instead of a number.
- Never leave the CEO with a bare "Unavailable" row. If data is unavailable, include: why, business impact, automatic action, expected review/completion, and confidence.
- Use three evidence levels: verified internal data, public platform signals, and clearly labeled hypotheses. If verified internal data is missing, keep operating with the best available evidence and label confidence.
- The brief must answer these measurement questions: What improved? Why? What got worse? What are we changing? What do we expect tomorrow? How will we know if we were right?
- Clearly separate real data, mock data, unavailable data, completed execution, blocked execution, failed execution, and next automatic retry.
- The brief is not an activity log. It is an executive dashboard.
- The CEO should be able to read it in under 90 seconds and immediately understand: business health, measurable value, yesterday, today, next action, biggest opportunity, and biggest risk.
- Include budget status only as operating proof: daily limit, monthly limit, active campaign status, and whether spend is verified. Do not imply spend occurred unless verified.
- Include learning only from `growth_intelligence`, `content_intelligence`, `hypothesis_register`, `decision_ledger`, and `business_memory`. If learning is pending because attribution is missing, say that directly.
- Include promotion only from `promotion_brain` and `budget_guard`. If Budget Guard blocks campaign creation, report the failed rule and next automatic retry.
- The brief must include a section titled exactly "Campaign Decision".
- The Campaign Decision section must use this exact structure:
  Campaign Decision:
  - Decision:
  - Reason:
  - Budget:
  - Status:
  - Next Automatic Action:
  - Retry Time:
  - CEO Action Required: Yes/No
  - Evidence:
- The Campaign Decision section must contain exactly one of these status answers:
  - Campaign launched.
  - Campaign intentionally not launched.
  - Campaign blocked and CEO action required.
  - Campaign failed and automatic retry scheduled.
- If launched, evidence must include Meta Campaign ID, Ad Set ID, Ad ID, Budget, Start time, Linked Instagram post, and Tracked WhatsApp link.
- If not launched, evidence must include Rules checked, Failed rules, and Next retry time.
- If attribution is missing, do not block exploration mode only for that reason. Label the decision low-confidence and use the controlled exploration rules from `campaign_decision`.
- Never leave the CEO asking "Will the campaign run?" The section must answer did launch, did not launch intentionally, blocked with CEO action, or failed with automatic retry.
- Use `monitoring` for health status, last successful run, next scheduled run, and blocking issues. Do not invent monitoring status.
- Include `Self-Evaluation` near the end. Answer only these five questions from `self_evaluation`: measurable business value, evidence, biggest positive decision, wrong decision, tomorrow's change.
- Workforce queue internals belong in memory. Mention only completed work, blocked work, business impact, autonomous completion rate, revenue influence, and business autonomy index.
- The Executive Layer is frozen except for bug fixes. New capability belongs in autonomous departments.
- The active department is Marketing Operations. The CEO brief must answer: "Are we closer to another paying customer than we were yesterday?"
- Do not ask the CEO to fetch metrics. If Meta/WhatsApp sync is pending, describe it as an internal execution queue item with status and retry.
- Do not claim content was published, an ad was started, or outreach was sent unless the relevant department action has status `executed` and contains required evidence. If there is no evidence, the action did not happen.
- For published Instagram content, required evidence is Buffer update ID, Buffer post URL, publish status, timestamp, caption hash, image hash, and worker ID. Include an Instagram permalink only when Buffer returns a real `instagram.com` URL.
- Do not tell the CEO that something is "ready", "prepared", or "queued". Prepared tasks belong only in internal memory.
- Do not describe infrastructure to the CEO. Never write phrases like "publishing path exists", "connector runtime exists", or "execution path is implemented".
- Only report: Completed, Blocked, Failed, and Next automatic retry.
- Do not imply that a Meta campaign is active unless `campaign_status` is `active` and verified.
- If no verified campaign exists, say: "No campaign has been verified as active."
- If WhatsApp data is unavailable, say: "No verified WhatsApp event data available."
- Include: "To track WhatsApp leads, connect the WhatsApp bot event log/webhook."
- Every completed item requires proof. Acceptable proof includes Instagram URL, Buffer ID, Campaign ID, Cloudinary URL, GitHub PR, Video URL, Report URL, timestamp, and SHA/hash. If there is no proof, do not report the item as completed.
- Use English headings and English body copy.
- The CEO brief to Rami must be English. Do not write Hebrew except for brand names, quoted terms, or phone/contact details.
- Use DailyReport as the source of truth. The email is only a Markdown view of the structured data.

Keep the CEO brief concise. Use these sections in this order:
0. Mandatory opening sentence: "Yesterday the business became healthier because ..." or "Yesterday the business did not improve because ...".
1. Executive Decision:
   - Exactly one short paragraph.
   - Use `executive_measurement.executive_decision.paragraph`.
   - Explain what happened, whether the business is closer to a customer, what decision is next, when the AI will decide, and the biggest measurement blocker.
2. EXECUTIVE SCOREBOARD:
   - No paragraphs.
   - Numbers/status only.
   - Include Business Health, Marketing Health, Revenue Momentum, Pipeline, Booked Demos, New Customers, Monthly Revenue, Marketing ROI, Today's Confidence, Business Autonomy, and Status.
   - Business Health must never be unavailable. Use `executive_measurement.business_health.score`, status, reason, and trend.
   - Use "No verified data available yet" only for unverified numeric KPIs, and explain why in the relevant intelligence section.
3. Revenue CMO:
   - Use `revenue_cmo`.
   - Include Primary KPI, Marketing Score, Website Score, Instagram Score, Meta Ads Score, Sales Funnel Score, Highest-impact recommendation, Top 3 priorities, Risks, and Recommended next action.
   - Answer the seven daily Revenue CMO questions: what changed, new leads, demo bookings, most valuable activity, today's revenue-maximizing action, Meta Ads decision, and single highest-ROI task.
   - Include a short post-review verdict if a published asset exists, including the 1-10 score and whether it passed the 8/10 quality bar.
   - Do not report vanity metrics unless connected to qualified leads, demo bookings, customers, CPL, CAC, or revenue.
4. Manager Performance:
   - The CEO should feel like reading reports from an executive team, not software logs.
   - Use `operating_executive.manager_reports`.
   - Include Social Manager, Ads Manager, Analytics Manager, Website Manager, Creative Director, and Growth Manager.
   - For each manager show: Status, Business Objective, Current KPI, Trend, Risk, Decision, Next Review.
   - Highlight which managers performed well and which need attention.
5. Executive Summary:
   - Maximum five bullets.
   - Business outcome first, not activity first.
6. Yesterday:
   - Created, Published, Promoted, Website changes, Videos, Images, Emails, Campaigns, PRs, Competitor analysis, Learning completed.
   - Every completed line must include evidence or say none completed.
7. Results:
   - Instagram, WhatsApp clicks, website visits, conversion, demo requests, booked demos, customers, revenue.
   - Compare to yesterday, last week, and average only when real data exists.
   - If a result is missing, explain why, business impact, automatic action, expected review/completion, and confidence.
8. Business Funnel:
   - Reach -> Clicks -> WhatsApp -> Qualified -> Demo -> Customer.
   - For each step show Current, Yesterday, Change, Target, Conversion, Bottleneck.
   - Highlight the bottleneck automatically.
9. Content Intelligence:
   - Score every published asset when verified data exists.
   - Include Business Value Score, Creative Score, Conversion Score, Expected ROI, Recommendation, and Reason.
   - If the post is under review, use `executive_measurement.instagram_performance`: published time, current metrics, reason metrics are missing, automatic action, review time, and recommendation.
   - Use `operating_executive.content_registry` for lifecycle: Published, Measured, Ranked, Promoted, Retired, Learning, Business Value Score.
10. Campaign Intelligence:
   - Show organic/running status, spend, CTR, CPC, WhatsApp, qualified, demos, customers, recommendation, expected ROI.
   - If Meta is unavailable, show `executive_measurement.campaign_if_available.campaign_to_launch`: audience, budget, objective, expected CPL, stop rule, schedule, and why it is blocked.
   - Use `operating_executive.campaign_registry`. Never write "Campaign unavailable"; show registry status, status reason, and next campaign decision.
11. Campaign Decision:
   - Use `campaign_decision` only.
   - Use the exact required structure and one of the four explicit campaign answers.
   - Include budget fields from `campaign_decision.budget_status`, not inferred prose.
   - CEO Action Required must be exactly Yes or No.
12. Website Intelligence:
   - Visitors, conversion, CTA clicks, most viewed page, worst page, bounce, top search query, recommendation, and whether to open a PR.
   - Use `operating_executive.website_management`.
13. Competitor Intelligence:
   - Analyzed, top campaign, opportunity, threat, recommended response. If not connected, say unavailable.
   - If not connected, say what public/platform signal will be used until competitor monitoring exists.
   - Use `operating_executive.competitor_registry`.
14. WhatsApp Intelligence:
   - Conversations, qualified, demo requests, booked, closed, lost, most common objection, response quality, average response time, recommendation.
   - If missing, use `executive_measurement.whatsapp_measurement`: status, business impact, automatic action, expected completion, confidence.
   - Use `operating_executive.whatsapp_intelligence` for intent, objections, drop-offs, booking quality, lead quality, lost reasons, and recommendation.
15. Decision Ledger:
   - Today's decisions, reason, expected outcome, and how success will be measured.
16. Currently Working:
   - Only real work in progress. No fake progress, no "ready", no "prepared", no "queued".
   - Use `executive_measurement.today_operating_work` for what the AI is doing today while Rami is working.
   - Use `operating_executive.self_management.manager_actions` to show what will happen automatically today.
17. Self Evaluation:
   - Yesterday's prediction, result, prediction confidence, learning, and whether a Business Memory rule was added.
   - If evidence is pending, say when the prediction will be reviewed and what changes if it is wrong.
18. Business Memory:
   - New learning only. If none is verified, say none verified.
   - Use `operating_executive.executive_memory` for campaigns, experiments, insights, failures, successful strategies, creative patterns, promotion history, and budget history.
19. Budget:
   - Use `operating_executive.internal_budget_ledger`.
   - Show Monthly budget, Reserved, Committed, Spent, Forecast, Remaining, per campaign, per experiment, and per asset.
   - Budget is internally authoritative even when Meta reconciliation is pending.
20. Opportunity Ranking:
   - The most important section. Rank today's opportunities by expected customer-acquisition impact and confidence.
   - Do not list the mission as the opportunity. Use `executive_measurement.opportunity`.
21. Risks:
   - Real business risks and mitigations.
22. Executive Calendar:
   - Today only. Show what the AI will do and when, using local Israel time.
23. Proof:
   - Evidence IDs/URLs/hashes for every completed action.
24. CEO Question:
   - End with exactly one sentence: "If I were the CEO today, I would focus on: ___ because ___."

Do not include long internal task lists in the CEO brief. Those belong in memory under `execution_queue`.

Budget rules:
- Daily budget: ₪{budget_rule["amount_ils_per_day"]}
- Saturday: {budget_rule["saturday"]}
- Friday: {budget_rule["friday"]}
- Note: {budget_rule["note"]}

CTA if relevant: {cta["channel"]} {cta["phone"]}.

Decision context and metrics:
{decision_payload}

Today by local time: {datetime.now().strftime("%Y-%m-%d")}
Return only the CEO brief in Markdown.
""".strip()

    return f"""
כתוב בריף מנכ"ל יומי בעברית עבור {company["name"]}.

זה לא "דוח". זה בריף של AI CMO שמטרתו לעזור ל-ChatBot2U להזמין יותר דמואים.

השתמש בעברית עסקית ישראלית, טבעית ומקצועית. אין לתרגם מילולית מאנגלית.
כתוב "WhatsApp" בדיוק כך בכל אזכור. אסור לכתוב "WattsApp".
אסור להשתמש במילה "נגנבו" בהקשר של לידים, פניות, שיחות או דמואים.

מדריך סגנון עברית מחייב:
{hebrew_style_guide}

הבריף צריך להיות חד, פרקטי וקצר, מיועד למנכ"ל, ולכלול:
1. Executive Summary.
2. Today's Mission.
3. Business Health.
4. Marketing Health.
5. מקטע חובה בשם "📊 Funnel Summary" שמסכם את WhatsApp Bot funnel כמקור ה-KPI המרכזי.
6. Website Health.
7. Content Plan.
8. Promotion Decision.
9. Campaign Decision.
10. Top Three Tasks.
11. Expected Business Impact.
12. Confidence.
13. Delivery Status אם קיים ב-DailyReport.
14. Learning Since Yesterday.
15. Judgment & Calibration:
   - ציין שהמטרה היא שיפור שיקול הדעת, לא הוספת פיצ'רים.
   - כלול את התחזית היומית מתוך prediction במשפט קצר.
   - ציין מתי צריך לבדוק את התחזית.
   - אם red_team_challenge.active_today=true, כלול שאלת Red Team קצרה.
16. שורות ברורות עבור:
   - Today's bottleneck
   - Highest impact recommendation
   - Estimated business impact
   - Confidence
17. CTA ברור: {cta["channel"]} {cta["phone"]}.

השתמש במונחים המועדפים:
- פניות חדשות
- לידים כשירים
- פגישות הדגמה שנקבעו
- המלצה לפעולה
- משימה מרכזית להיום

כללי תקציב שחייבים להופיע בהחלטות:
- תקציב יומי: ₪{budget_rule["amount_ils_per_day"]}
- שבת: {budget_rule["saturday"]}
- שישי: {budget_rule["friday"]}
- הערה: {budget_rule["note"]}

קונטקסט החלטות ומדדים:
{decision_payload}

השתמש ב-DailyReport כמקור האמת. האימייל הוא רק תצוגת Markdown של הנתונים המובנים.
התייחס ל-CEO Constitution כמסמך התרבות והגבולות הראשון של המערכת.
כל המלצה צריכה לכלול ביטחון או רמת ודאות כאשר זה טבעי.
הדגש את Today's Mission כמשימה אחת בלבד.
התייחס ל-whatsapp_bot בתור מקור האמת ל-funnel: פניות חדשות, לידים כשירים, בקשות דמו, פגישות הדגמה שנקבעו ולקוחות.
התייחס ל-AI CMO כמנהל עצמאי שלא ממתין למשימות. אם אין פעולה ברורה, עליו לייצר עבודה מועילה: סקירת אתר, ריפו, שיווק, מתחרים, SEO, funnel, שיחות WhatsApp, השערות וניסויים.
כבד את delegated_authority: ה-AI CMO פועל תחת סמכות מואצלת, לא תחת אישור מתמשך. עליו לבצע כאשר הוא מוסמך, לתעד כל החלטה משמעותית, ולהסלים רק כשפעולה חורגת מגבולות הסמכות.
התייחס ל-Chief of Staff plan כמסנן הביצוע: מה רץ היום, מה יכול להמתין, ומה חורג מגבולות הסמכות.
התייחס ל-Initiatives כמבנה המרכזי: יוזמה מובילה, משימות תומכות, KPI, אימפקט צפוי וביטחון.
התייחס ל-judgment_scorecard, prediction, prediction_evaluation, red_team_challenge ו-success_90_day_status כמנגנון מדידת איכות החלטות.
אל תבקש מהמנכ"ל "אישור" על כל פעולה. בקש ממנו לציין ציון רק אם הוא בוחר למדוד את איכות הבריף. הניסוח צריך להיות מנהלי וקצר.
אם קיימת prediction, הצג אותה כתחזית עסקית מדידה, לא כהבטחה.
אם קיימת success_90_day_status, קשר את ההמלצה המרכזית ליעד 90 הימים רק במשפט אחד.
התייחס ל-brand_intelligence כמקור האמת למותג. ה-AI לא מנחש מיתוג כאשר Brand Library זמינה.
אם Design System Agent לא מאשר, אל תמליץ על פרסום creative אוטונומי; המלץ להשלים/לתקן את Brand Library או ליצור טיוטה בלבד.
אם קיימים board_advisors, שקף בקצרה את ההכרעה הסופית של Executive Brain אחרי שקלול הפרספקטיבות, בלי להפוך את הבריף לוויכוח פנימי.
אם marketing_platform מציין ש-Meta MCP דורש הרצה חיצונית, אל תכתוב שנתוני Meta "מנותקים" או "לא זמינים" באופן כללי.
כתוב בעברית עסקית: "נתוני Meta זמינים דרך MCP, אך הריצה המקומית אינה מפעילה MCP ישירות. נדרש סנכרון דרך ChatGPT/Meta MCP או הפעלת Graph API fallback."

היום לפי זמן מקומי: {datetime.now().strftime("%Y-%m-%d")}
אל תכתוב באנגלית מלבד השם WhatsApp, שמות מוצרים, ומונחי KPI קיימים מהקונטקסט.
אל תמציא נתונים מעבר לקונטקסט. אם חסר מידע, ציין שזה נתון זמני או חיבור עתידי.
לפני החזרת התשובה, בדוק שאין בה את המילים האסורות: נגנבו, WattsApp.
""".strip()


def _compact_prompt_payload(decision_context: DecisionContext) -> dict[str, Any]:
    if not hasattr(decision_context, "summary"):
        if hasattr(decision_context, "to_prompt_payload"):
            return _compact_value(decision_context.to_prompt_payload(), depth=0)
        return {}

    summary = decision_context.summary
    selected_summary = {
        key: summary.get(key)
        for key in [
            "data_confidence",
            "data_status",
            "metric_sources",
            "execution_reality",
            "executed_actions_today",
            "blocked_actions",
            "failed_actions",
            "autonomous_work_completion_rate",
            "revenue_influence_score",
            "business_autonomy_index",
            "executive_measurement",
            "operating_executive",
            "revenue_cmo",
            "growth_intelligence",
            "promotion_brain",
            "budget_status",
            "budget_guard",
            "campaign_decision",
            "campaign_run_answer",
            "content_intelligence",
            "decision_ledger",
            "hypothesis_register",
            "business_memory",
            "monitoring",
            "weekly_executive_review",
            "self_evaluation",
            "connector_execution",
            "whatsapp_bot",
            "meta_ads",
            "website_intelligence",
            "brand_intelligence",
        ]
        if key in summary
    }
    if isinstance(selected_summary.get("revenue_cmo"), dict):
        selected_summary["revenue_cmo"] = _compact_revenue_cmo(selected_summary["revenue_cmo"])
    return _compact_value(
        {
            "run_date": decision_context.run_date,
            "questions": decision_context.questions,
            "summary": selected_summary,
            "decisions": decision_context.decisions[:12],
            "highest_roi_activity": decision_context.highest_roi_activity,
            "risks": decision_context.risks[:12],
            "daily_report": {
                "company": decision_context.daily_report.company,
                "company_state": decision_context.daily_report.company_state,
                "date": decision_context.daily_report.date,
                "mission": decision_context.daily_report.mission,
                "objective_status": decision_context.daily_report.objective_status,
                "initiatives": [
                    initiative.to_dict()
                    for initiative in decision_context.daily_report.initiatives[:4]
                ],
                "recommendations": [
                    recommendation.to_dict()
                    for recommendation in decision_context.daily_report.recommendations[:6]
                ],
                "confidence": decision_context.daily_report.confidence,
                "next_review": decision_context.daily_report.next_review,
            },
            "snapshots": [
                {
                    "provider": snapshot.provider,
                    "collected_at": snapshot.collected_at.isoformat(),
                    "notes": snapshot.notes[:4],
                    "metric_groups": list(snapshot.metrics.keys())[:12],
                }
                for snapshot in decision_context.snapshots
            ],
        },
        depth=0,
    )


def _compact_revenue_cmo(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": report.get("role"),
        "primary_kpi": report.get("primary_kpi"),
        "revenue_metrics": report.get("revenue_metrics"),
        "vanity_metric_policy": report.get("vanity_metric_policy"),
        "decision_framework": report.get("decision_framework"),
        "daily_review_questions": report.get("daily_review_questions"),
        "scores": report.get("scores"),
        "published_post_review": report.get("published_post_review"),
        "meta_ads_decision": report.get("meta_ads_decision"),
        "highest_impact_recommendation": report.get("highest_impact_recommendation"),
        "top_3_priorities": report.get("top_3_priorities"),
        "risks": report.get("risks"),
        "recommended_next_action": report.get("recommended_next_action"),
    }


def _compact_value(value: Any, *, depth: int) -> Any:
    if depth > 8:
        return "<truncated>"
    if isinstance(value, dict):
        return {
            str(key): _compact_value(item, depth=depth + 1)
            for key, item in list(value.items())[:40]
            if item is not None
        }
    if isinstance(value, list):
        return [_compact_value(item, depth=depth + 1) for item in value[:20]]
    if isinstance(value, tuple):
        return [_compact_value(item, depth=depth + 1) for item in value[:20]]
    if isinstance(value, str):
        if len(value) > 1600:
            return value[:1600] + "... <truncated>"
        return value
    return value


def generate_brief(
    settings: Settings,
    company_config: dict[str, Any],
    decision_context: DecisionContext,
    hebrew_style_guide: str,
) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to generate the brief.")

    client = OpenAI(api_key=settings.openai_api_key)

    brief_language = settings.brief_language or company_config["company"].get("brief_language", "en")
    system_content = (
        "You are an AI CMO chief of staff writing an Executive Decision Brief for a CEO. "
        "Write concise, professional English focused on customer acquisition, business health, "
        "evidence, bottlenecks, and next decisions. "
        "Never invent metrics. If data is unavailable or unverified, say so clearly. "
        "Never write an activity log. Return only the CEO brief."
    )
    if str(brief_language).lower() in {"he", "hebrew", "עברית"}:
        system_content = (
            "You are an Israeli Hebrew-speaking CMO chief of staff. "
            "Write concise, professional business Hebrew. "
            "Always spell WhatsApp exactly as WhatsApp. "
            "Never use the Hebrew word נגנבו for leads or inquiries. "
            "Return only the CEO brief."
        )

    messages = [
        {
            "role": "system",
            "content": system_content,
        },
        {
            "role": "user",
            "content": build_prompt(
                company_config,
                decision_context,
                hebrew_style_guide,
                brief_language=brief_language,
            ),
        },
    ]

    last_error: RuntimeError | None = None
    for attempt in range(2):
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
        )

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned an empty brief.")

        normalized = _enforce_campaign_decision_section(
            _enforce_revenue_cmo_section(
                _ensure_executive_opening(
                    normalize_brief_language(content.strip()),
                    decision_context,
                ),
                decision_context,
            ),
            decision_context,
        )
        try:
            validate_hebrew_brief_style(normalized)
            if str(brief_language).lower() in {"en", "english"}:
                validate_executive_decision_brief_style(normalized)
            return normalized
        except RuntimeError as exc:
            last_error = exc
            if attempt == 1 or str(brief_language).lower() not in {"en", "english"}:
                raise
            messages.extend(
                [
                    {"role": "assistant", "content": normalized},
                    {
                        "role": "user",
                        "content": (
                            "Rewrite the brief to satisfy the Executive Decision Brief contract. "
                            f"Validation failed: {exc}. "
                            "Start with the mandatory business-health sentence, include all required "
                            "executive sections, avoid activity-log language, never use bare unavailable rows, "
                            "and use only verified data or clearly labeled lower-confidence evidence."
                        ),
                    },
                ]
            )

    raise last_error or RuntimeError("Failed to generate a valid Executive Decision Brief.")


def normalize_brief_language(brief: str) -> str:
    replacements = {
        "WattsApp": "WhatsApp",
        "וואטסאפ": "WhatsApp",
        "ווטסאפ": "WhatsApp",
        "Today's bottledneck": "Today's bottleneck",
        "Todays bottleneck": "Today's bottleneck",
        "לחומש את": "להגדיל את",
        "להמריא את": "להגדיל את",
        "להעביר לידים כשהם מתאימים": "להמיר לידים כשירים",
        "ינסח לפחות 1 פגישת הדגמה": "יוביל לפחות לפגישת הדגמה אחת",
        "לפחות 1 פגישת הדגמה": "לפחות פגישת הדגמה אחת",
        "הדמיות": "פגישות הדגמה",
        "נגנבו לידים": "נוצרו לידים",
        "נגנבו פניות": "התקבלו פניות",
        "נגנבו שיחות": "נפתחו שיחות חדשות",
        "נגנבו": "התקבלו",
    }
    normalized = brief
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


def _ensure_executive_opening(brief: str, decision_context: DecisionContext) -> str:
    first_line = next((line.strip() for line in brief.splitlines() if line.strip()), "")
    cleaned_first_line = re.sub(r"^[#>*_\-\s]+", "", first_line).strip()
    if cleaned_first_line.startswith(EXECUTIVE_DECISION_STARTS):
        return brief

    opening = _structured_executive_opening(decision_context)
    return f"{opening}\n\n{brief.lstrip()}".strip()


def _structured_executive_opening(decision_context: DecisionContext) -> str:
    measurement = decision_context.summary.get("executive_measurement", {})
    if not isinstance(measurement, dict):
        measurement = {}
    business_health = measurement.get("business_health", {})
    if not isinstance(business_health, dict):
        business_health = {}

    trend = str(business_health.get("trend") or "").lower()
    status = str(business_health.get("status") or "").lower()
    improved = trend == "improving" or status == "improving"
    reason = _business_health_reason(business_health.get("reason"), improved=improved)

    if improved:
        return f"Yesterday the business became healthier because {reason}"
    return f"Yesterday the business did not improve because {reason}"


def _business_health_reason(value: Any, *, improved: bool) -> str:
    fallback = (
        "verified business-health signals improved."
        if improved
        else "no verified customer-acquisition improvement was proven yet."
    )
    if not isinstance(value, list):
        return fallback

    preferred_prefix = "+" if improved else "-"
    candidates = [
        str(item).strip()
        for item in value
        if isinstance(item, str) and str(item).strip().startswith(preferred_prefix)
    ]
    if not candidates:
        candidates = [
            str(item).strip()
            for item in value
            if isinstance(item, str) and str(item).strip()
        ]
    if not candidates:
        return fallback

    reason = re.sub(r"^[+\-]\s*", "", candidates[0]).strip()
    if not reason:
        return fallback
    first_word = reason.split(maxsplit=1)[0]
    if len(first_word) > 1 and first_word[1:].islower():
        reason = reason[0].lower() + reason[1:]
    return reason if reason.endswith((".", "!", "?")) else reason + "."


def _enforce_revenue_cmo_section(brief: str, decision_context: DecisionContext) -> str:
    section = _revenue_cmo_markdown(decision_context)
    if not section:
        return brief
    pattern = re.compile(r"(?ms)^#{2,3}\s+Revenue CMO:?.*?(?=^#{2,3}\s+|\Z)")
    if pattern.search(brief):
        return pattern.sub(section + "\n\n", brief, count=1).strip()
    insert_before = re.search(r"(?m)^#{2,3}\s+Manager Performance", brief)
    if insert_before:
        index = insert_before.start()
        return (brief[:index].rstrip() + "\n\n" + section + "\n\n" + brief[index:].lstrip()).strip()
    insert_after = re.search(r"(?ms)^#{2,3}\s+EXECUTIVE SCOREBOARD:?.*?(?=^#{2,3}\s+|\Z)", brief)
    if insert_after:
        index = insert_after.end()
        return (brief[:index].rstrip() + "\n\n" + section + "\n\n" + brief[index:].lstrip()).strip()
    return (brief.rstrip() + "\n\n" + section).strip()


def _revenue_cmo_markdown(decision_context: DecisionContext) -> str:
    report = decision_context.summary.get("revenue_cmo", {})
    if not isinstance(report, dict) or not report:
        return ""

    scores = report.get("scores", {})
    priorities = report.get("top_3_priorities", [])
    risks = report.get("risks", [])
    meta_decision = report.get("meta_ads_decision", {})
    post_review = report.get("published_post_review", {})
    highest = report.get("highest_impact_recommendation", {})

    def score_line(name: str, key: str) -> str:
        item = scores.get(key, {}) if isinstance(scores, dict) else {}
        return f"- {name}: {item.get('score')}/10. {item.get('reason')}"

    priority_lines = []
    if isinstance(priorities, list):
        for item in priorities[:3]:
            if isinstance(item, dict):
                priority_lines.append(
                    f"  {item.get('rank')}. {item.get('action')} "
                    f"(Impact: {item.get('expected_revenue_impact')}; Effort: {item.get('effort')}; "
                    f"Time: {item.get('time_to_results')})"
                )

    risk_lines = []
    if isinstance(risks, list):
        for item in risks[:3]:
            if isinstance(item, dict):
                risk_lines.append(f"  - {item.get('risk')} Mitigation: {item.get('mitigation')}")

    daily_questions = report.get("daily_review_questions", [])
    question_text = "; ".join(str(item) for item in daily_questions[:7]) if isinstance(daily_questions, list) else ""
    post_score = post_review.get("score") if isinstance(post_review, dict) else None
    post_text = (
        f"{post_score}/10; {post_review.get('explanation')} Recommendation: {post_review.get('recommendation')}"
        if post_score is not None
        else "No published asset proof is available for scoring."
    )

    lines = [
        "### Revenue CMO",
        f"- Primary KPI: {report.get('primary_kpi')}",
        score_line("Marketing Score", "marketing"),
        score_line("Website Score", "website"),
        score_line("Instagram Score", "instagram"),
        score_line("Meta Ads Score", "meta_ads"),
        score_line("Sales Funnel Score", "sales_funnel"),
        f"- Highest-impact recommendation: {highest.get('action') if isinstance(highest, dict) else report.get('highest_impact_recommendation')}",
        "- Top 3 priorities:",
        *priority_lines,
        f"- Meta Ads decision: {meta_decision.get('decision') if isinstance(meta_decision, dict) else None}. {meta_decision.get('why') if isinstance(meta_decision, dict) else None}",
        f"- Published post review: {post_text}",
        "- Risks:",
        *risk_lines,
        f"- Recommended next action: {report.get('recommended_next_action')}",
        f"- Daily Revenue CMO questions: {question_text}",
        f"- Vanity metric rule: {report.get('vanity_metric_policy')}",
    ]
    return "\n".join(str(line) for line in lines if str(line).strip())


def _enforce_campaign_decision_section(brief: str, decision_context: DecisionContext) -> str:
    section = _campaign_decision_markdown(decision_context)
    if not section:
        return brief
    pattern = re.compile(r"(?ms)^#{2,3}\s+Campaign Decision:?.*?(?=^#{2,3}\s+|\Z)")
    if pattern.search(brief):
        return pattern.sub(section + "\n\n", brief, count=1).strip()
    insert_before = re.search(r"(?m)^#{2,3}\s+Website Intelligence", brief)
    if insert_before:
        index = insert_before.start()
        return (brief[:index].rstrip() + "\n\n" + section + "\n\n" + brief[index:].lstrip()).strip()
    return (brief.rstrip() + "\n\n" + section).strip()


def _campaign_decision_markdown(decision_context: DecisionContext) -> str:
    decision = decision_context.summary.get("campaign_decision", {})
    if not isinstance(decision, dict) or not decision:
        return ""
    budget = decision.get("budget_status", {})
    evidence = decision.get("evidence", {})
    rules_checked = decision.get("rules_checked", {})
    failed_rules = decision.get("failed_rules", [])
    answer = str(decision.get("campaign_run_answer") or "Campaign failed and automatic retry scheduled.")
    ceo_action = "Yes" if decision.get("requires_ceo_action") else "No"
    if isinstance(budget, dict):
        budget_text = (
            f"Daily limit ₪{budget.get('daily_budget_limit')}; "
            f"monthly limit ₪{budget.get('monthly_budget_limit')}; "
            f"reserved today ₪{budget.get('reserved_today')}; "
            f"committed today ₪{budget.get('committed_today')}; "
            f"spent today ₪{budget.get('spent_today')}; "
            f"spent month ₪{budget.get('spent_month')}; "
            f"remaining today ₪{budget.get('remaining_today')}; "
            f"remaining month ₪{budget.get('remaining_month')}; "
            f"allowed to launch: {budget.get('allowed_to_launch')}."
        )
    else:
        budget_text = "Internal budget ledger unavailable."
    launched = decision.get("state") in {"launched", "monitoring", "launch_approved"}
    if launched:
        evidence_text = (
            f"Meta Campaign ID: {evidence.get('meta_campaign_id')}; "
            f"Ad Set ID: {evidence.get('ad_set_id')}; "
            f"Ad ID: {evidence.get('ad_id')}; "
            f"Budget: {evidence.get('budget')}; "
            f"Start time: {evidence.get('start_time')}; "
            f"Linked Instagram post: {evidence.get('linked_instagram_post')}; "
            f"Tracked WhatsApp link: {evidence.get('tracked_whatsapp_link')}."
        )
    else:
        evidence_text = (
            f"Rules checked: {', '.join(rules_checked.keys()) or 'none'}; "
            f"Failed rules: {', '.join(str(rule) for rule in failed_rules) or 'none'}; "
            f"Next retry time: {decision.get('next_retry_at') or evidence.get('next_retry_time')}."
        )
    return "\n".join(
        [
            "### Campaign Decision:",
            f"- Decision: {answer}",
            f"- Reason: {decision.get('reason')}",
            f"- Budget: {budget_text}",
            f"- Status: {decision.get('state')}",
            f"- Next Automatic Action: {decision.get('next_automatic_action')}",
            f"- Retry Time: {decision.get('next_retry_at') or evidence.get('next_retry_time')}",
            f"- CEO Action Required: {ceo_action}",
            f"- Evidence: {evidence_text}",
        ]
    )


def validate_hebrew_brief_style(brief: str) -> None:
    found = [term for term in FORBIDDEN_TERMS if term in brief]
    if found:
        raise RuntimeError(f"Brief contains forbidden Hebrew style terms: {', '.join(found)}")


def validate_executive_decision_brief_style(brief: str) -> None:
    first_line = next((line.strip() for line in brief.splitlines() if line.strip()), "")
    cleaned_first_line = re.sub(r"^[#>*_\-\s]+", "", first_line).strip()
    if not cleaned_first_line.startswith(EXECUTIVE_DECISION_STARTS):
        raise RuntimeError(
            "English CEO brief must start with a business-health sentence, not an activity log."
        )

    lower_brief = brief.lower()
    forbidden = [
        phrase
        for phrase in EXECUTIVE_DECISION_FORBIDDEN_PHRASES
        if phrase.lower() in lower_brief
    ]
    if forbidden:
        raise RuntimeError(
            "English CEO brief contains forbidden activity/infrastructure language: "
            + ", ".join(forbidden)
        )

    bare_unavailable = [
        line.strip()
        for line in brief.splitlines()
        if line.strip().lower() in {"unavailable", "unavailable."}
    ]
    if bare_unavailable:
        raise RuntimeError(
            "English CEO brief contains bare unavailable rows. Explain why, impact, action, timing, and confidence."
        )

    missing = [
        marker
        for marker in EXECUTIVE_DECISION_REQUIRED_MARKERS
        if marker.lower() not in lower_brief
    ]
    if missing:
        raise RuntimeError(
            "English CEO brief is missing Executive Decision Brief sections: "
            + ", ".join(missing)
        )

    if not any(answer.lower() in lower_brief for answer in CAMPAIGN_AUTONOMY_ANSWERS):
        raise RuntimeError(
            "English CEO brief must answer campaign autonomy with launched, intentionally not launched, "
            "blocked with CEO action, or failed with automatic retry."
        )
