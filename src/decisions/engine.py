from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from src.execution.chief_of_staff import ChiefOfStaff
from src.providers.base import MetricSnapshot
from src.reports.daily import DailyReport, Initiative, Recommendation, Task


@dataclass(frozen=True)
class DecisionContext:
    run_date: str
    questions: list[str]
    snapshots: list[MetricSnapshot]
    summary: dict[str, Any]
    decisions: list[str]
    highest_roi_activity: str
    daily_report: DailyReport
    risks: list[str] = field(default_factory=list)

    def to_prompt_payload(self) -> dict[str, Any]:
        return {
            "run_date": self.run_date,
            "questions": self.questions,
            "summary": self.summary,
            "decisions": self.decisions,
            "highest_roi_activity": self.highest_roi_activity,
            "daily_report": self.daily_report.to_dict(),
            "risks": self.risks,
            "snapshots": [
                {
                    "provider": snapshot.provider,
                    "collected_at": snapshot.collected_at.isoformat(),
                    "metrics": snapshot.metrics,
                    "notes": snapshot.notes,
                }
                for snapshot in self.snapshots
            ],
        }


class DecisionEngine:
    questions = [
        "What happened yesterday?",
        "Why?",
        "What should we change?",
        "What is today's highest ROI activity?",
        "What is the highest-impact action I can take today to help ChatBot2U acquire another paying customer?",
    ]

    def __init__(
        self,
        company_config: dict[str, Any],
        objectives_config: dict[str, Any],
        company_knowledge: str,
        timezone: str,
    ) -> None:
        self.company_config = company_config
        self.objectives_config = objectives_config
        self.company_knowledge = company_knowledge
        self.timezone = timezone

    def evaluate(self, snapshots: list[MetricSnapshot]) -> DecisionContext:
        metrics = self._merge_metrics(snapshots)
        marketing = self.company_config["marketing"]
        budget_rule = marketing["budget_rule"]
        primary_kpi = marketing["primary_kpi"]
        now = datetime.now(ZoneInfo(self.timezone))
        run_date = now.date().isoformat()
        company_state = str(self.objectives_config.get("company_state", "Validation"))
        delegated_authority = self._delegated_authority()
        website_intelligence = metrics.get("website_intelligence", {})
        brand_intelligence = metrics.get("brand_intelligence", {})
        marketing_platform = metrics.get("marketing_platform", {})
        meta_ads = metrics.get("meta_ads", {})
        whatsapp_bot = metrics.get("whatsapp_bot", {})

        booked_demos_observed = self._verified_whatsapp_int(whatsapp_bot, "demo_bookings")
        qualified_leads_observed = self._verified_whatsapp_int(whatsapp_bot, "qualified_leads")
        booked_demos = (
            booked_demos_observed
            if booked_demos_observed is not None
            else int(metrics.get("booked_demos", 0) or 0)
        )
        target_booked_demos = int(metrics.get("target_booked_demos", 0) or 0)
        qualified_leads = (
            qualified_leads_observed
            if qualified_leads_observed is not None
            else int(metrics.get("qualified_leads", 0) or 0)
        )
        whatsapp_clicks = int(metrics.get("whatsapp_clicks", 0) or 0)
        spend = float(metrics.get("estimated_spend_ils", 0.0))
        real_spend_today = self._real_spend_today(meta_ads)
        budget_spend = real_spend_today if real_spend_today is not None else spend

        budget_decision = self._budget_decision(now, budget_spend, float(budget_rule["amount_ils_per_day"]))
        objective_status = self._objective_status(booked_demos_observed, budget_spend)

        decisions = [
            f"Keep the primary KPI focused on {primary_kpi}.",
            budget_decision,
            "Use WhatsApp as the primary CTA for every recommended action.",
            (
                "Never wait for work: if no obvious growth task exists, proactively review the website, "
                "repository, marketing, competitors, SEO, sales funnel, WhatsApp conversations, hypotheses, "
                "and experiments."
            ),
            self._delegated_authority_decision(delegated_authority),
            self._state_decision(company_state),
        ]
        risks: list[str] = []

        if target_booked_demos and booked_demos < target_booked_demos:
            decisions.append("Prioritize conversion from qualified leads to booked demos.")
            risks.append("Booked demos are below target.")

        if qualified_leads and whatsapp_clicks:
            decisions.append("Review WhatsApp conversation quality before increasing media spend.")

        website_risks = website_intelligence.get("website_risks", [])
        if website_risks:
            decisions.append("Use website intelligence to remove conversion friction before scaling acquisition.")
            risks.extend(str(risk) for risk in website_risks[:3])

        brand_decisions, brand_risks = self._brand_decisions(brand_intelligence)
        decisions.extend(brand_decisions)
        risks.extend(brand_risks)

        meta_decisions, meta_risks = self._marketing_platform_decisions(
            marketing_platform,
            meta_ads,
            budget_decision,
        )
        decisions.extend(meta_decisions)
        risks.extend(meta_risks)
        whatsapp_decisions, whatsapp_risks = self._whatsapp_decisions(whatsapp_bot)
        decisions.extend(whatsapp_decisions)
        risks.extend(whatsapp_risks)

        mission = str(self.objectives_config.get("mission_template", "Generate one qualified demo booking."))
        recommendations = self._recommendations(
            run_date=run_date,
            company_state=company_state,
            budget_decision=budget_decision,
            booked_demos=booked_demos,
            target_booked_demos=target_booked_demos,
            website_intelligence=website_intelligence,
            brand_intelligence=brand_intelligence,
            marketing_platform=marketing_platform,
            meta_ads=meta_ads,
            whatsapp_bot=whatsapp_bot,
        )
        highest_roi_activity = (
            recommendations[0].title
            if recommendations
            else "Follow up manually with qualified WhatsApp leads and convert them into booked demos."
        )
        initiatives = self._initiatives(recommendations, whatsapp_bot, website_intelligence)
        tasks = self._tasks_from_recommendations(recommendations, initiatives, run_date)
        chief_of_staff_plan = ChiefOfStaff(delegated_authority).plan(tasks)
        okr_status = self._okr_status(metrics)
        board_advisors = self._board_advisors(metrics, okr_status)
        judgment_scorecard = self._judgment_scorecard()
        prediction = self._prediction(now, highest_roi_activity, whatsapp_bot, budget_decision)
        prediction_evaluation = self._prediction_evaluation(prediction)
        red_team_challenge = self._red_team_challenge(now, recommendations, metrics)
        success_90_day_status = self._success_90_day_status(metrics)
        confidence = {
            "overall": round(
                sum(recommendation.confidence for recommendation in recommendations)
                / max(len(recommendations), 1),
                2,
            ),
            "metrics_quality": 0.45,
            "decision_quality": 0.76 if company_state == "Validation" else 0.7,
        }
        data_confidence = self._data_confidence(whatsapp_bot, meta_ads)
        metric_sources = self._metric_sources(
            booked_demos_observed=booked_demos_observed,
            qualified_leads_observed=qualified_leads_observed,
            whatsapp_bot=whatsapp_bot,
            meta_ads=meta_ads,
        )
        execution_reality = self._execution_reality(recommendations, chief_of_staff_plan.autonomous_action_log)
        summary = {
            "data_confidence": data_confidence,
            "primary_kpi": primary_kpi,
            "booked_demos": booked_demos_observed,
            "target_booked_demos": target_booked_demos,
            "qualified_leads": qualified_leads_observed,
            "whatsapp_clicks": whatsapp_clicks if "whatsapp_clicks" in metrics else None,
            "estimated_spend_ils": spend,
            "real_meta_spend_today_ils": real_spend_today,
            "metric_sources": metric_sources,
            "data_status": self._data_status(whatsapp_bot, meta_ads),
            "execution_reality": execution_reality,
            "executed_actions_today": execution_reality["executed_actions_today"],
            "prepared_actions": execution_reality["prepared_actions"],
            "recommended_actions": execution_reality["recommended_actions"],
            "budget_rule": budget_rule,
            "budget_decision": budget_decision,
            "company_state": company_state,
            "objectives": self.objectives_config,
            "delegated_authority": delegated_authority,
            "weekly_board_meeting": self.objectives_config.get("weekly_board_meeting", {}),
            "marketing_platform": marketing_platform,
            "website_intelligence": website_intelligence,
            "brand_intelligence": brand_intelligence,
            "meta_ads": meta_ads,
            "whatsapp_bot": whatsapp_bot,
            "judgment_scorecard": judgment_scorecard,
            "prediction": prediction,
            "prediction_evaluation": prediction_evaluation,
            "red_team_challenge": red_team_challenge,
            "success_90_day_status": success_90_day_status,
        }
        daily_report = DailyReport(
            company=self.company_config["company"]["name"],
            company_state=company_state,
            date=run_date,
            mission=mission,
            metrics=summary,
            objective_status=objective_status,
            decisions=decisions,
            initiatives=initiatives,
            recommendations=recommendations,
            tasks=tasks,
            chief_of_staff_plan=chief_of_staff_plan.to_dict(),
            autonomous_action_log=chief_of_staff_plan.autonomous_action_log,
            okr_status=okr_status,
            board_advisors=board_advisors,
            judgment_scorecard=judgment_scorecard,
            prediction=prediction,
            prediction_evaluation=prediction_evaluation,
            red_team_challenge=red_team_challenge,
            success_90_day_status=success_90_day_status,
            confidence=confidence,
            risks=risks,
            next_review=f"{run_date} 18:00 {self.timezone}",
            knowledge_summary=self._knowledge_summary(),
        )

        return DecisionContext(
            run_date=run_date,
            questions=self.questions,
            snapshots=snapshots,
            summary=summary,
            decisions=decisions,
            highest_roi_activity=highest_roi_activity,
            daily_report=daily_report,
            risks=risks,
        )

    def _merge_metrics(self, snapshots: list[MetricSnapshot]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for snapshot in snapshots:
            merged.update(snapshot.metrics)
        return merged

    def _verified_whatsapp_int(self, whatsapp_bot: dict[str, Any], key: str) -> int | None:
        if not isinstance(whatsapp_bot, dict):
            return None
        if not whatsapp_bot.get("available") or not whatsapp_bot.get("verified"):
            return None
        today = whatsapp_bot.get("today", {})
        if not isinstance(today, dict):
            return None
        value = today.get(key)
        if value is None and key == "demo_bookings":
            value = today.get("demos_booked")
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _data_confidence(self, whatsapp_bot: dict[str, Any], meta_ads: dict[str, Any]) -> dict[str, Any]:
        verified_sources = [
            bool(isinstance(whatsapp_bot, dict) and whatsapp_bot.get("available") and whatsapp_bot.get("verified")),
            bool(isinstance(meta_ads, dict) and meta_ads.get("available") and meta_ads.get("verified")),
        ]
        verified_count = sum(1 for source in verified_sources if source)
        if verified_count == len(verified_sources):
            level = "High"
        elif verified_count:
            level = "Medium"
        else:
            level = "Low"
        return {
            "level": level,
            "definition": {
                "High": "real data from connected source",
                "Medium": "partial real data",
                "Low": "no verified data / mock disabled",
            },
            "reason": (
                "No verified data available yet."
                if level == "Low"
                else "At least one connected source returned verified data."
            ),
        }

    def _metric_sources(
        self,
        *,
        booked_demos_observed: int | None,
        qualified_leads_observed: int | None,
        whatsapp_bot: dict[str, Any],
        meta_ads: dict[str, Any],
    ) -> list[dict[str, Any]]:
        sources = [
            {
                "metric": "booked_demos",
                "value": booked_demos_observed,
                "source": "whatsapp_bot" if booked_demos_observed is not None else "unavailable",
                "verified": booked_demos_observed is not None,
            },
            {
                "metric": "qualified_leads",
                "value": qualified_leads_observed,
                "source": "whatsapp_bot" if qualified_leads_observed is not None else "unavailable",
                "verified": qualified_leads_observed is not None,
            },
        ]
        for payload in (whatsapp_bot, meta_ads):
            if isinstance(payload, dict):
                sources.extend(payload.get("metric_sources", []))
        return sources

    def _data_status(self, whatsapp_bot: dict[str, Any], meta_ads: dict[str, Any]) -> dict[str, Any]:
        whatsapp_available = bool(isinstance(whatsapp_bot, dict) and whatsapp_bot.get("available"))
        meta_available = bool(isinstance(meta_ads, dict) and meta_ads.get("available"))
        return {
            "whatsapp": {
                "status": "real_data" if whatsapp_available and whatsapp_bot.get("verified") else "unavailable",
                "message": (
                    "Verified WhatsApp event data connected."
                    if whatsapp_available and whatsapp_bot.get("verified")
                    else "No verified WhatsApp event data available."
                ),
            },
            "meta": {
                "status": "real_data" if meta_available and meta_ads.get("verified") else "unavailable",
                "message": (
                    "Verified Meta campaign data connected."
                    if meta_available and meta_ads.get("verified")
                    else "No verified Meta campaign data available."
                ),
                "campaign_status": (
                    meta_ads.get("campaign_status", "unknown")
                    if isinstance(meta_ads, dict)
                    else "unknown"
                ),
                "campaign_status_note": (
                    meta_ads.get("campaign_status_note", "No campaign has been verified as active.")
                    if isinstance(meta_ads, dict)
                    else "No campaign has been verified as active."
                ),
            },
        }

    def _execution_reality(
        self,
        recommendations: list[Recommendation],
        autonomous_action_log: list[dict[str, Any]],
    ) -> dict[str, Any]:
        executed = [
            str(item.get("task"))
            for item in autonomous_action_log
            if isinstance(item, dict) and item.get("status") == "executed"
        ]
        prepared = [
            str(item.get("task"))
            for item in autonomous_action_log
            if isinstance(item, dict) and item.get("status") in {"prepared", "drafted"}
        ]
        return {
            "executed_actions_today": executed or ["none"],
            "prepared_actions": prepared,
            "recommended_actions": [recommendation.title for recommendation in recommendations],
        }

    def _budget_decision(self, now: datetime, spend: float, daily_budget_ils: float) -> str:
        if now.weekday() == 5:
            return "Do not spend today because Saturday is a no-spend day."

        if now.weekday() == 4 and now.hour >= 13:
            return "Do not start or increase paid spend now because Friday paid spend stops after 13:00 Israel time."

        if spend >= daily_budget_ils:
            return "Do not increase spend because the daily ₪20 budget is already effectively used."

        return "Paid spend may continue only up to the ₪20 daily cap if demo-booking intent remains strong."

    def _objective_status(self, booked_demos: int | None, spend: float) -> dict[str, Any]:
        targets = self.objectives_config.get("targets", {})
        weekly_demo_target = int(targets.get("demos_per_week", 0))
        cac_max = float(targets.get("cac_ils_max", 0))
        projected_cac = round(spend / booked_demos, 2) if booked_demos else None

        return {
            "period": self.objectives_config.get("period"),
            "goal": self.objectives_config.get("goal", {}),
            "north_star_kpi": self.objectives_config.get("north_star_kpi"),
            "weekly_demo_target": weekly_demo_target,
            "booked_demos_observed": booked_demos,
            "on_track_for_demo_target": (
                booked_demos >= weekly_demo_target
                if booked_demos is not None and weekly_demo_target
                else None
            ),
            "cac_ils_max": cac_max,
            "projected_cac_ils": projected_cac,
            "cac_on_track": projected_cac <= cac_max if projected_cac is not None and cac_max else None,
        }

    def _state_decision(self, company_state: str) -> str:
        if company_state.lower() == "validation":
            return (
                "Because ChatBot2U is in Validation, prioritize customer interviews, demo bookings, "
                "and rapid iteration over scaling ad spend."
            )

        return f"Company state is {company_state}; keep recommendations aligned with that stage."

    def _delegated_authority(self) -> dict[str, Any]:
        return self.objectives_config.get("delegated_authority", {})

    def _delegated_authority_decision(self, delegated_authority: dict[str, Any]) -> str:
        autonomous = []
        limited = []
        for section, rules in delegated_authority.items():
            if not isinstance(rules, dict):
                continue
            for action, value in rules.items():
                path = f"{section}.{action}"
                if value == "always":
                    autonomous.append(path)
                elif value in {"never", "draft_only"}:
                    limited.append(f"{path}={value}")
        return (
            "The AI CMO operates under delegated authority, not continuous approval. "
            f"Autonomous authority={autonomous}; delegated limits={limited}. "
            "Execute when authorized, document every significant decision, and escalate only when a decision exceeds delegated limits."
        )

    def _okr_status(self, metrics: dict[str, Any]) -> dict[str, Any]:
        okrs = self.objectives_config.get("quarterly_okrs", {})
        key_results = okrs.get("key_results", {}) if isinstance(okrs, dict) else {}
        booked_demos = int(metrics.get("booked_demos", 0) or 0)
        qualified_leads = int(metrics.get("qualified_leads", 0) or 0)
        whatsapp_bot = metrics.get("whatsapp_bot", {})
        today = whatsapp_bot.get("today", {}) if isinstance(whatsapp_bot, dict) else {}
        customers = int(today.get("customers", 0) or 0)
        observed = {
            "paying_customers": customers,
            "demos": booked_demos,
            "qualified_leads": qualified_leads,
        }
        progress = {}
        for key, target in key_results.items():
            current = observed.get(key)
            if current is None:
                progress[key] = {"target": target, "observed": None, "status": "needs_data"}
                continue
            progress[key] = {
                "target": target,
                "observed": current,
                "progress": round(current / target, 4) if target else None,
                "status": "on_track" if target and current >= target else "behind_or_learning",
            }
        return {
            "objective": okrs.get("objective") if isinstance(okrs, dict) else "",
            "key_results": progress,
            "daily_question": (
                "What is the highest-impact action I can take today to help ChatBot2U acquire another paying customer?"
            ),
        }

    def _board_advisors(self, metrics: dict[str, Any], okr_status: dict[str, Any]) -> list[dict[str, Any]]:
        whatsapp_bot = metrics.get("whatsapp_bot", {})
        today = whatsapp_bot.get("today", {}) if isinstance(whatsapp_bot, dict) else {}
        bottleneck = str(today.get("bottleneck", whatsapp_bot.get("today_bottleneck", "unknown")))
        spend = float(metrics.get("estimated_spend_ils", 0.0) or 0.0)
        brand_intelligence = metrics.get("brand_intelligence", {})
        brand_source = brand_intelligence.get("source", "unknown") if isinstance(brand_intelligence, dict) else "unknown"
        design_status = (
            brand_intelligence.get("design_system_review", {}).get("status", "unknown")
            if isinstance(brand_intelligence, dict)
            else "unknown"
        )
        return [
            {
                "advisor": "Growth Advisor",
                "perspective": "Acquire more qualified law-firm leads and convert them into booked demos.",
                "argument": f"Focus on the current funnel bottleneck: {bottleneck}.",
                "recommendation": "Prioritize the action most likely to increase booked demos this week.",
            },
            {
                "advisor": "Product Advisor",
                "perspective": "Market only real product capabilities and strengthen differentiation.",
                "argument": f"Repository and website intelligence should anchor every claim; brand source is {brand_source}.",
                "recommendation": "Turn new or under-demonstrated capabilities into demos, posts, or website updates while following Brand Brain rules.",
            },
            {
                "advisor": "Design System Advisor",
                "perspective": "Protect ChatBot2U visual identity and prevent brand drift.",
                "argument": f"Design System Agent status: {design_status}.",
                "recommendation": "Reject or regenerate creative assets that do not follow logo, color, typography, CTA, or image-style rules.",
            },
            {
                "advisor": "Finance Advisor",
                "perspective": "Protect ROI and budget discipline.",
                "argument": f"Current observed spend is ₪{spend:.2f}; every shekel needs expected return.",
                "recommendation": "Promote only one asset when evidence supports it and stay inside delegated budget.",
            },
            {
                "advisor": "Customer Success Advisor",
                "perspective": "Protect trust, retention, and long-term customer relationships.",
                "argument": "Growth must not create false expectations or weak customer handoffs.",
                "recommendation": "Educate first, demonstrate second, sell third.",
            },
        ]

    def _judgment_scorecard(self) -> dict[str, Any]:
        configured = self.objectives_config.get("judgment_scorecard", {})
        dimensions = configured.get("dimensions") if isinstance(configured, dict) else None
        if not dimensions:
            dimensions = [
                {
                    "name": "Judgment",
                    "question": "Would I have made the same decision?",
                    "score_range": "1-10",
                },
                {
                    "name": "Business Impact",
                    "question": "Would acting on this likely increase customers?",
                    "score_range": "1-10",
                },
                {
                    "name": "Proactivity",
                    "question": "Did it find opportunities on its own?",
                    "score_range": "1-10",
                },
                {
                    "name": "Signal vs. Noise",
                    "question": "Was it concise and focused?",
                    "score_range": "1-10",
                },
                {
                    "name": "Learning",
                    "question": "Did it improve compared to yesterday?",
                    "score_range": "1-10",
                },
            ]
        return {
            "principle": "We are no longer building features. We are building judgment.",
            "cadence": "Score every daily brief after reading it as if it came from a human executive.",
            "dimensions": dimensions,
            "ceo_scores": {str(item.get("name")): None for item in dimensions if isinstance(item, dict)},
            "notes": "CEO scores are intentionally blank until Rami reviews the brief.",
        }

    def _prediction(
        self,
        now: datetime,
        highest_roi_activity: str,
        whatsapp_bot: dict[str, Any],
        budget_decision: str,
    ) -> dict[str, Any]:
        if not whatsapp_bot.get("available") or not whatsapp_bot.get("verified"):
            evaluation_days = int(
                self.objectives_config.get("prediction_policy", {}).get("evaluation_window_days", 7)
                if isinstance(self.objectives_config.get("prediction_policy", {}), dict)
                else 7
            )
            due_at = now + timedelta(days=evaluation_days)
            return {
                "hypothesis": (
                    f"Executing '{highest_roi_activity}' will produce one verified learning about "
                    "the fastest path to booked demos after WhatsApp and campaign tracking are connected."
                ),
                "action": highest_roi_activity,
                "primary_kpi": self.objectives_config.get("north_star_kpi", "booked demos"),
                "expected_outcome": {
                    "validated_learning": ">=1",
                    "verified_whatsapp_data": "required",
                    "verified_campaign_data": "required",
                    "timeframe_days": evaluation_days,
                },
                "baseline": {
                    "conversations_today": None,
                    "qualified_leads_today": None,
                    "booked_demos_today": None,
                    "bottleneck": "unknown",
                },
                "confidence": 0.52,
                "created_at": now.isoformat(),
                "evaluate_after_days": evaluation_days,
                "evaluation_due_date": due_at.date().isoformat(),
                "calibration_questions": [
                    "Was the recommendation useful without verified data?",
                    "Which data integration changed the decision quality most?",
                    "What should change next time?",
                ],
            }
        today = whatsapp_bot.get("today", {}) if isinstance(whatsapp_bot, dict) else {}
        conversations = int(today.get("conversations", 0) or 0)
        qualified = int(today.get("qualified_leads", 0) or 0)
        demos_booked = int(today.get("demo_bookings", today.get("demos_booked", 0)) or 0)
        bottleneck = str(today.get("bottleneck", whatsapp_bot.get("today_bottleneck", "unknown")))
        evaluation_days = int(
            self.objectives_config.get("prediction_policy", {}).get("evaluation_window_days", 7)
            if isinstance(self.objectives_config.get("prediction_policy", {}), dict)
            else 7
        )
        budget_phrase = "without new paid spend"
        if "Do not" not in budget_decision:
            budget_phrase = "with up to ₪20/day inside delegated authority"

        if bottleneck == "low_conversation_volume" or conversations < 5:
            expected_outcome = {
                "qualified_whatsapp_conversations": "3-5",
                "booked_demos": ">=1",
                "timeframe_days": 5,
            }
            hypothesis = (
                f"Executing '{highest_roi_activity}' {budget_phrase} will create 3-5 qualified "
                "WhatsApp conversations and at least 1 booked demo within 5 days."
            )
        elif bottleneck in {"qualification", "demo_scheduling"} or qualified > demos_booked:
            expected_outcome = {
                "demo_booking_rate_change": "+15%",
                "booked_demos": ">=1",
                "timeframe_days": 7,
            }
            hypothesis = (
                f"Executing '{highest_roi_activity}' will improve the WhatsApp qualification-to-demo "
                "path and produce at least 1 additional booked demo within 7 days."
            )
        else:
            expected_outcome = {
                "validated_learning": ">=1",
                "booked_demos": "maintain_or_increase",
                "timeframe_days": 7,
            }
            hypothesis = (
                f"Executing '{highest_roi_activity}' will produce at least one measurable learning "
                "about the fastest path from content or WhatsApp to booked demos within 7 days."
            )

        due_at = now + timedelta(days=evaluation_days)
        return {
            "hypothesis": hypothesis,
            "action": highest_roi_activity,
            "primary_kpi": self.objectives_config.get("north_star_kpi", "booked demos"),
            "expected_outcome": expected_outcome,
            "baseline": {
                "conversations_today": conversations,
                "qualified_leads_today": qualified,
                "booked_demos_today": demos_booked,
                "bottleneck": bottleneck,
            },
            "confidence": 0.74,
            "created_at": now.isoformat(),
            "evaluate_after_days": evaluation_days,
            "evaluation_due_date": due_at.date().isoformat(),
            "calibration_questions": [
                "Was the prediction accurate?",
                "Why or why not?",
                "What should change next time?",
            ],
        }

    def _prediction_evaluation(self, prediction: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "pending",
            "prediction_created_at": prediction.get("created_at"),
            "evaluation_due_date": prediction.get("evaluation_due_date"),
            "criteria": prediction.get("expected_outcome", {}),
            "questions": prediction.get("calibration_questions", []),
            "note": "Evaluate this prediction against actual WhatsApp, demo, customer, and campaign metrics when the window closes.",
        }

    def _red_team_challenge(
        self,
        now: datetime,
        recommendations: list[Recommendation],
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        policy = self.objectives_config.get("red_team", {})
        cadence = str(policy.get("cadence", "Friday")) if isinstance(policy, dict) else "Friday"
        is_friday = now.weekday() == 4
        top_recommendation = recommendations[0].title if recommendations else "Run autonomous growth opportunity scan"
        website_intelligence = metrics.get("website_intelligence", {})
        content_ideas = (
            website_intelligence.get("content_ideas", [])
            if isinstance(website_intelligence, dict)
            else []
        )
        alternative = str(content_ideas[0]) if content_ideas else "a practical carousel or website CTA experiment"
        return {
            "cadence": cadence,
            "active_today": is_friday,
            "assumption_to_challenge": f"The current highest-ROI action is '{top_recommendation}'.",
            "challenge_question": (
                f"What evidence suggests {alternative} could outperform this recommendation for booked demos?"
            ),
            "required_response": (
                "Record one counter-hypothesis and decide whether it changes today's priority."
                if is_friday
                else "Run this challenge on Friday unless a major strategic decision appears earlier."
            ),
        }

    def _success_90_day_status(self, metrics: dict[str, Any]) -> dict[str, Any]:
        goals = self.objectives_config.get("success_90_days", {})
        whatsapp_bot = metrics.get("whatsapp_bot", {})
        today = whatsapp_bot.get("today", {}) if isinstance(whatsapp_bot, dict) else {}
        demos_booked = (
            self._verified_whatsapp_int(whatsapp_bot, "demo_bookings")
            if isinstance(whatsapp_bot, dict)
            else None
        )
        customers = int(today.get("customers", 0) or 0)
        qualified = (
            self._verified_whatsapp_int(whatsapp_bot, "qualified_leads")
            if isinstance(whatsapp_bot, dict)
            else None
        )
        return {
            "definition": goals,
            "current_signals": {
                "qualified_leads_today": qualified,
                "booked_demos_today": demos_booked,
                "customers_today": customers if whatsapp_bot.get("available") and whatsapp_bot.get("verified") else None,
            },
            "status": (
                "needs_verified_data"
                if demos_booked is None and qualified is None
                else "learning" if demos_booked == 0 and customers == 0 else "evidence_building"
            ),
            "business_trend_goal": self.objectives_config.get("demo_booking_growth_trend", {}),
            "governance": self.objectives_config.get("governance", {}),
        }

    def _recommendations(
        self,
        run_date: str,
        company_state: str,
        budget_decision: str,
        booked_demos: int,
        target_booked_demos: int,
        website_intelligence: dict[str, Any],
        brand_intelligence: dict[str, Any],
        marketing_platform: dict[str, Any],
        meta_ads: dict[str, Any],
        whatsapp_bot: dict[str, Any],
    ) -> list[Recommendation]:
        recommendations = [
            Recommendation(
                title="Connect verified WhatsApp lead tracking",
                reason=(
                    "No verified WhatsApp lead or demo data is available yet, so the first growth task is measurement integrity."
                    if not whatsapp_bot.get("available") or not whatsapp_bot.get("verified")
                    else (
                        "The North Star KPI is booked demos, and the current demo count is below target."
                        if target_booked_demos and booked_demos < target_booked_demos
                        else "Booked demos remain the strongest proof of business value."
                    )
                ),
                estimated_impact="High",
                confidence=0.84,
            ),
            Recommendation(
                title="Review WhatsApp conversation drop-offs before changing spend",
                reason="In Validation, conversion learning is more valuable than pushing more traffic.",
                estimated_impact="Medium",
                confidence=0.78,
            ),
            Recommendation(
                title="Draft one founder-led demonstration post",
                reason="The knowledge base says Hebrew founder-led messaging is a useful trust signal.",
                estimated_impact="Medium",
                confidence=0.72,
            ),
        ]

        if "Do not" in budget_decision:
            recommendations.append(
                Recommendation(
                    title="Hold paid media changes until the next eligible spend window",
                    reason=budget_decision,
                    estimated_impact="Medium",
                    confidence=0.91,
                )
            )

        opportunities = website_intelligence.get("marketing_opportunities", [])
        if opportunities:
            recommendations.append(
                Recommendation(
                    title="Improve website conversion path for booked demos",
                    reason=str(opportunities[0]),
                    estimated_impact="Medium",
                    confidence=0.74,
                )
            )

        missing_ctas = website_intelligence.get("missing_or_weak_ctas", [])
        if missing_ctas:
            recommendations.append(
                Recommendation(
                    title="Strengthen website CTA toward WhatsApp demo booking",
                    reason=str(missing_ctas[0]),
                    estimated_impact="High",
                    confidence=0.81,
                )
            )

        design_review = brand_intelligence.get("design_system_review", {})
        if design_review.get("status") != "approved":
            recommendations.append(
                Recommendation(
                    title="Complete Brand Library before autonomous creative production",
                    reason=str(
                        design_review.get(
                            "reason",
                            "Brand Brain needs official assets before creative execution.",
                        )
                    ),
                    estimated_impact="High",
                    confidence=0.9,
                )
            )

        if marketing_platform.get("mcp", {}).get("requires_external_mcp_execution") and not marketing_platform.get(
            "metrics_available"
        ):
            recommendations.append(
                Recommendation(
                    title="Fetch live Meta metrics through ChatGPT/Meta MCP",
                    reason="Meta MCP is the preferred execution layer, but this local AI CMO run cannot invoke MCP tools directly.",
                    estimated_impact="High",
                    confidence=0.86,
                )
            )
        elif not meta_ads.get("available"):
            recommendations.append(
                Recommendation(
                    title="Connect Meta Ads credentials before making spend decisions",
                    reason=str(meta_ads.get("reason", "Real Meta metrics are unavailable.")),
                    estimated_impact="Medium",
                    confidence=0.7,
                )
            )
        elif self._has_no_campaigns(meta_ads):
            recommendations.append(
                Recommendation(
                    title="Create first Meta campaign within delegated budget limits",
                    reason="No real campaign exists yet, so the next step is preparation within delegated authority and the ₪20/day cap.",
                    estimated_impact="Medium",
                    confidence=0.82,
                )
            )

        recommendations.extend(self._whatsapp_recommendations(whatsapp_bot))

        if company_state.lower() != "validation":
            recommendations.append(
                Recommendation(
                    title=f"Review whether tasks still fit the {company_state} stage",
                    reason="State changes should alter the operating cadence and risk tolerance.",
                    estimated_impact="Medium",
                    confidence=0.66,
                )
            )

        return recommendations

    def _initiatives(
        self,
        recommendations: list[Recommendation],
        whatsapp_bot: dict[str, Any],
        website_intelligence: dict[str, Any],
    ) -> list[Initiative]:
        recommendation_titles = [recommendation.title for recommendation in recommendations]
        today = whatsapp_bot.get("today", {}) if isinstance(whatsapp_bot, dict) else {}
        bottleneck = str(today.get("bottleneck", whatsapp_bot.get("today_bottleneck", "")))
        website_tasks = [
            title
            for title in recommendation_titles
            if "website" in title.lower() or "cta" in title.lower()
        ]
        return [
            Initiative(
                title="Increase demo bookings",
                objective="Move qualified law-firm demand into booked demos and paying customers.",
                kpi="booked_demos",
                expected_business_impact="High",
                confidence=0.88,
                tasks=[
                    title
                    for title in recommendation_titles
                    if "WhatsApp" in title or "demo" in title.lower() or "lead" in title.lower()
                ],
            ),
            Initiative(
                title="Improve acquisition conversion system",
                objective="Reduce friction from website, content, ads, and WhatsApp into the sales funnel.",
                kpi="qualified_leads",
                expected_business_impact="High" if bottleneck else "Medium",
                confidence=0.8,
                tasks=website_tasks
                or [
                    str(item)
                    for item in website_intelligence.get("marketing_opportunities", [])[:2]
                ],
            ),
            Initiative(
                title="Build learning loop for repeatable growth",
                objective="Turn recommendations into experiments and compare expected impact with outcomes.",
                kpi="paying_customers",
                expected_business_impact="Medium",
                confidence=0.74,
                tasks=["Log experiment hypothesis, execution, result, business impact, and learning."],
            ),
        ]

    def _tasks_from_recommendations(
        self,
        recommendations: list[Recommendation],
        initiatives: list[Initiative],
        due_date: str,
    ) -> list[Task]:
        tasks: list[Task] = []

        if not recommendations:
            return [
                Task(
                    title="Run autonomous growth opportunity scan",
                    priority="High",
                    due_date=due_date,
                    estimated_impact="Medium",
                    confidence=0.7,
                    dependencies=[
                        "Website intelligence",
                        "Repository intelligence",
                        "Marketing metrics",
                        "WhatsApp funnel metrics",
                    ],
                    reason=(
                        "The AI CMO should never wait for work. When no obvious task exists, review the "
                        "website, repository, marketing, competitors, SEO opportunities, sales funnel, "
                        "WhatsApp conversations, hypotheses, and experiments."
                    ),
                    initiative="Build learning loop for repeatable growth",
                    authority_policy="marketing.create_post_drafts",
                    expected_outcome="One new qualified growth hypothesis or experiment ready to execute.",
                )
            ]

        for recommendation in recommendations:
            priority = "High" if recommendation.estimated_impact == "High" else "Medium"
            dependencies = ["WhatsApp conversation data"] if "WhatsApp" in recommendation.title else []
            initiative_title = self._initiative_for_recommendation(recommendation, initiatives)
            tasks.append(
                Task(
                    title=recommendation.title,
                    priority=priority,
                    due_date=due_date,
                    estimated_impact=recommendation.estimated_impact,
                    confidence=recommendation.confidence,
                    dependencies=dependencies,
                    reason=recommendation.reason,
                    initiative=initiative_title,
                    authority_policy="delegated_authority",
                    expected_outcome=self._expected_outcome_for_recommendation(recommendation),
                )
            )

        return tasks

    def _initiative_for_recommendation(
        self,
        recommendation: Recommendation,
        initiatives: list[Initiative],
    ) -> str:
        title = recommendation.title.lower()
        if "website" in title or "cta" in title or "meta" in title or "campaign" in title:
            return "Improve acquisition conversion system"
        if "experiment" in title or "review" in title:
            return "Build learning loop for repeatable growth"
        return initiatives[0].title if initiatives else "Increase demo bookings"

    def _expected_outcome_for_recommendation(self, recommendation: Recommendation) -> str:
        if recommendation.estimated_impact == "High":
            return "Increase probability of booked demos or paying customers this week."
        return "Create measurable learning that improves future conversion decisions."

    def _knowledge_summary(self) -> str:
        compact = " ".join(self.company_knowledge.split())
        return compact[:800]

    def _real_spend_today(self, meta_ads: dict[str, Any]) -> float | None:
        if not meta_ads.get("available"):
            return None
        today = meta_ads.get("today", {})
        if not isinstance(today, dict) or today.get("spend") is None:
            return None
        try:
            return float(today["spend"])
        except (TypeError, ValueError):
            return None

    def _brand_decisions(self, brand_intelligence: dict[str, Any]) -> tuple[list[str], list[str]]:
        if not brand_intelligence.get("available"):
            return [
                "Brand Brain is unavailable; use website repository inference only as a temporary fallback."
            ], [
                "Autonomous creative generation risks brand drift until the Brand Library is available."
            ]

        review = brand_intelligence.get("design_system_review", {})
        decisions = [
            "Use Brand Brain as the source of truth for logos, colors, typography, design rules, and asset library paths."
        ]
        risks: list[str] = []
        if review.get("status") != "approved":
            decisions.append("Design System Agent requires brand completion before autonomous publishing.")
            risks.append(str(review.get("reason", "Brand Library is incomplete.")))
        missing_assets = brand_intelligence.get("missing_assets", [])
        if missing_assets:
            risks.append(f"Brand asset library has missing or empty sections: {', '.join(missing_assets[:5])}.")
        return decisions, risks

    def _marketing_platform_decisions(
        self,
        marketing_platform: dict[str, Any],
        meta_ads: dict[str, Any],
        budget_decision: str,
    ) -> tuple[list[str], list[str]]:
        decisions: list[str] = []
        risks: list[str] = []

        mcp_payload = marketing_platform.get("mcp", {})
        if mcp_payload.get("requires_external_mcp_execution") and not marketing_platform.get("metrics_available"):
            decisions.append(
                "No verified Meta campaign data available. Meta MCP is the preferred execution layer, but this local AI CMO run cannot invoke MCP tools directly. Use ChatGPT/Meta MCP to fetch live metrics or configure Graph API credentials."
            )
            actions = marketing_platform.get("mcp_required_actions", [])
            if actions:
                decisions.append(f"Next Meta MCP actions needed: {'; '.join(str(action) for action in actions)}")
            risks.append("No campaign has been verified as active.")
            return decisions, risks

        if not meta_ads.get("available"):
            reason = meta_ads.get("reason", "Real Meta metrics are unavailable.")
            decisions.append(f"No verified Meta campaign data available: {reason}")
            risks.append("No campaign has been verified as active.")
            return decisions, risks

        campaigns_summary = meta_ads.get("campaigns_summary", {})
        active_campaigns = campaigns_summary.get("active", [])
        paused_campaigns = campaigns_summary.get("paused", [])
        total_campaigns = int(campaigns_summary.get("total", 0) or 0)

        if total_campaigns == 0:
            decisions.append("No real Meta campaign exists; create the first campaign within delegated authority and keep spend inside the ₪20/day cap.")
            return decisions, risks

        if active_campaigns and "Do not" in budget_decision:
            decisions.append("Review active Meta campaigns because today's budget rule blocks new paid spend.")

        if paused_campaigns and not active_campaigns:
            decisions.append("Meta campaigns exist but are paused; review them before approving any spend.")

        delivery_errors = meta_ads.get("delivery_errors", [])
        if delivery_errors:
            decisions.append("Fix Meta delivery errors before approving paid spend.")
            risks.extend(str(error) for error in delivery_errors[:3])

        instagram = meta_ads.get("instagram", {})
        if not instagram.get("available"):
            decisions.append(
                f"Instagram metrics are unavailable: {instagram.get('reason', 'permissions or IG account missing.')}"
            )

        return decisions, risks

    def _has_no_campaigns(self, meta_ads: dict[str, Any]) -> bool:
        if not meta_ads.get("available"):
            return False
        campaigns_summary = meta_ads.get("campaigns_summary", {})
        return int(campaigns_summary.get("total", 0) or 0) == 0

    def _whatsapp_decisions(self, whatsapp_bot: dict[str, Any]) -> tuple[list[str], list[str]]:
        if not whatsapp_bot.get("available"):
            reason = whatsapp_bot.get("reason", "WhatsApp bot funnel metrics are unavailable.")
            return [f"WhatsApp bot funnel metrics are unavailable: {reason}"], [
                "Primary KPI decisions are limited because WhatsApp bot funnel metrics are unavailable."
            ]
        if not whatsapp_bot.get("verified"):
            reason = whatsapp_bot.get("reason", "WhatsApp bot funnel metrics are not verified.")
            return [f"WhatsApp bot funnel metrics are not verified: {reason}"], [
                "Do not use mock WhatsApp metrics for production KPI decisions."
            ]

        today = whatsapp_bot.get("today", {})
        conversations = int(today.get("conversations", 0) or 0)
        qualified = int(today.get("qualified_leads", 0) or 0)
        demos_booked = int(today.get("demo_bookings", today.get("demos_booked", 0)) or 0)
        customers = int(today.get("customers", 0) or 0)
        health_score = int(today.get("funnel_health_score", whatsapp_bot.get("funnel_health_score", 0)) or 0)
        bottleneck = str(today.get("bottleneck", whatsapp_bot.get("today_bottleneck", "")))
        rates = today.get("conversion_rates", {})

        decisions: list[str] = [
            (
                "Use WhatsApp bot funnel metrics as the primary conversion signal: "
                f"{conversations} conversations, {qualified} qualified leads, "
                f"{demos_booked} demos booked, {customers} customers today."
            ),
            f"Funnel Health Score is {health_score}/100; today's bottleneck is {bottleneck}.",
        ]
        risks: list[str] = []

        if bottleneck == "low_conversation_volume":
            decisions.append("Few WhatsApp conversations today; improve Instagram and ads CTA into WhatsApp.")
            risks.append("Low WhatsApp conversation volume may limit demo bookings.")
        elif bottleneck == "qualification" or rates.get("conversation_to_qualified", 0.0) < 0.3:
            decisions.append("Many WhatsApp conversations but few qualified leads; improve opening questions.")
            risks.append("WhatsApp qualification rate is weak.")
        elif bottleneck == "demo_scheduling" or (
            qualified >= 3 and rates.get("qualified_to_demo", rates.get("qualified_to_demo_booked", 0.0)) < 0.4
        ):
            decisions.append("Many qualified WhatsApp leads but few demos booked; improve scheduling CTA.")
            risks.append("Qualified leads are not converting into demo bookings.")
        elif bottleneck == "demo_to_customer":
            decisions.append("Demos are happening but customers are low; review demo quality and follow-up.")
            risks.append("Demo-to-customer conversion is the current funnel risk.")

        return decisions, risks

    def _whatsapp_recommendations(self, whatsapp_bot: dict[str, Any]) -> list[Recommendation]:
        if not whatsapp_bot.get("available"):
            return [
                Recommendation(
                    title="Connect WhatsApp bot event log",
                    reason=str(whatsapp_bot.get("reason", "WhatsApp bot funnel metrics are unavailable.")),
                    estimated_impact="High",
                    confidence=0.84,
                )
            ]
        if not whatsapp_bot.get("verified"):
            return [
                Recommendation(
                    title="Connect WhatsApp bot event log",
                    reason="No verified WhatsApp event data available. To track WhatsApp leads, connect the WhatsApp bot event log/webhook.",
                    estimated_impact="High",
                    confidence=0.84,
                )
            ]

        today = whatsapp_bot.get("today", {})
        conversations = int(today.get("conversations", 0) or 0)
        qualified = int(today.get("qualified_leads", 0) or 0)
        demos_booked = int(today.get("demo_bookings", today.get("demos_booked", 0)) or 0)
        customers = int(today.get("customers", 0) or 0)
        health_score = int(today.get("funnel_health_score", whatsapp_bot.get("funnel_health_score", 0)) or 0)
        bottleneck = str(today.get("bottleneck", whatsapp_bot.get("today_bottleneck", "")))
        rates = today.get("conversion_rates", {})

        if bottleneck == "low_conversation_volume" or conversations < 5:
            return [
                Recommendation(
                    title="Increase WhatsApp conversation volume",
                    reason=(
                        "Few conversations entered the bot today, so the CTA from Instagram, ads, "
                        f"and website needs more focus. Funnel Health Score: {health_score}/100."
                    ),
                    estimated_impact="High",
                    confidence=0.86,
                )
            ]

        if bottleneck == "qualification" or rates.get("conversation_to_qualified", 0.0) < 0.3:
            return [
                Recommendation(
                    title="Improve WhatsApp opening questions",
                    reason=(
                        "Many conversations are not becoming qualified leads. "
                        f"Current conversation-to-qualified rate: {rates.get('conversation_to_qualified', 0.0):.0%}."
                    ),
                    estimated_impact="High",
                    confidence=0.87,
                )
            ]

        if bottleneck == "demo_scheduling" or (
            qualified >= 3 and rates.get("qualified_to_demo", rates.get("qualified_to_demo_booked", 0.0)) < 0.4
        ):
            return [
                Recommendation(
                    title="Improve WhatsApp scheduling CTA",
                    reason=(
                        "Qualified leads are not converting into booked demos fast enough. "
                        f"Today: {qualified} qualified leads and {demos_booked} demos booked."
                    ),
                    estimated_impact="High",
                    confidence=0.89,
                )
            ]

        if bottleneck == "demo_to_customer":
            return [
                Recommendation(
                    title="Review demo quality and follow-up",
                    reason=(
                        "Demo volume is good, but customer conversion is weak. "
                        f"Today: {demos_booked} demos booked and {customers} customers."
                    ),
                    estimated_impact="High",
                    confidence=0.82,
                )
            ]

        return [
            Recommendation(
                title="Keep optimizing WhatsApp demo-booking flow",
                reason=(
                    "WhatsApp is the closest signal to booked demos and should remain the operating focus. "
                    f"Funnel Health Score: {health_score}/100."
                ),
                estimated_impact="Medium",
                confidence=0.78,
            )
        ]
