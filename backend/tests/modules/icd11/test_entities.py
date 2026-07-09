import pytest

from app.modules.icd11.domain.entities import (
    ICD11Node,
    NodeKind,
    SpecialCode,
    TranslationStatus,
)


def _make(**overrides) -> ICD11Node:
    defaults = dict(
        id="http://id.who.int/icd/release/11/2024-01/mms/123",
        english_title="Certain infectious or parasitic diseases",
        translation_status=TranslationStatus.VERIFIED,
        node_kind=NodeKind.CHAPTER,
        special_code=SpecialCode.NONE,
        sort_order=1,
        source_release="2024-01",
        parent_id=None,
        icd_code=None,
        ukrainian_title="Певні інфекційні або паразитарні хвороби",
    )
    defaults.update(overrides)
    return ICD11Node(**defaults)


class TestValidation:
    def test_creates_with_valid_id(self):
        node = _make()
        assert node.id == "http://id.who.int/icd/release/11/2024-01/mms/123"

    def test_raises_when_id_empty(self):
        with pytest.raises(ValueError, match="id"):
            _make(id="")

    def test_raises_when_id_whitespace_only(self):
        with pytest.raises(ValueError, match="id"):
            _make(id="   ")


class TestNodeKindAndSpecialCode:
    def test_category_can_have_icd_code(self):
        node = _make(node_kind=NodeKind.CATEGORY, icd_code="1A00", parent_id="block-1")
        assert node.node_kind == NodeKind.CATEGORY
        assert node.icd_code == "1A00"

    def test_block_and_chapter_can_have_icd_code_none(self):
        chapter = _make(node_kind=NodeKind.CHAPTER, icd_code=None)
        block = _make(node_kind=NodeKind.BLOCK, icd_code=None, parent_id="chapter-1")
        assert chapter.icd_code is None
        assert block.icd_code is None

    def test_special_code_stored_correctly(self):
        node = _make(special_code=SpecialCode.Y)
        assert node.special_code == SpecialCode.Y

    def test_translation_status_stored_correctly(self):
        node = _make(translation_status=TranslationStatus.NEEDS_REVIEW)
        assert node.translation_status == TranslationStatus.NEEDS_REVIEW


class TestParentId:
    def test_root_chapter_allows_parent_id_none(self):
        node = _make(node_kind=NodeKind.CHAPTER, parent_id=None)
        assert node.parent_id is None
        assert node.is_root() is True

    def test_non_root_node_has_parent_id(self):
        node = _make(node_kind=NodeKind.CATEGORY, parent_id="block-1")
        assert node.parent_id == "block-1"
        assert node.is_root() is False
