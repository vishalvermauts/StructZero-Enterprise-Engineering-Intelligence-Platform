# Deterministic blueprint validator: structural, cross-reference and compliance-regime checks.
# Co-authored with CoCo
"""
Production Validators Module
============================
A deterministic Python rules engine that validates the AI-generated architecture blueprints
against enterprise completeness, consistency, security and performance criteria.

Design note: the checks here deliberately verify *substance that can be absent*, not
vocabulary that the generator was already instructed to include. Rules that merely look for
a word the synthesizer prompt mandates cannot fail, and a score that cannot fail is not a
measurement. Every rule below can fail on a plausible blueprint.
"""
from core.models import ValidationResult
import re

# Sections whose absence makes the blueprint unusable -> error (blocks approval).
CORE_SECTIONS = ["Executive Summary", "Architecture", "Components", "Security", "Risks"]

# Sections the synthesizer is asked for and a developer needs -> warning if absent.
# Kept as warnings so a single omission degrades the score instead of permanently
# rejecting every run, which would just burn revision rounds.
EXPECTED_SECTIONS = [
    "Requirements", "Folder Structure", "API Design", "Performance",
    "Trade-offs", "Assumptions", "Decision Log", "Roadmap", "Recommended Actions",
]

# Substantive obligations per compliance regime. Presence of the regime's *name* proves
# nothing, so each regime is checked for the concepts a real design must address.
COMPLIANCE_OBLIGATIONS = {
    "HIPAA": [
        ("PHI handling", r"\bPHI\b|protected health information"),
        ("de-identification", r"de-?identif|anonymi[sz]|pseudonymi[sz]"),
        ("business associate agreement", r"\bBAA\b|business associate"),
        ("audit logging of access", r"audit (log|trail)|access log"),
    ],
    "GDPR": [
        ("data residency", r"residenc|data location|region[- ]lock|in-region|EU region"),
        ("retention limits", r"retention|purge|delete after|TTL"),
        ("right to erasure", r"erasure|right to be forgotten|deletion request|\bDSAR\b"),
        ("lawful basis or DPA", r"\bDPA\b|data processing agreement|lawful basis|consent"),
    ],
    "PCI-DSS": [
        ("cardholder data scope", r"cardholder|\bCDE\b|\bPAN\b"),
        ("tokenization", r"token[iz]|tokenis"),
        ("network segmentation", r"segment|isolat|separate network|\bVLAN\b|\bDMZ\b"),
        ("key management", r"\bKMS\b|key rotation|key management"),
    ],
    "SOC2": [
        ("access control", r"\bRBAC\b|least privilege|access control|\bIAM\b"),
        ("change management", r"change management|change control|approval workflow"),
        ("monitoring and alerting", r"monitor|alert|observab"),
        ("audit logging", r"audit (log|trail)|immutable log"),
    ],
}


# Only these categories are severe enough that a hard error rejects outright.
SEVERE_ERROR_CATEGORIES = ("Security", "Compliance")


class ProductionValidator:
    """
    Validates raw markdown blueprints against enterprise constraints.
    Returns a ValidationResult containing scores and warnings/errors.
    """

    def validate(self, raw_markdown: str, compliance: str = None, prompt: str = None,
                 board_votes: dict = None) -> ValidationResult:
        warnings = []
        errors = []
        # Track which categories raised hard errors so severity can be graded below.
        error_categories = set()

        scores = {
            "Completeness": 100,
            "Security": 100,
            "Performance": 100,
            "Consistency": 100,
            "Compliance": 100,
        }

        def deduct(category: str, amount: int, msg: str, is_error: bool = False):
            scores[category] = max(0, scores[category] - amount)
            if is_error:
                errors.append(msg)
                error_categories.add(category)
            else:
                warnings.append(msg)

        md = raw_markdown or ""
        lower_md = md.lower()

        # ------------------------------------------------------------------ structure
        for section in CORE_SECTIONS:
            if not re.search(rf"#+.*{re.escape(section)}", md, re.IGNORECASE):
                deduct("Completeness", 10, f"Missing core section: {section}", is_error=True)
        for section in EXPECTED_SECTIONS:
            if not re.search(rf"#+.*{re.escape(section)}", md, re.IGNORECASE):
                deduct("Completeness", 5, f"Missing expected section: {section}")

        graphviz_matches = re.findall(r"```graphviz(.*?)```", md, re.DOTALL)
        if not graphviz_matches:
            deduct("Completeness", 10, "Missing Graphviz Diagram block.", is_error=True)
        elif len(graphviz_matches) > 1:
            deduct("Consistency", 5, "Multiple Graphviz Diagram blocks found. Only the first will be rendered.")

        # ------------------------------------------- diagram vs prose cross-reference
        # A diagram whose components are never described is a genuine defect and is
        # invisible to keyword checks.
        if graphviz_matches:
            diagram = graphviz_matches[0]
            prose = re.sub(r"```graphviz.*?```", "", md, flags=re.DOTALL).lower()
            labels = re.findall(r'label\s*=\s*"([^"]{3,60})"', diagram)
            if not labels:
                labels = re.findall(r'^\s*([A-Za-z][A-Za-z0-9_]{2,40})\s*\[', diagram, re.M)
            cleaned = []
            for raw_label in labels:
                text = re.sub(r"\\[nlr]", " ", raw_label)
                text = re.sub(r"[\(\[].*?[\)\]]", " ", text)
                text = text.strip(" -:\u2022|")
                if len(text) >= 3 and not text.lower().startswith(("cluster", "subgraph")):
                    cleaned.append(text)
            orphans = []
            for label in dict.fromkeys(cleaned):
                tokens = [t for t in re.split(r"[^A-Za-z0-9]+", label) if len(t) > 3]
                if not tokens:
                    continue
                if not any(t.lower() in prose for t in tokens):
                    orphans.append(label)
            if cleaned:
                ratio = len(orphans) / len(cleaned)
                if ratio > 0.4:
                    deduct("Consistency", 15,
                           f"{len(orphans)} of {len(cleaned)} diagram components are never described "
                           f"in the document: {', '.join(orphans[:5])}", is_error=True)
                elif orphans:
                    deduct("Consistency", 6,
                           f"Diagram components not described in the document: {', '.join(orphans[:5])}")

        # -------------------------------------------------- compliance obligations
        regime = (compliance or "").strip().upper()
        if regime and regime != "NONE":
            obligations = COMPLIANCE_OBLIGATIONS.get(regime)
            if obligations:
                missing = [label for label, pattern in obligations
                           if not re.search(pattern, md, re.IGNORECASE)]
                if missing:
                    per_item = 12 if len(missing) > 1 else 8
                    deduct("Compliance", per_item * len(missing),
                           f"{regime} design obligations not addressed: {', '.join(missing)}",
                           is_error=len(missing) >= len(obligations) / 2)
            elif not re.search(rf"{re.escape(regime)}", md, re.IGNORECASE):
                deduct("Compliance", 15,
                       f"Target compliance regime {regime} is never mentioned.", is_error=True)

        # ------------------------------------------------ quantitative commitments
        if prompt:
            asked_numeric = re.search(
                r"\d[\d,\.]*\s*(tps|rps|qps|ms|seconds?|/s|per second|requests|transactions|users|vehicles|devices)",
                prompt, re.IGNORECASE)
            if asked_numeric:
                committed = re.findall(
                    r"\d[\d,\.]*\s*(?:tps|rps|qps|ms|seconds?|/s|per second|GB|TB|MB/s)",
                    md, re.IGNORECASE)
                if len(committed) < 3:
                    deduct("Performance", 15,
                           f"Request specified quantitative targets but the design commits to only "
                           f"{len(committed)} numeric figure(s).", is_error=(len(committed) == 0))
        if not re.search(r"\d[\d,\.]*\s*(ms|tps|rps|qps|/s|per second)", md, re.IGNORECASE):
            deduct("Performance", 10, "No concrete numeric performance bounds anywhere in the design.")

        # ------------------------------------------------------- risks & mitigations
        risk_body = self._section_body(md, r"Risks?")
        if risk_body:
            risk_items = re.findall(r"^\s*(?:[-*+]|\d+\.|\|)\s*(.+)$", risk_body, re.M)
            risk_items = [r for r in risk_items if len(r.strip()) > 12]
            if risk_items and not re.search(r"mitigat|remediat|contingen|fallback", risk_body, re.I):
                # Filed under Completeness, not Security: risks documented without mitigations
                # is a documentation gap, not a security defect, and should not hard-reject an
                # otherwise sound design.
                deduct("Completeness", 10,
                       f"{len(risk_items)} risks listed with no mitigation stated.", is_error=True)
        elif re.search(r"#+.*Risks?", md, re.I):
            deduct("Completeness", 5, "Risks section is present but empty.")

        # ------------------------------------------------------------- decision log
        decision_body = self._section_body(md, r"Decision Log")
        if decision_body:
            buckets = [b for b in ("Accepted", "Rejected", "Modified")
                       if re.search(rf"\b{b}\b", decision_body, re.I)]
            if len(buckets) < 2:
                deduct("Consistency", 8,
                       f"Decision Log records only {len(buckets)} of Accepted/Rejected/Modified - "
                       f"no evidence recommendations were genuinely weighed.")

        # ----------------------------------------------------- legacy sanity checks
        if "kafka" in lower_md and not re.search(r"(broker|event|queue|stream)", lower_md):
            deduct("Consistency", 5, "Kafka is mentioned but no event/broker terminology found.")
        if "redis" in lower_md and not re.search(r"(cache|caching)", lower_md):
            deduct("Consistency", 5, "Redis is mentioned but caching strategy is missing.")
        if not re.search(r"(encryption|tls|kms|encrypt)", lower_md):
            deduct("Security", 10, "No mention of encryption in transit or at rest.", is_error=True)

        # ---------------------------------------------------------- board of review
        # The specialist reviewers already produce a real judgement; treat it as evidence.
        board_decision = None
        if board_votes:
            verdicts = [str(v).strip().upper() for v in board_votes.values() if v]
            if any(v.startswith("BLOCK") for v in verdicts):
                board_decision = "BLOCK"
                blockers = [k for k, v in board_votes.items()
                            if str(v).strip().upper().startswith("BLOCK")]
                deduct("Consistency", 25,
                       f"Review board BLOCKED: {', '.join(blockers)}", is_error=True)
            elif any("WARNING" in v for v in verdicts):
                board_decision = "APPROVE WITH WARNINGS"
                warned = [k for k, v in board_votes.items() if "WARNING" in str(v).upper()]
                deduct("Consistency", 5,
                       f"Review board approved with reservations from: {', '.join(warned)}")
            elif verdicts:
                board_decision = "APPROVE"

        # -------------------------------------------------------------- final status
        overall = sum(scores.values()) // len(scores)

        # Severity tiers. Previously any single error rejected the blueprint, so documents
        # scoring 92-94 were rejected over one missing section while the review board was
        # voting APPROVE - the record contradicted itself. Reject only for material defects:
        #   * the review board explicitly vetoed it (already given MAX_REVISION_ROUNDS to fix)
        #   * the overall score collapsed below 80
        #   * a Security or Compliance error, which cannot be shipped with a caveat
        # Everything else is a warning: the design is usable but carries known gaps.
        blocking = sorted(c for c in error_categories if c in SEVERE_ERROR_CATEGORIES)

        if board_decision == "BLOCK":
            status = "REJECTED"
        elif overall < 80:
            status = "REJECTED"
        elif blocking:
            status = "REJECTED"
        elif errors or warnings or overall < 85:
            status = "APPROVED WITH WARNINGS"
        else:
            status = "APPROVED"

        return ValidationResult(
            status=status,
            warnings=warnings,
            errors=errors,
            overall_score=overall,
            category_scores=scores,
            board_votes=board_votes or {},
            board_decision=board_decision,
            blocking_categories=blocking,
        )

    @staticmethod
    def _section_body(markdown: str, heading_pattern: str) -> str:
        """
        Return the text under the first heading matching heading_pattern, stopping at the
        next heading of the same or higher level. Stopping at *any* heading would treat a
        section organised into subheadings (Decision Log -> Accepted/Rejected/Modified) as
        empty, which produced false positives.
        """
        m = re.search(rf"^(#+)\s*[^\n]*{heading_pattern}[^\n]*$", markdown, re.I | re.M)
        if not m:
            return ""
        level = len(m.group(1))
        start = m.end()
        nxt = re.search(rf"^#{{1,{level}}}\s+\S", markdown[start:], re.M)
        return markdown[start:start + nxt.start()] if nxt else markdown[start:]
