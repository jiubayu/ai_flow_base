"""005 领域单元测试：应用名称/描述值对象校验与 WorkspaceApplication 实体行为。"""
from datetime import datetime, timezone

import pytest

from src.domain.workspace.entities import WorkspaceApplication
from src.domain.workspace.value_objects import (
    APPLICATION_DESCRIPTION_MAX_LENGTH,
    APPLICATION_NAME_MAX_LENGTH,
    ApplicationStatus,
    is_valid_application_description,
    is_valid_application_name,
    normalize_application_description,
    normalize_application_name,
)

NOW = datetime(2026, 11, 7, 12, 0, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 11, 7, 13, 0, 0, tzinfo=timezone.utc)


def _application(**overrides) -> WorkspaceApplication:
    defaults = dict(
        application_id="app-1",
        workspace_id="ws-1",
        owner_user_id="user-1",
        name="示例应用",
        description="描述",
        created_at=NOW,
        updated_at=NOW,
    )
    defaults.update(overrides)
    return WorkspaceApplication(**defaults)


class TestApplicationNameValidation:
    def test_rejects_empty_and_whitespace_only(self):
        assert not is_valid_application_name("")
        assert not is_valid_application_name("   ")

    def test_accepts_trimmed_1_to_80_chars(self):
        assert is_valid_application_name("a")
        assert is_valid_application_name(" 客户支持助手 ")
        assert is_valid_application_name("x" * APPLICATION_NAME_MAX_LENGTH)

    def test_rejects_over_80_chars(self):
        assert not is_valid_application_name("x" * (APPLICATION_NAME_MAX_LENGTH + 1))

    def test_normalize_trims_surrounding_whitespace(self):
        assert normalize_application_name("  报表助手 \n") == "报表助手"


class TestApplicationDescriptionValidation:
    def test_accepts_empty_and_up_to_500_chars(self):
        assert is_valid_application_description("")
        assert is_valid_application_description("y" * APPLICATION_DESCRIPTION_MAX_LENGTH)

    def test_rejects_over_500_chars(self):
        assert not is_valid_application_description("y" * (APPLICATION_DESCRIPTION_MAX_LENGTH + 1))

    def test_normalize_trims(self):
        assert normalize_application_description("  说明  ") == "说明"


class TestWorkspaceApplicationEntity:
    def test_default_status_is_draft(self):
        assert _application().status is ApplicationStatus.DRAFT

    def test_update_summary_changes_name_description_and_updated_at(self):
        app = _application()
        app.update_summary(" 新名称 ", " 新描述 ", LATER)
        assert app.name == "新名称"
        assert app.description == "新描述"
        assert app.updated_at == LATER
        assert app.created_at == NOW

    def test_update_summary_rejects_invalid_name(self):
        app = _application()
        with pytest.raises(ValueError):
            app.update_summary("   ", "描述", LATER)
        assert app.name == "示例应用"

    def test_update_summary_rejects_overlong_description(self):
        app = _application()
        with pytest.raises(ValueError):
            app.update_summary("名称", "z" * 501, LATER)
        assert app.description == "描述"

    def test_card_view_shape(self):
        card = _application().to_card_view()
        assert card.application_id == "app-1"
        assert card.name == "示例应用"
        assert card.description == "描述"
        assert card.status == "draft"
        assert card.updated_at == NOW

    def test_canvas_view_is_always_readonly_empty(self):
        canvas = _application().to_canvas_view()
        assert canvas.mode == "empty"
        assert canvas.editable is False
        assert canvas.entry_label == "开始编排"
        assert canvas.application_id == "app-1"
