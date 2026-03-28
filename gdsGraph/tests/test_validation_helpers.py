from __future__ import annotations

from gds.validation.gds_checks import GDSValidationReport, format_validation_report


def test_validation_report_formatting_contains_checks_samples_and_issues() -> None:
    report = GDSValidationReport(
        checks={"projection_exists": True, "protein_with_graph_embedding": 100},
        warnings=["some warning"],
        critical_issues=["critical issue"],
        sample_similar_proteins=[{"source_id": "P1", "target_id": "P2", "score": 0.91}],
        sample_communities=[{"community_id": 1, "member_count": 42}],
    )

    text = format_validation_report(report)

    assert "projection_exists: True" in text
    assert "sample_similar_proteins:" in text
    assert "P1 -> P2" in text
    assert "sample_communities:" in text
    assert "warnings:" in text
    assert "critical_issues:" in text
