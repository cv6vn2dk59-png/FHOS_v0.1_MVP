from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.clinical_reasoning.domain.evidence import HypothesisEvidenceRole
from app.modules.clinical_reasoning.domain.laboratory_profile import LaboratoryObservationSnapshot


@dataclass(frozen=True)
class EvidenceReference:
    laboratory_result_id: int
    test_code: str
    role: HypothesisEvidenceRole
    rationale: str


@dataclass(frozen=True)
class CandidateHypothesis:
    code: str
    title: str
    status: str = "candidate_direction"
    evidence: list[EvidenceReference] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    prohibited_conclusions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DomainReaderReport:
    specialty: str
    observed_fact_ids: list[int]
    candidate_hypotheses: list[CandidateHypothesis]
    questions: list[str]
    confidence: str
    prohibited_conclusions: list[str]


def _by_code(observations: list[LaboratoryObservationSnapshot]) -> dict[str, LaboratoryObservationSnapshot]:
    return {item.test_code.upper(): item for item in observations}


def _ref(item: LaboratoryObservationSnapshot, role: HypothesisEvidenceRole, rationale: str) -> EvidenceReference:
    return EvidenceReference(item.laboratory_result_id, item.test_code, role, rationale)


def build_domain_reports(observations: list[LaboratoryObservationSnapshot]) -> list[DomainReaderReport]:
    by_code = _by_code(observations)
    reports: list[DomainReaderReport] = []

    glycemic = [by_code[c] for c in ("GLUCOSE_FASTING", "HBA1C", "INSULIN_FASTING") if c in by_code]
    if glycemic:
        evidence: list[EvidenceReference] = []
        for item in glycemic:
            if item.test_code in {"GLUCOSE_FASTING", "HBA1C"} and item.interpretation in {"high", "critical_high"}:
                evidence.append(_ref(item, HypothesisEvidenceRole.SUPPORTING, "Підвищений показник підтримує напрямок порушення глікемічної регуляції."))
            else:
                evidence.append(_ref(item, HypothesisEvidenceRole.CONTEXT, "Показник зберігається як контекст і не визначає діагноз самостійно."))
        reports.append(DomainReaderReport(
            specialty="endocrinology",
            observed_fact_ids=[x.laboratory_result_id for x in glycemic],
            candidate_hypotheses=[CandidateHypothesis(
                code="glycemic_dysregulation",
                title="Порушення глікемічної регуляції",
                evidence=evidence,
                missing_evidence=["repeat_fasting_glucose", "symptoms", "medications", "anthropometrics"],
                prohibited_conclusions=["diabetes_confirmed", "diabetes_type_determined"],
            )],
            questions=["Чи підтверджено глікемічні зміни повторним вимірюванням?", "Чи є ліки або гострі стани, що впливають на глюкозу?"],
            confidence="moderate",
            prohibited_conclusions=["Не встановлювати тип або тривалість діабету за цим профілем."],
        ))

    lipid = [by_code[c] for c in ("TRIGLYCERIDES", "LDL", "HDL", "TOTAL_CHOLESTEROL", "APOB") if c in by_code]
    if lipid:
        evidence = [_ref(x, HypothesisEvidenceRole.SUPPORTING if x.interpretation in {"high", "critical_high", "low", "critical_low"} else HypothesisEvidenceRole.CONTEXT, "Ліпідний показник враховується у кардіометаболічному профілі.") for x in lipid]
        reports.append(DomainReaderReport(
            specialty="lipidology_cardiometabolic",
            observed_fact_ids=[x.laboratory_result_id for x in lipid],
            candidate_hypotheses=[CandidateHypothesis(
                code="cardiometabolic_pattern",
                title="Кардіометаболічний профіль",
                evidence=evidence,
                missing_evidence=["LDL", "HDL", "non_HDL", "ApoB", "blood_pressure", "smoking_status"],
                prohibited_conclusions=["cardiovascular_risk_calculated", "metabolic_syndrome_confirmed"],
            )],
            questions=["Чи доступна повна ліпідограма?", "Які артеріальний тиск та антропометричні дані?"],
            confidence="low_to_moderate",
            prohibited_conclusions=["Не розраховувати серцево-судинний ризик без повних факторів."],
        ))

    hepatic = [by_code[c] for c in ("ALT", "AST", "GGT", "ALP", "BILIRUBIN_TOTAL") if c in by_code]
    if hepatic:
        evidence = [_ref(x, HypothesisEvidenceRole.SUPPORTING if x.interpretation in {"high", "critical_high", "low", "critical_low"} else HypothesisEvidenceRole.CONTEXT, "Печінковий маркер підтримує або обмежує печінкові гіпотези лише у контексті інших даних.") for x in hepatic]
        reports.append(DomainReaderReport(
            specialty="hepatology",
            observed_fact_ids=[x.laboratory_result_id for x in hepatic],
            candidate_hypotheses=[CandidateHypothesis(
                code="possible_hepatic_involvement",
                title="Можливий печінковий компонент",
                evidence=evidence,
                missing_evidence=["AST", "GGT", "bilirubin", "ALP", "platelets", "medications", "alcohol_history", "viral_hepatitis_screen"],
                prohibited_conclusions=["MASLD_confirmed", "liver_disease_cause_determined"],
            )],
            questions=["Чи є інші печінкові показники та дані про ліки/алкоголь?"],
            confidence="low",
            prohibited_conclusions=["Не встановлювати MASLD або етіологію лише за ALT."],
        ))

    renal = [by_code[c] for c in ("CREATININE", "EGFR", "UREA", "ALBUMIN_URINE") if c in by_code]
    if renal:
        evidence = []
        for x in renal:
            role = HypothesisEvidenceRole.CONTRADICTING if x.test_code == "CREATININE" and x.interpretation == "normal" else HypothesisEvidenceRole.CONTEXT
            rationale = "Нормальний креатинін не підтримує явне зниження фільтрації, але не виключає ранню CKD." if role == HypothesisEvidenceRole.CONTRADICTING else "Нирковий показник є частиною контексту."
            evidence.append(_ref(x, role, rationale))
        reports.append(DomainReaderReport(
            specialty="nephrology",
            observed_fact_ids=[x.laboratory_result_id for x in renal],
            candidate_hypotheses=[CandidateHypothesis(
                code="renal_context",
                title="Нирковий контекст",
                evidence=evidence,
                missing_evidence=["eGFR", "urine_ACR", "urinalysis", "blood_pressure"],
                prohibited_conclusions=["kidneys_healthy", "CKD_excluded"],
            )],
            questions=["Чи доступні eGFR та альбумін/креатинін сечі?"],
            confidence="low",
            prohibited_conclusions=["Не виключати ранню CKD за одним нормальним креатиніном."],
        ))

    return reports


def build_consensus(reports: list[DomainReaderReport]) -> dict:
    hypotheses = [h for r in reports for h in r.candidate_hypotheses]
    missing = sorted({item for h in hypotheses for item in h.missing_evidence})
    unsafe = sorted({item for h in hypotheses for item in h.prohibited_conclusions})
    fact_ids = sorted({item for r in reports for item in r.observed_fact_ids})
    return {
        "agreed_fact_ids": fact_ids,
        "shared_hypotheses": [{"code": h.code, "title": h.title, "status": h.status} for h in hypotheses],
        "specialty_disagreements": [],
        "unresolved_questions": sorted({q for r in reports for q in r.questions}),
        "missing_evidence": missing,
        "unsafe_conclusions": unsafe,
        "next_data_requests": missing,
    }
