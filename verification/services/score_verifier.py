from __future__ import annotations

from statistics import mean

from verification.schemas.claim_models import ClaimType, ExtractedClaim
from verification.schemas.evidence_models import ModelScoreRecord, VerificationInputPayload
from verification.schemas.verification_models import ScoreVerificationResult

_HIGHER_TERMS = {"higher", "greater", "better", "above", "top", "highest"}
_LOWER_TERMS = {"lower", "less", "below", "lowest"}
_STRONG_TERMS = {"strong", "high confidence", "high score", "robust"}
_WEAK_TERMS = {"weak", "low confidence", "low score", "limited"}


class ScoreVerifier:
    """Model-score presence/metadata/consistency checks."""

    def verify_claims(self, claims: list[ExtractedClaim], payload: VerificationInputPayload) -> list[ScoreVerificationResult]:
        by_candidate: dict[str, list[ModelScoreRecord]] = {}
        for score in payload.model_scores:
            by_candidate.setdefault(score.candidate_id, []).append(score)

        results: list[ScoreVerificationResult] = []

        for claim in claims:
            relevant = self._scores_for_claim(claim, by_candidate)
            score_blocks = [
                {
                    "candidate_id": score.candidate_id,
                    "score_name": score.score_name,
                    "score_value": score.score_value,
                    "model_name": score.model_name,
                    "model_version": score.model_version,
                    "run_id": score.run_id,
                }
                for score in relevant
            ]

            if claim.claim_type not in {ClaimType.RANKING_CLAIM, ClaimType.EVIDENCE_STRENGTH_CLAIM}:
                support = "true" if relevant else "partial"
                notes = [
                    "Score check is optional for this claim type.",
                    "Linked score metadata present." if relevant else "No directly linked score block for optional check.",
                ]
                results.append(
                    ScoreVerificationResult(
                        claim_id=claim.claim_id,
                        score_supported=support,
                        supporting_score_blocks=score_blocks,
                        score_notes=notes,
                    )
                )
                continue

            if not relevant:
                results.append(
                    ScoreVerificationResult(
                        claim_id=claim.claim_id,
                        score_supported="false",
                        supporting_score_blocks=[],
                        score_notes=["Claim references ranking/strength but no model scores were provided."],
                    )
                )
                continue

            metadata_complete = all(score.model_name and score.model_version for score in relevant)
            consistent, detail = self._directional_consistency(claim, relevant)

            if consistent and metadata_complete:
                support = "true"
            elif consistent or metadata_complete:
                support = "partial"
            else:
                support = "false"

            notes = [detail]
            if not metadata_complete:
                notes.append("Some score blocks are missing model_name/model_version metadata.")

            results.append(
                ScoreVerificationResult(
                    claim_id=claim.claim_id,
                    score_supported=support,
                    supporting_score_blocks=score_blocks,
                    score_notes=notes,
                )
            )

        return results

    def _scores_for_claim(self, claim: ExtractedClaim, by_candidate: dict[str, list[ModelScoreRecord]]) -> list[ModelScoreRecord]:
        scores: list[ModelScoreRecord] = []
        for target in claim.target_entity_ids:
            scores.extend(by_candidate.get(target, []))

        if scores:
            return scores

        if claim.claim_type in {ClaimType.RANKING_CLAIM, ClaimType.EVIDENCE_STRENGTH_CLAIM}:
            all_scores: list[ModelScoreRecord] = []
            for blocks in by_candidate.values():
                all_scores.extend(blocks)
            return all_scores

        return []

    def _directional_consistency(self, claim: ExtractedClaim, scores: list[ModelScoreRecord]) -> tuple[bool, str]:
        text = claim.claim_text.lower()
        grouped: dict[str, list[float]] = {}
        for score in scores:
            grouped.setdefault(score.candidate_id, []).append(float(score.score_value))

        aggregated = {candidate: mean(values) for candidate, values in grouped.items()}
        ordered = [target for target in claim.target_entity_ids if target in aggregated]

        if claim.claim_type == ClaimType.EVIDENCE_STRENGTH_CLAIM:
            avg_score = mean(aggregated.values())
            if any(term in text for term in _STRONG_TERMS):
                return (avg_score >= 0.60, f"Average supporting score is {avg_score:.3f} for strong-evidence claim.")
            if any(term in text for term in _WEAK_TERMS):
                return (avg_score <= 0.40, f"Average supporting score is {avg_score:.3f} for weak-evidence claim.")
            return (True, f"Average supporting score is {avg_score:.3f}; no explicit direction term found.")

        if len(ordered) >= 2:
            first = aggregated[ordered[0]]
            second = aggregated[ordered[1]]
            if any(term in text for term in _LOWER_TERMS):
                return (first <= second, f"Directional check: {ordered[0]} ({first:.3f}) <= {ordered[1]} ({second:.3f}).")
            if any(term in text for term in _HIGHER_TERMS):
                return (first >= second, f"Directional check: {ordered[0]} ({first:.3f}) >= {ordered[1]} ({second:.3f}).")

        if "top" in text or "highest" in text:
            top_candidate = max(aggregated, key=aggregated.get)
            first_target = ordered[0] if ordered else next(iter(aggregated))
            return (
                first_target == top_candidate,
                f"Top-score candidate is {top_candidate} ({aggregated[top_candidate]:.3f}).",
            )

        return (True, "No explicit directional ranking term found; treated as non-contradictory.")
