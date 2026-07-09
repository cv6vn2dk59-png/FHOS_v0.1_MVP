import pytest

from app.modules.contraindications.domain.entities import (
    Contraindication,
    find_contraindications,
)


class TestValidation:
    def test_creates_with_valid_ids(self):
        c = Contraindication(
            substance_chebi_id="CHEBI:6801",
            disease_mondo_id="MONDO:0005148",
            description="Метформін протипоказаний при тяжкій нирковій недостатності",
            knowledge_source_id="medic_v1",
        )
        assert c.substance_chebi_id == "CHEBI:6801"
        assert c.disease_mondo_id == "MONDO:0005148"

    def test_strips_whitespace(self):
        c = Contraindication(
            substance_chebi_id="  CHEBI:6801  ",
            disease_mondo_id=" MONDO:0005148 ",
            description="x",
            knowledge_source_id="medic_v1",
        )
        assert c.substance_chebi_id == "CHEBI:6801"
        assert c.disease_mondo_id == "MONDO:0005148"

    def test_raises_when_substance_id_missing_chebi_prefix(self):
        with pytest.raises(ValueError, match="substance_chebi_id"):
            Contraindication(
                substance_chebi_id="6801",
                disease_mondo_id="MONDO:0005148",
                description="x",
                knowledge_source_id="medic_v1",
            )

    def test_raises_when_disease_id_missing_mondo_prefix(self):
        with pytest.raises(ValueError, match="disease_mondo_id"):
            Contraindication(
                substance_chebi_id="CHEBI:6801",
                disease_mondo_id="0005148",
                description="x",
                knowledge_source_id="medic_v1",
            )

    def test_raises_when_substance_id_empty(self):
        with pytest.raises(ValueError, match="substance_chebi_id"):
            Contraindication(
                substance_chebi_id="   ",
                disease_mondo_id="MONDO:0005148",
                description="x",
                knowledge_source_id="medic_v1",
            )

    def test_raises_when_disease_id_empty(self):
        with pytest.raises(ValueError, match="disease_mondo_id"):
            Contraindication(
                substance_chebi_id="CHEBI:6801",
                disease_mondo_id="",
                description="x",
                knowledge_source_id="medic_v1",
            )


class TestMatches:
    def _make(self) -> Contraindication:
        return Contraindication(
            substance_chebi_id="CHEBI:6801",
            disease_mondo_id="MONDO:0005148",
            description="x",
            knowledge_source_id="medic_v1",
        )

    def test_true_when_both_present(self):
        c = self._make()
        assert c.matches({"CHEBI:6801"}, {"MONDO:0005148"}) is True

    def test_false_when_substance_missing(self):
        c = self._make()
        assert c.matches({"CHEBI:9999"}, {"MONDO:0005148"}) is False

    def test_false_when_disease_missing(self):
        c = self._make()
        assert c.matches({"CHEBI:6801"}, {"MONDO:9999999"}) is False

    def test_false_when_both_missing(self):
        c = self._make()
        assert c.matches(set(), set()) is False


class TestFindContraindications:
    def test_finds_matching_record(self):
        c1 = Contraindication(
            substance_chebi_id="CHEBI:6801",
            disease_mondo_id="MONDO:0005148",
            description="x",
            knowledge_source_id="medic_v1",
        )
        c2 = Contraindication(
            substance_chebi_id="CHEBI:1234",
            disease_mondo_id="MONDO:0007256",
            description="y",
            knowledge_source_id="medic_v1",
        )
        result = find_contraindications(
            substance_chebi_ids=["CHEBI:6801"],
            disease_mondo_ids=["MONDO:0005148"],
            known_contraindications=[c1, c2],
        )
        assert result == [c1]

    def test_returns_empty_when_no_match(self):
        c1 = Contraindication(
            substance_chebi_id="CHEBI:6801",
            disease_mondo_id="MONDO:0005148",
            description="x",
            knowledge_source_id="medic_v1",
        )
        result = find_contraindications(
            substance_chebi_ids=["CHEBI:9999"],
            disease_mondo_ids=["MONDO:9999999"],
            known_contraindications=[c1],
        )
        assert result == []

    def test_returns_multiple_matches(self):
        c1 = Contraindication(
            substance_chebi_id="CHEBI:6801",
            disease_mondo_id="MONDO:0005148",
            description="x",
            knowledge_source_id="medic_v1",
        )
        c2 = Contraindication(
            substance_chebi_id="CHEBI:6801",
            disease_mondo_id="MONDO:0007256",
            description="y",
            knowledge_source_id="medic_v1",
        )
        result = find_contraindications(
            substance_chebi_ids=["CHEBI:6801"],
            disease_mondo_ids=["MONDO:0005148", "MONDO:0007256"],
            known_contraindications=[c1, c2],
        )
        assert result == [c1, c2]
