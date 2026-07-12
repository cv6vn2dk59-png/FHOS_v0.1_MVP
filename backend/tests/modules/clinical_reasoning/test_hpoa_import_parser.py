from pathlib import Path

from scripts.import_phenotype_hpoa import parse_rows


def test_parse_rows_supports_hpo_headers_and_skips_not(tmp_path: Path):
    file = tmp_path / "phenotype.hpoa"
    file.write_text(
        "database_id\tdisease_name\tqualifier\thpo_id\treference\n"
        "OMIM:1\tDisease A\t\tHP:0001\tPMID:1\n"
        "OMIM:2\tDisease B\tNOT\tHP:0002\tPMID:2\n",
        encoding="utf-8",
    )
    assert list(parse_rows(file)) == [("OMIM:1", "Disease A", "HP:0001", "PMID:1")]
