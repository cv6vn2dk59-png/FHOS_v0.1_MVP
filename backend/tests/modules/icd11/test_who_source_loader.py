"""Тест importer-а на синтетичному xlsx, що повторює реальну схему
WHO SimpleTabulation (18 колонок, включно з Grouping1-5 і колонкою
версії з непередбачуваним іменем "Version:...").

Не використовує реальний SimpleTabulation-ICD-11-MMS-en.xlsx --
той файл живе поза git (WHO_ICD11_DATA_DIR), тести мають бути
детерміновані й не залежати від зовнішнього файлу.
"""
import pytest
from openpyxl import Workbook

from app.modules.icd11.domain.entities import NodeKind, SpecialCode
from app.modules.icd11.persistence.who_source_loader import load_icd11_chapter_from_xlsx

HEADER = [
    "Foundation URI", "Linearization URI", "Code", "BlockId", "Title", "ClassKind",
    "DepthInKind", "IsResidual", "ChapterNo", "BrowserLink", "isLeaf",
    "Primary tabulation", "Grouping1", "Grouping2", "Grouping3", "Grouping4", "Grouping5",
    "Version:2024 Jan 21 - 22:30 UTC",
]

ROWS = [
    ["fnd:1", "who:chapter-01", None, "1", "Certain infectious or parasitic diseases", "chapter",
     0, False, "01", "http://x", False, True, None, None, None, None, None, "2024-01-21"],
    ["fnd:1A00-1A03", "who:block-1A00-1A03", None, "1A00-1A03",
     "- Gastroenteritis or colitis of infectious origin", "block",
     1, False, "01", "http://x", False, True, "1", None, None, None, None, "2024-01-21"],
    ["fnd:1A03", "who:category-1A03", "1A03", "1A03", "- - Cholera", "category",
     2, False, "01", "http://x", False, True, "1", "1A00-1A03", None, None, None, "2024-01-21"],
    ["fnd:1A03.0", "who:category-1A03.0", "1A03.0", None,
     "- - - Cholera due to Vibrio cholerae 01, biovar cholerae", "category",
     3, False, "01", "http://x", True, True, "1", "1A00-1A03", "1A03", None, None, "2024-01-21"],
    ["fnd:1A00.Z", "who:category-1A00.Z", "1A00.Z", None,
     "- - Gastroenteritis or colitis of infectious origin, unspecified", "category",
     2, True, "01", "http://x", True, True, "1", "1A00-1A03", None, None, None, "2024-01-21"],
    ["fnd:2A00", "who:category-2A00", "2A00", None, "- Some chapter 2 category", "category",
     1, False, "02", "http://x", True, True, "2", None, None, None, None, "2024-01-21"],
    ["fnd:weird", "who:weird", None, None, "Weird row", "unknown_kind",
     0, False, "01", "http://x", False, True, None, None, None, None, None, "2024-01-21"],
]


@pytest.fixture
def synthetic_xlsx(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(HEADER)
    for row in ROWS:
        ws.append(row)
    xlsx_dir = tmp_path / "who_data"
    xlsx_dir.mkdir()
    xlsx_path = xlsx_dir / "SimpleTabulation-ICD-11-MMS-en.xlsx"
    wb.save(xlsx_path)
    return xlsx_dir


class TestChapterFilterAndCounts:
    def test_only_chapter_01_rows_included(self, synthetic_xlsx):
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx))
        assert len(nodes) == 5
        assert "who:category-2A00" not in [n.id for n in nodes]

    def test_unknown_class_kind_row_excluded(self, synthetic_xlsx):
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx))
        assert "who:weird" not in [n.id for n in nodes]


class TestParentResolution:
    def test_chapter_row_has_no_parent(self, synthetic_xlsx):
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx))
        chapter = next(n for n in nodes if n.id == "who:chapter-01")
        assert chapter.parent_id is None
        assert chapter.node_kind == NodeKind.CHAPTER

    def test_block_parent_is_chapter(self, synthetic_xlsx):
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx))
        block = next(n for n in nodes if n.id == "who:block-1A00-1A03")
        assert block.parent_id == "who:chapter-01"

    def test_1a03_0_parent_resolves_to_1a03_record(self, synthetic_xlsx):
        """Точний випадок із завдання: 1A03.0 -> запис з Code=1A03."""
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx))
        by_id = {n.id: n for n in nodes}
        child = by_id["who:category-1A03.0"]
        parent = by_id[child.parent_id]
        assert parent.icd_code == "1A03"


class TestSpecialCodeAndTitle:
    def test_z_suffix_parsed_as_special_code(self, synthetic_xlsx):
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx))
        node = next(n for n in nodes if n.icd_code == "1A00.Z")
        assert node.special_code == SpecialCode.Z

    def test_no_special_code_for_regular_code(self, synthetic_xlsx):
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx))
        node = next(n for n in nodes if n.icd_code == "1A03")
        assert node.special_code == SpecialCode.NONE

    def test_depth_marker_stripped_from_title(self, synthetic_xlsx):
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx))
        node = next(n for n in nodes if n.icd_code == "1A03")
        assert node.english_title == "Cholera"
        assert not node.english_title.startswith("-")


class TestSourceRelease:
    def test_version_column_value_used_as_source_release(self, synthetic_xlsx):
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx))
        assert all(n.source_release == "2024-01-21" for n in nodes)


class TestFullTreeNoChapterFilter:
    """chapter_no=None (S07E06, ADR-0015 п.4 закрито) -- фільтр глави
    вимкнено, вантажаться усі глави одразу. Синтетичний фікстур уже
    містить рядок глави 02 (who:category-2A00), навмисно виключений
    у тестах TestChapterFilterAndCounts вище -- тут перевіряємо
    протилежне: він МАЄ бути включений."""

    def test_includes_rows_from_multiple_chapters(self, synthetic_xlsx):
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx), chapter_no=None)
        ids = [n.id for n in nodes]
        assert "who:chapter-01" in ids
        assert "who:category-2A00" in ids

    def test_still_excludes_unknown_class_kind(self, synthetic_xlsx):
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx), chapter_no=None)
        assert "who:weird" not in [n.id for n in nodes]

    def test_count_equals_all_valid_rows_regardless_of_chapter(self, synthetic_xlsx):
        """7 рядків фікстури - 1 (unknown_kind "weird") = 6 валідних
        вузлів з УСІХ глав (5 з глави 01 + 1 з глави 02)."""
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx), chapter_no=None)
        assert len(nodes) == 6

    def test_chapter_filter_still_works_when_explicit(self, synthetic_xlsx):
        """Регресія: chapter_no="01" явно і далі поводиться так само,
        як до появи повного дерева (зворотна сумісність)."""
        nodes = load_icd11_chapter_from_xlsx(who_data_dir=str(synthetic_xlsx), chapter_no="01")
        assert len(nodes) == 5
        assert "who:category-2A00" not in [n.id for n in nodes]
