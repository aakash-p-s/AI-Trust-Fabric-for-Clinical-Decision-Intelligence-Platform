from backend.services import rulebook_service


def test_update_rulebook_writes_changelog_for_changed_fields(db_session):
    new_values = {
        "approved_model_versions": ["v2.0", "v2.1", "v2.2"],
        "minimum_confidence_threshold": 0.80,
        "high_risk_conditions_requiring_review": ["Pneumonia", "Tumor", "Cancer"],
    }
    rulebook_service.update_rulebook(db_session, new_values, changed_by="compliance.lead")

    entries = rulebook_service.get_changelog(db_session)
    descriptions = [e.change_description for e in entries]

    assert any("approved model versions" in d for d in descriptions)
    assert any("0.75 -> 0.8" in d for d in descriptions)
    # high_risk_conditions_requiring_review unchanged -> no changelog entry for it
    assert not any("high-risk conditions" in d for d in descriptions)


def test_update_rulebook_no_changelog_when_nothing_changes(db_session):
    current = rulebook_service.get_rulebook(db_session)
    same_values = {
        "approved_model_versions": current.approved_model_versions,
        "minimum_confidence_threshold": current.minimum_confidence_threshold,
        "high_risk_conditions_requiring_review": current.high_risk_conditions_requiring_review,
    }
    rulebook_service.update_rulebook(db_session, same_values, changed_by="compliance.lead")
    entries = rulebook_service.get_changelog(db_session)
    assert len(entries) == 0
