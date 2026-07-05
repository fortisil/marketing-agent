from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from src.agents.design_system import DesignSystemAgent
from src.providers.base import MetricSnapshot


class BrandProvider:
    name = "brand_brain"

    def __init__(
        self,
        company_config: dict[str, Any],
        timezone: str,
        brand_root: Path,
        assets_root: Path,
    ) -> None:
        self.company_config = company_config
        self.timezone = timezone
        self.brand_root = brand_root
        self.assets_root = assets_root

    def collect(self) -> MetricSnapshot:
        collected_at = datetime.now(ZoneInfo(self.timezone))
        if not self.brand_root.exists():
            return MetricSnapshot(
                provider=self.name,
                collected_at=collected_at,
                metrics={
                    "brand_intelligence": {
                        "available": False,
                        "source": "missing_brand_library",
                        "reason": f"Brand Library not found: {self.brand_root}",
                    }
                },
                notes=["Brand Library missing; repository inference may be used only as fallback."],
            )

        brand_intelligence = self._load_brand_intelligence()
        brand_intelligence["design_system_review"] = DesignSystemAgent().review_brand(brand_intelligence)
        return MetricSnapshot(
            provider=self.name,
            collected_at=collected_at,
            metrics={"brand_intelligence": brand_intelligence},
            notes=["Loaded dedicated Brand Library before repository fallback."],
        )

    def _load_brand_intelligence(self) -> dict[str, Any]:
        brand_config = self._load_yaml(self.brand_root / "brand.yaml")
        colors = self._load_yaml(self.brand_root / "colors.yaml")
        design_rules_path = self.brand_root / "design_rules.md"
        design_rules = design_rules_path.read_text(encoding="utf-8").strip() if design_rules_path.exists() else ""
        logos = self._logos(brand_config)
        return {
            "available": True,
            "source": "brand_library",
            "company": self.company_config.get("company", {}).get("name", "ChatBot2U"),
            "brand": brand_config.get("brand", {}),
            "cta": brand_config.get("cta", {}),
            "image_generation": brand_config.get("image_generation", {}),
            "colors": colors,
            "logos": logos,
            "typography": brand_config.get("typography", {}),
            "tone": brand_config.get("brand", {}).get("tone", []),
            "instagram": brand_config.get("instagram", {}),
            "rules": brand_config.get("rules", []),
            "design_rules": design_rules,
            "asset_library": self._asset_library(brand_config),
            "missing_assets": self._missing_assets(brand_config),
            "fallback_policy": "Use website repository inference only when a Brand Library field is missing.",
        }

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}

    def _logos(self, brand_config: dict[str, Any]) -> dict[str, str]:
        logo_config = brand_config.get("logo", {})
        if not isinstance(logo_config, dict):
            logo_config = {}
        return {
            "preferred": str(self.brand_root / "logo" / str(logo_config.get("preferred", ""))),
            "light_background": str(self.brand_root / "logo" / str(logo_config.get("light_background", ""))),
            "dark_background": str(self.brand_root / "logo" / str(logo_config.get("dark_background", ""))),
        }

    def _asset_library(self, brand_config: dict[str, Any]) -> dict[str, str]:
        library = brand_config.get("asset_library", {})
        if not isinstance(library, dict):
            return {}
        return {key: str(Path(value)) for key, value in library.items()}

    def _missing_assets(self, brand_config: dict[str, Any]) -> list[str]:
        missing = []
        for key, path in self._asset_library(brand_config).items():
            if not Path(path).exists():
                missing.append(key)
        for key, path in self._logos(brand_config).items():
            if path and not Path(path).exists():
                missing.append(f"logo.{key}")
        return missing
