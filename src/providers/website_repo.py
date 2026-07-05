from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import subprocess
from typing import Any, Optional
from zoneinfo import ZoneInfo

from src.providers.base import MetricSnapshot


TEXT_EXTENSIONS = {
    ".md",
    ".mdx",
    ".txt",
    ".html",
    ".tsx",
    ".ts",
    ".jsx",
    ".js",
    ".vue",
    ".svelte",
    ".css",
}
IGNORED_PARTS = {
    ".git",
    ".next",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
}
CTA_PATTERNS = re.compile(
    r"(book|demo|contact|whatsapp|call|schedule|start|try|learn more|דמו|צור קשר|וואטסאפ|שיחה)",
    re.IGNORECASE,
)
WHATSAPP_PATTERNS = re.compile(
    r"(?:wa\.me/[\d+]+|api\.whatsapp\.com/[^\s\"')]+|whatsapp:[^\s\"')]+|\+972[\d\s-]{7,})",
    re.IGNORECASE,
)
TEXT_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9 ,.'’:-]{12,}|[\u0590-\u05FF][\u0590-\u05FF ,.'״׳:-]{8,}")
QUOTED_TEXT_PATTERN = re.compile(r"""(?P<quote>["'`])(?P<text>[^"'`{}<>]{8,240})(?P=quote)""")
JSX_TEXT_PATTERN = re.compile(r">([^<>{}\n][^<>{}]{8,240})<")


class WebsiteRepoProvider:
    name = "website_repo"

    def __init__(
        self,
        company_config: dict[str, Any],
        timezone: str,
        repo_path: Optional[Path] = None,
    ) -> None:
        self.company_config = company_config
        self.timezone = timezone
        self.repo_path = repo_path

    def collect(self) -> MetricSnapshot:
        collected_at = datetime.now(ZoneInfo(self.timezone))

        if not self.repo_path:
            return MetricSnapshot(
                provider=self.name,
                collected_at=collected_at,
                metrics={"website_intelligence": self._mock_intelligence()},
                notes=["CHATBOT2U_REPO_PATH is not set; using mock website intelligence."],
            )

        if not self.repo_path.exists():
            return MetricSnapshot(
                provider=self.name,
                collected_at=collected_at,
                metrics={"website_intelligence": self._mock_intelligence()},
                notes=[f"Configured website repo path does not exist: {self.repo_path}"],
            )

        intelligence = self._analyze_repo(self.repo_path)
        return MetricSnapshot(
            provider=self.name,
            collected_at=collected_at,
            metrics={"website_intelligence": intelligence},
            notes=[f"Analyzed local website repo at {self.repo_path}."],
        )

    def _mock_intelligence(self) -> dict[str, Any]:
        assets = self.company_config.get("business_assets", {})
        return {
            "source": "mock",
            "repo": assets.get("website_repo", "fortisil/ChatBot2U"),
            "local_path": None,
            "package_app_structure": [
                "Website repo not connected locally yet.",
                "Set CHATBOT2U_REPO_PATH to enable local repo analysis.",
            ],
            "landing_pages": ["Mock landing page: home"],
            "readme_summary": "README not inspected because local repo path is not configured.",
            "recent_commits": [],
            "product_claims": [
                "ChatBot2U helps law firms convert WhatsApp conversations into booked demos.",
            ],
            "features_detected": [
                "WhatsApp-first lead capture",
                "AI-assisted qualification",
                "Booked demo workflow",
            ],
            "ctas_detected": ["Book a demo", "Contact on WhatsApp"],
            "whatsapp_links_detected": [assets.get("whatsapp", "+972559720244")],
            "missing_or_weak_ctas": [
                "Confirm every primary landing page has a WhatsApp CTA above the fold.",
            ],
            "marketing_opportunities": [
                "Connect website claims to the mission: generate one additional paying customer.",
            ],
            "content_ideas": [
                "Publish a founder-led demo showing a law-firm lead moving from WhatsApp to booked appointment.",
            ],
            "website_risks": [
                "Website intelligence is mocked until CHATBOT2U_REPO_PATH points at the local repo.",
            ],
            "sample_text": [],
        }

    def _analyze_repo(self, repo_path: Path) -> dict[str, Any]:
        files = self._iter_files(repo_path)
        text_files = self._prioritize_text_files(
            [path for path in files if path.suffix.lower() in TEXT_EXTENSIONS],
            repo_path,
        )
        file_contents = self._read_text_files(text_files)
        sample_text = self._collect_text_samples(file_contents)
        ctas = self._detect_ctas(sample_text)
        whatsapp_links = self._detect_whatsapp_links(file_contents)

        return {
            "source": "local",
            "repo": self.company_config.get("business_assets", {}).get("website_repo"),
            "local_path": str(repo_path),
            "package_app_structure": self._package_app_structure(repo_path, files),
            "landing_pages": self._landing_pages(repo_path, files),
            "readme_summary": self._readme_summary(repo_path),
            "recent_commits": self._recent_commits(repo_path),
            "product_claims": self._product_claims(sample_text),
            "features_detected": self._features_detected(sample_text),
            "ctas_detected": ctas,
            "whatsapp_links_detected": whatsapp_links,
            "missing_or_weak_ctas": self._missing_or_weak_ctas(ctas, whatsapp_links),
            "marketing_opportunities": self._marketing_opportunities(sample_text, ctas),
            "content_ideas": self._content_ideas(sample_text),
            "website_risks": self._website_risks(text_files, whatsapp_links),
            "sample_text": sample_text[:25],
        }

    def _iter_files(self, repo_path: Path) -> list[Path]:
        files: list[Path] = []
        for path in repo_path.rglob("*"):
            if not path.is_file():
                continue
            if any(part in IGNORED_PARTS for part in path.parts):
                continue
            files.append(path)
        return sorted(files)

    def _package_app_structure(self, repo_path: Path, files: list[Path]) -> list[str]:
        markers = [
            "package.json",
            "next.config.js",
            "next.config.ts",
            "vite.config.ts",
            "src",
            "app",
            "pages",
            "components",
            "public",
        ]
        structure: list[str] = []
        for marker in markers:
            candidate = repo_path / marker
            if candidate.exists():
                structure.append(marker)

        top_dirs = sorted({path.relative_to(repo_path).parts[0] for path in files if path.relative_to(repo_path).parts})
        for item in top_dirs[:12]:
            if item not in structure:
                structure.append(item)

        return structure[:20]

    def _landing_pages(self, repo_path: Path, files: list[Path]) -> list[str]:
        landing_pages: list[str] = []
        for path in files:
            rel = path.relative_to(repo_path).as_posix()
            rel_lower = rel.lower()
            if rel_lower in {"app/page.tsx", "app/page.jsx", "pages/index.tsx", "pages/index.jsx"}:
                landing_pages.append(rel)
            elif any(part in rel_lower for part in ["landing", "home", "hero", "pricing"]):
                landing_pages.append(rel)
        return landing_pages[:20]

    def _readme_summary(self, repo_path: Path) -> str:
        for name in ("README.md", "readme.md", "README.mdx"):
            readme = repo_path / name
            if readme.exists():
                return self._safe_read(readme)[:1200]
        return "No README found."

    def _recent_commits(self, repo_path: Path) -> list[str]:
        if not (repo_path / ".git").exists():
            return []

        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), "log", "--oneline", "-5"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return []

        if result.returncode != 0:
            return []

        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def _read_text_files(self, text_files: list[Path]) -> list[str]:
        contents: list[str] = []
        for path in text_files[:120]:
            content = self._safe_read(path)
            if content:
                contents.append(content)
        return contents

    def _prioritize_text_files(self, text_files: list[Path], repo_path: Path) -> list[Path]:
        def priority(path: Path) -> tuple[int, str]:
            rel = path.relative_to(repo_path).as_posix().lower()
            if "translation" in rel:
                return (0, rel)
            if "hero" in rel or "pricing" in rel or "contact" in rel:
                return (1, rel)
            if "legalpractice" in rel or "solutions" in rel:
                return (2, rel)
            if rel.endswith("readme.md"):
                return (3, rel)
            return (4, rel)

        return sorted(text_files, key=priority)

    def _collect_text_samples(self, file_contents: list[str]) -> list[str]:
        samples: list[str] = []
        for content in file_contents:
            candidates = []
            candidates.extend(match.group("text") for match in QUOTED_TEXT_PATTERN.finditer(content))
            candidates.extend(match.group(1) for match in JSX_TEXT_PATTERN.finditer(content))
            candidates.extend(TEXT_TOKEN_PATTERN.findall(content))

            for candidate in candidates:
                cleaned = self._clean_text(candidate)
                if not self._is_marketing_text(cleaned):
                    continue
                samples.append(cleaned[:240])
        return self._unique_limited(samples, 120)

    def _detect_ctas(self, samples: list[str]) -> list[str]:
        ctas = []
        for sample in samples:
            if CTA_PATTERNS.search(sample):
                ctas.append(sample)
        return self._unique_limited(ctas, 20)

    def _detect_whatsapp_links(self, file_contents: list[str]) -> list[str]:
        links: list[str] = []
        for content in file_contents:
            links.extend(match.group(0) for match in WHATSAPP_PATTERNS.finditer(content))
        return self._unique_limited(links, 20)

    def _product_claims(self, samples: list[str]) -> list[str]:
        claim_words = ("AI", "chatbot", "WhatsApp", "lead", "demo", "law", "firm", "automation")
        claims = [sample for sample in samples if any(word.lower() in sample.lower() for word in claim_words)]
        return self._unique_limited(claims, 12)

    def _features_detected(self, samples: list[str]) -> list[str]:
        feature_map = {
            "WhatsApp": "WhatsApp conversation capture",
            "demo": "Demo booking flow",
            "calendar": "Calendar scheduling",
            "lead": "Lead qualification",
            "AI": "AI-assisted messaging",
            "dashboard": "Dashboard or reporting",
            "analytics": "Analytics",
            "law": "Law-firm positioning",
        }
        features = []
        joined = " ".join(samples).lower()
        for needle, feature in feature_map.items():
            if needle.lower() in joined:
                features.append(feature)
        return features

    def _missing_or_weak_ctas(self, ctas: list[str], whatsapp_links: list[str]) -> list[str]:
        issues: list[str] = []
        if not ctas:
            issues.append("No clear CTA text detected in scanned website content.")
        if not whatsapp_links:
            issues.append("No WhatsApp link or phone CTA detected in scanned website content.")
        if ctas and not any("demo" in cta.lower() or "דמו" in cta for cta in ctas):
            issues.append("CTA language may not be directly tied to booked demos.")
        return issues

    def _marketing_opportunities(self, samples: list[str], ctas: list[str]) -> list[str]:
        opportunities = [
            "Align the website hero CTA with the daily mission: generate one additional paying customer.",
        ]
        joined = " ".join(samples).lower()
        if "law" not in joined and "עורכ" not in joined:
            opportunities.append("Make law-firm ICP clearer on high-intent pages.")
        if not any("whatsapp" in cta.lower() or "וואטסאפ" in cta for cta in ctas):
            opportunities.append("Add a WhatsApp-first CTA wherever prospects show intent.")
        return opportunities

    def _content_ideas(self, samples: list[str]) -> list[str]:
        ideas = [
            "Create a short product demo showing a WhatsApp lead becoming a booked appointment.",
            "Publish a law-firm intake checklist tied to faster response time.",
        ]
        joined = " ".join(samples).lower()
        if "pricing" not in joined:
            ideas.append("Test a pricing or pilot-offer section to validate willingness to pay.")
        return ideas

    def _website_risks(self, text_files: list[Path], whatsapp_links: list[str]) -> list[str]:
        risks: list[str] = []
        if len(text_files) < 3:
            risks.append("Very little website text was available for analysis.")
        if not whatsapp_links:
            risks.append("Missing WhatsApp CTA can weaken demo-booking conversion.")
        return risks

    def _safe_read(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""

    def _unique_limited(self, values: list[str], limit: int) -> list[str]:
        seen = set()
        unique: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            unique.append(value)
            if len(unique) >= limit:
                break
        return unique

    def _clean_text(self, value: str) -> str:
        cleaned = value.replace("\\n", " ")
        cleaned = cleaned.replace("%20", " ")
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip(" \t\r\n,;{}()[]")

    def _is_marketing_text(self, value: str) -> bool:
        if len(value) < 8:
            return False
        lowered = value.lower()
        code_markers = (
            "text-",
            "bg-",
            "border-",
            "rounded-",
            "case ",
            "return ",
            "import ",
            "export ",
            "classname",
            "usestate",
            "onclick",
            "href=",
            "https://fonts",
        )
        if any(marker in lowered for marker in code_markers):
            return False
        if re.fullmatch(r"[A-Za-z0-9_./:-]+", value):
            return False
        if value.startswith(("import ", "export ", "const ", "return ")):
            return False
        if value in {"IndustrySolutions", "LegalPracticeAutomationHebrew", "WhatsAppPage"}:
            return False
        return any(ch.isalpha() or "\u0590" <= ch <= "\u05ff" for ch in value)
