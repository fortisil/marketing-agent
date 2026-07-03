from __future__ import annotations

from typing import Any


class DesignSystemAgent:
    name = "design_system_agent"

    def review_brand(self, brand_intelligence: dict[str, Any]) -> dict[str, Any]:
        if not brand_intelligence.get("available"):
            return {
                "status": "needs_regeneration",
                "reason": "Brand Library is unavailable; generated assets must not guess branding.",
                "checks": [],
            }

        checks = [
            self._check(bool(brand_intelligence.get("logos", {}).get("preferred")), "preferred_logo_available"),
            self._check(bool(brand_intelligence.get("colors", {}).get("primary")), "primary_color_available"),
            self._check(bool(brand_intelligence.get("design_rules")), "design_rules_available"),
            self._check(bool(brand_intelligence.get("asset_library")), "asset_library_available"),
        ]
        failed = [check for check in checks if not check["passed"]]
        return {
            "status": "approved" if not failed else "needs_regeneration",
            "reason": (
                "Brand Library is complete enough for autonomous content orchestration."
                if not failed
                else "Missing core brand assets; request regeneration or fill Brand Library before publishing."
            ),
            "checks": checks,
        }

    def _check(self, passed: bool, name: str) -> dict[str, Any]:
        return {"name": name, "passed": passed}
