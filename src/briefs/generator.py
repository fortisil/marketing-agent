from __future__ import annotations

from datetime import datetime
from typing import Any

from openai import OpenAI

from src.config import Settings
from src.decisions.engine import DecisionContext


FORBIDDEN_TERMS = ("נגנבו", "WattsApp")


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
    decision_payload = decision_context.to_prompt_payload()
    language = (brief_language or company.get("brief_language") or "en").strip().lower()

    if language in {"en", "english"}:
        return f"""
Write a daily CEO brief in English for {company["name"]}.

This is not a generic report. It is an AI CMO brief for Rami that must help ChatBot2U make better growth decisions without overstating reality. Write like an operator, not a reporter.

Mandatory trust banner at the very top:
Data confidence:
- High: real data from connected source
- Medium: partial real data
- Low: no verified data / mock disabled

Use the `data_confidence`, `data_status`, `metric_sources`, `execution_reality`, `execution_queue`, `connector_execution`, `autonomous_work_completion_rate`, `revenue_influence_score`, `business_autonomy_index`, `workforce`, and `marketing_department` fields from the DailyReport as source of truth.

Hard rules:
- Never invent KPI numbers.
- If a metric has `source: unavailable` or `verified: false`, write "No verified data available yet" instead of a number.
- Clearly separate real data, mock data, unavailable data, completed execution, blocked execution, failed execution, and next automatic retry.
- Put `Autonomous Work Completion Rate` immediately after the trust banner. Show planned tasks, completed automatically, blocked, failed, and success rate.
- Include `Revenue Influence Score` after Autonomous Work Completion Rate. If funnel attribution is unavailable, say it is unavailable and name the missing verified connector.
- Include `Business Autonomy Index` after Revenue Influence Score. Show Planning, Execution, Learning, Revenue Influence, and Overall.
- Workforce queue internals belong in memory. Mention only completed work, blocked work, business impact, autonomous completion rate, revenue influence, and business autonomy index.
- The Executive Layer is frozen except for bug fixes. New capability belongs in autonomous departments.
- The active department is Marketing Operations. The CEO brief must answer: "What did I accomplish for ChatBot2U while you were away?"
- Do not ask the CEO to fetch metrics. If Meta/WhatsApp sync is pending, describe it as an internal execution queue item with status and retry.
- Do not claim content was published, an ad was started, or outreach was sent unless the relevant department action has status `executed` and contains a real URL, post ID, campaign ID, or delivery record.
- Do not tell the CEO that something is "ready", "prepared", or "queued". Prepared tasks belong only in internal memory.
- Do not describe infrastructure to the CEO. Never write phrases like "publishing path exists", "connector runtime exists", or "execution path is implemented".
- Only report: Completed, Blocked, Failed, and Next automatic retry.
- Do not imply that a Meta campaign is active unless `campaign_status` is `active` and verified.
- If no verified campaign exists, say: "No campaign has been verified as active."
- If WhatsApp data is unavailable, say: "No verified WhatsApp event data available."
- Include: "To track WhatsApp leads, connect the WhatsApp bot event log/webhook."
- Use English headings and English body copy.
- The CEO brief to Rami must be English. Do not write Hebrew except for brand names, quoted terms, or phone/contact details.
- Use DailyReport as the source of truth. The email is only a Markdown view of the structured data.

Keep the CEO brief to one page. Include only:
1. Data confidence trust banner.
2. Autonomous Work Completion Rate.
3. Revenue Influence Score.
4. Business Autonomy Index.
5. Executive Summary.
6. What changed.
7. Today's initiative.
8. Completed execution.
9. Blocked or failed execution, with next automatic retry.
10. Decisions requiring escalation, if any.
11. Missing verified data only when it affects today's decision.

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
        "You are an AI CMO chief of staff. Write concise, professional English. "
        "Never invent metrics. If data is unavailable or unverified, say so clearly. "
        "Separate executed actions from recommended actions. Return only the CEO brief."
    )
    if str(brief_language).lower() in {"he", "hebrew", "עברית"}:
        system_content = (
            "You are an Israeli Hebrew-speaking CMO chief of staff. "
            "Write concise, professional business Hebrew. "
            "Always spell WhatsApp exactly as WhatsApp. "
            "Never use the Hebrew word נגנבו for leads or inquiries. "
            "Return only the CEO brief."
        )

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
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
        ],
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("OpenAI returned an empty brief.")

    normalized = normalize_brief_language(content.strip())
    validate_hebrew_brief_style(normalized)
    return normalized


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


def validate_hebrew_brief_style(brief: str) -> None:
    found = [term for term in FORBIDDEN_TERMS if term in brief]
    if found:
        raise RuntimeError(f"Brief contains forbidden Hebrew style terms: {', '.join(found)}")
