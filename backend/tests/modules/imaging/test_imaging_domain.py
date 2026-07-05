from datetime import date

from app.modules.imaging.domain.entities import ImagingStudy, ImagingStudyType


def make_study(**overrides) -> ImagingStudy:
    defaults = dict(
        study_type=ImagingStudyType.XRAY,
        body_part="Грудна клітка",
        study_date=date(2026, 5, 9),
    )
    defaults.update(overrides)
    return ImagingStudy(**defaults)


class TestHasConclusion:
    def test_true_when_conclusion_present(self):
        assert make_study(radiologist_conclusion="Без патологій").has_conclusion() is True

    def test_false_when_conclusion_none(self):
        assert make_study(radiologist_conclusion=None).has_conclusion() is False

    def test_false_when_conclusion_empty_string(self):
        assert make_study(radiologist_conclusion="   ").has_conclusion() is False


class TestHasImageFile:
    def test_true_when_path_present(self):
        assert make_study(image_file_path="D:/scans/xray1.dcm").has_image_file() is True

    def test_false_when_path_none(self):
        assert make_study(image_file_path=None).has_image_file() is False


class TestDaysSinceStudy:
    def test_calculates_days_correctly(self):
        study = make_study(study_date=date(2026, 5, 9))
        assert study.days_since_study(as_of=date(2026, 6, 26)) == 48

    def test_zero_when_same_day(self):
        study = make_study(study_date=date(2026, 5, 9))
        assert study.days_since_study(as_of=date(2026, 5, 9)) == 0