from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dependencies import get_uow
from app.application.uow import UnitOfWork
from app.modules.clinical_reasoning.application.service import FamilyDataAccessService
from app.modules.clinical_reasoning.schemas.access import ConsentCreate, ConsentRead, SharedNodeRead, SharedNodeRequest

router = APIRouter(prefix="/clinical-reasoning", tags=["Clinical Reasoning"])


@router.post("/family-consents", response_model=ConsentRead, status_code=status.HTTP_201_CREATED)
def create_consent(data: ConsentCreate, uow: UnitOfWork = Depends(get_uow)):
    return FamilyDataAccessService(uow).create_consent(**data.model_dump())


@router.post("/family-consents/{consent_id}/revoke", response_model=ConsentRead)
def revoke_consent(consent_id: int, uow: UnitOfWork = Depends(get_uow)):
    try:
        return FamilyDataAccessService(uow).revoke_consent(consent_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/family/shared-nodes", response_model=SharedNodeRead)
def shared_nodes(data: SharedNodeRequest, uow: UnitOfWork = Depends(get_uow)):
    result = FamilyDataAccessService(uow).authorized_shared_nodes(data.actor_id, data.patient_ids, data.purpose_code)
    return {"shared_nodes": result}


from app.modules.clinical_reasoning.application.reasoning_service import ClinicalReasoningService
from app.modules.clinical_reasoning.schemas.reasoning import HypothesisExpansionRead, HypothesisExpansionRequest


@router.post("/hypothesis-expansion", response_model=HypothesisExpansionRead)
def hypothesis_expansion(data: HypothesisExpansionRequest, uow: UnitOfWork = Depends(get_uow)):
    try:
        hypotheses, review = ClinicalReasoningService(uow).expand_hypotheses(
            symptom_node_id=data.symptom_node_id,
            user_supplied_title=data.user_supplied_title,
            max_results=data.max_results,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "symptom_node_id": data.symptom_node_id,
        "hypotheses": [
            {
                "title": h.title,
                "mechanism": h.mechanism,
                "origin": h.origin.value,
                "evidence_level": h.evidence_level.value,
                "anatomical_source": h.anatomical_source,
                "body_system": h.body_system,
                "etiology_category": h.etiology_category,
                "verification_questions": h.verification_questions,
                "source_ids": h.source_ids,
                "status": h.status.value,
            }
            for h in hypotheses
        ],
        "devil_review": review,
    }


from app.modules.clinical_reasoning.application.laboratory_profile_service import (
    LaboratoryProfileService,
    LaboratoryResultsNotFoundError,
)
from app.modules.clinical_reasoning.schemas.laboratory_profile import (
    LaboratoryProfileRead,
    LaboratoryProfileRequest,
)


@router.post("/laboratory-profile", response_model=LaboratoryProfileRead)
def laboratory_profile(data: LaboratoryProfileRequest, uow: UnitOfWork = Depends(get_uow)):
    try:
        result = LaboratoryProfileService(uow).project(
            patient_id=data.patient_id,
            episode_id=data.episode_id,
            result_ids=data.result_ids,
            persist=data.persist,
        )
    except LaboratoryResultsNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "patient_id": result["patient_id"],
        "episode_id": result["episode_id"],
        "observations": [
            {
                **observation.__dict__,
                "observation_class": observation.observation_class.value,
                "evidence_role": observation.evidence_role.value,
            }
            for observation in result["observations"]
        ],
        "review_domains": [domain.__dict__ for domain in result["review_domains"]],
        "devil_review": result["devil_review"],
    }


from app.modules.clinical_reasoning.application.discrimination_service import BranchDiscriminationService
from app.modules.clinical_reasoning.domain.branch_discrimination import (
    BranchEvidenceEffect,
    EvidenceCandidate,
    EvidenceEffectType,
)
from app.modules.clinical_reasoning.domain.causality import ContextConstraint, ProvenanceReference
from app.modules.clinical_reasoning.domain.hypothesis_expansion import BranchStatus, HypothesisBranch
from app.modules.clinical_reasoning.schemas.discrimination import (
    BranchDiscriminationRead,
    BranchDiscriminationRequest,
)


@router.post("/branch-discrimination", response_model=BranchDiscriminationRead)
def branch_discrimination(data: BranchDiscriminationRequest):
    branches = [
        HypothesisBranch(
            id=item.id,
            case_id=item.case_id,
            title=item.title,
            description=item.description,
            root_trigger_ids=item.root_trigger_ids,
            causal_domain=item.causal_domain,
            branch_type=item.branch_type,
            node_ids=item.node_ids,
            edge_ids=item.edge_ids,
            supporting_fact_ids=item.supporting_fact_ids,
            contradicting_fact_ids=item.contradicting_fact_ids,
            neutral_fact_ids=item.neutral_fact_ids,
            missing_evidence_ids=item.missing_evidence_ids,
            evidence_strength=item.evidence_strength,
            confidence=item.confidence,
            status=BranchStatus(item.status),
            provenance=[ProvenanceReference(**p.model_dump()) for p in item.provenance],
            context_constraints=[ContextConstraint(**constraint) for constraint in item.context_constraints],
            safety_critical=item.safety_critical,
        )
        for item in data.branches
    ]
    candidates = [
        EvidenceCandidate(
            id=item.id,
            proposed_data_item=item.proposed_data_item,
            evidence_type=item.evidence_type,
            affected_branch_ids=item.affected_branch_ids,
            effects=[
                BranchEvidenceEffect(
                    branch_id=effect.branch_id,
                    possible_result=effect.possible_result,
                    effect_type=EvidenceEffectType(effect.effect_type),
                    expected_strength=effect.expected_strength,
                )
                for effect in item.effects
            ],
            evidence_reliability=item.evidence_reliability,
            context_applicability=item.context_applicability,
            clinical_utility=item.clinical_utility,
            safety_priority=item.safety_priority,
            time_sensitivity=item.time_sensitivity,
            invasiveness=item.invasiveness,
            cost_burden=item.cost_burden,
            actionability=item.actionability,
            provenance=[ProvenanceReference(**p.model_dump()) for p in item.provenance],
            limitations=item.limitations,
        )
        for item in data.candidates
    ]
    result = BranchDiscriminationService().evaluate(data.case_id, branches, candidates)
    return {
        "case_id": result.case_id,
        "comparisons": [comparison.__dict__ for comparison in result.comparisons],
        "ranked_candidates": [candidate.__dict__ for candidate in result.ranked_candidates],
        "unresolved_branch_pairs": [list(pair) for pair in result.unresolved_branch_pairs],
        "limitations": result.limitations,
        "warnings": result.warnings,
    }


from datetime import timedelta
from app.modules.clinical_reasoning.application.temporal_causality_service import TemporalCausalityService
from app.modules.clinical_reasoning.domain.temporal_causality import (
    CausalTemporalLink,
    ClinicalEventKind,
    ClinicalTimelineEvent,
    TemporalInterval,
    TemporalPrecision,
)
from app.modules.clinical_reasoning.schemas.temporal_causality import (
    TemporalCausalityRead,
    TemporalCausalityRequest,
)


@router.post("/temporal-causality", response_model=TemporalCausalityRead)
def temporal_causality(data: TemporalCausalityRequest):
    events = [
        ClinicalTimelineEvent(
            id=item.id,
            case_id=item.case_id,
            kind=ClinicalEventKind(item.kind),
            label=item.label,
            interval=TemporalInterval(
                earliest_start=item.interval.earliest_start,
                latest_start=item.interval.latest_start,
                earliest_end=item.interval.earliest_end,
                latest_end=item.interval.latest_end,
                precision=TemporalPrecision(item.interval.precision),
                timezone=item.interval.timezone,
            ),
            provenance=[ProvenanceReference(**p.model_dump()) for p in item.provenance],
            branch_ids=item.branch_ids,
            context=item.context,
        )
        for item in data.events
    ]
    links = [
        CausalTemporalLink(
            id=item.id,
            source_event_id=item.source_event_id,
            target_event_id=item.target_event_id,
            relation_type=item.relation_type,
            provenance=[ProvenanceReference(**p.model_dump()) for p in item.provenance],
            minimum_lag=timedelta(seconds=item.minimum_lag_seconds) if item.minimum_lag_seconds is not None else None,
            maximum_lag=timedelta(seconds=item.maximum_lag_seconds) if item.maximum_lag_seconds is not None else None,
            confidence=item.confidence,
        )
        for item in data.causal_links
    ]
    result = TemporalCausalityService().evaluate(data.case_id, events, links)
    return {
        "case_id": result.case_id,
        "ordered_event_ids": result.ordered_event_ids,
        "relations": [{**relation.__dict__, "relation_kind": relation.relation_kind.value} for relation in result.relations],
        "conflicts": [conflict.__dict__ for conflict in result.conflicts],
        "missing_evidence": [item.__dict__ for item in result.missing_evidence],
        "branch_assessments": [item.__dict__ for item in result.branch_assessments],
        "limitations": result.limitations,
        "warnings": result.warnings,
    }

from app.modules.clinical_reasoning.application.mechanistic_clustering_service import MechanisticClusteringService
from app.modules.clinical_reasoning.domain.mechanistic_clustering import BranchMechanisticProfile
from app.modules.clinical_reasoning.schemas.mechanistic_clustering import (
    MechanisticClusteringRead,
    MechanisticClusteringRequest,
)


@router.post("/mechanistic-clustering", response_model=MechanisticClusteringRead)
def mechanistic_clustering(data: MechanisticClusteringRequest):
    branches = [
        HypothesisBranch(
            id=item.id,
            case_id=item.case_id,
            title=item.title,
            description=item.description,
            root_trigger_ids=item.root_trigger_ids,
            causal_domain=item.causal_domain,
            branch_type=item.branch_type,
            node_ids=item.node_ids,
            edge_ids=item.edge_ids,
            supporting_fact_ids=item.supporting_fact_ids,
            contradicting_fact_ids=item.contradicting_fact_ids,
            neutral_fact_ids=item.neutral_fact_ids,
            missing_evidence_ids=item.missing_evidence_ids,
            evidence_strength=item.evidence_strength,
            confidence=item.confidence,
            status=BranchStatus(item.status),
            provenance=[ProvenanceReference(**p.model_dump()) for p in item.provenance],
            context_constraints=[ContextConstraint(**constraint) for constraint in item.context_constraints],
            safety_critical=item.safety_critical,
        )
        for item in data.branches
    ]
    profiles = [
        BranchMechanisticProfile(
            branch_id=item.branch_id,
            body_systems=item.body_systems,
            upstream_mechanism_ids=item.upstream_mechanism_ids,
            downstream_consequence_ids=item.downstream_consequence_ids,
            risk_factor_ids=item.risk_factor_ids,
            provenance=[ProvenanceReference(**p.model_dump()) for p in item.provenance],
            context_constraints=[ContextConstraint(**constraint) for constraint in item.context_constraints],
        )
        for item in data.profiles
    ]
    result = MechanisticClusteringService().evaluate(data.case_id, branches, profiles)
    return {
        "case_id": result.case_id,
        "clusters": [
            {
                **cluster.__dict__,
                "cluster_type": cluster.cluster_type.value,
                "provenance": [p.__dict__ for p in cluster.provenance],
                "context_constraints": [c.__dict__ for c in cluster.context_constraints],
            }
            for cluster in result.clusters
        ],
        "conflicts": [
            {**conflict.__dict__, "code": conflict.code.value}
            for conflict in result.conflicts
        ],
        "independent_branch_ids": result.independent_branch_ids,
        "limitations": result.limitations,
        "warnings": result.warnings,
    }

from app.modules.clinical_reasoning.application.dynamic_consilium_service import DynamicConsiliumService
from app.modules.clinical_reasoning.domain.dynamic_consilium import (
    BranchReview,
    ConsiliumRole,
    ReviewPosition,
)
from app.modules.clinical_reasoning.schemas.dynamic_consilium import (
    DynamicConsiliumRead,
    DynamicConsiliumRequest,
)


@router.post("/dynamic-consilium", response_model=DynamicConsiliumRead)
def dynamic_consilium(data: DynamicConsiliumRequest):
    branches = [
        HypothesisBranch(
            id=item.id,
            case_id=item.case_id,
            title=item.title,
            description=item.description,
            root_trigger_ids=item.root_trigger_ids,
            causal_domain=item.causal_domain,
            branch_type=item.branch_type,
            node_ids=item.node_ids,
            edge_ids=item.edge_ids,
            supporting_fact_ids=item.supporting_fact_ids,
            contradicting_fact_ids=item.contradicting_fact_ids,
            neutral_fact_ids=item.neutral_fact_ids,
            missing_evidence_ids=item.missing_evidence_ids,
            evidence_strength=item.evidence_strength,
            confidence=item.confidence,
            status=BranchStatus(item.status),
            provenance=[ProvenanceReference(**p.model_dump()) for p in item.provenance],
            context_constraints=[ContextConstraint(**constraint) for constraint in item.context_constraints],
            safety_critical=item.safety_critical,
        )
        for item in data.branches
    ]
    roles = [
        ConsiliumRole(
            code=item.code,
            title=item.title,
            focus_domains=item.focus_domains,
            devil_role=item.devil_role,
        )
        for item in data.roles
    ]
    reviews = [
        BranchReview(
            role_code=item.role_code,
            branch_id=item.branch_id,
            position=ReviewPosition(item.position),
            rationale=item.rationale,
            evidence_ids=item.evidence_ids,
            requested_evidence_ids=item.requested_evidence_ids,
            confidence=item.confidence,
            provenance=[ProvenanceReference(**p.model_dump()) for p in item.provenance],
        )
        for item in data.reviews
    ]
    result = DynamicConsiliumService().evaluate(
        data.case_id,
        branches,
        roles,
        reviews,
        data.cluster_branch_ids,
    )
    return {
        "case_id": result.case_id,
        "branch_reviews": [
            {
                **review.__dict__,
                "position": review.position.value,
                "provenance": [p.__dict__ for p in review.provenance],
            }
            for review in result.branch_reviews
        ],
        "consensus": {
            **result.consensus.__dict__,
            "minority_opinions": [
                {**item.__dict__, "position": item.position.value}
                for item in result.consensus.minority_opinions
            ],
        },
        "violations": [violation.__dict__ for violation in result.violations],
        "warnings": result.warnings,
        "limitations": result.limitations,
    }

from app.modules.clinical_reasoning.application.biomechanics_service import BiomechanicsService
from app.modules.clinical_reasoning.schemas.biomechanics import (
    BiomechanicsExpansionRead,
    BiomechanicsExpansionRequest,
)


@router.post("/biomechanics/hip-complex", response_model=BiomechanicsExpansionRead)
def biomechanics_hip_complex(data: BiomechanicsExpansionRequest):
    return BiomechanicsService().expand_hip_complex(
        data.case_id,
        [item.model_dump() for item in data.facts],
    )

from app.modules.clinical_reasoning.application.biomechanical_examination_service import (
    BiomechanicalExaminationService,
)
from app.modules.clinical_reasoning.schemas.biomechanical_examination import (
    BiomechanicalExaminationRead,
    BiomechanicalExaminationRequest,
)


@router.post("/biomechanics/examination", response_model=BiomechanicalExaminationRead)
def biomechanics_examination(data: BiomechanicalExaminationRequest):
    return BiomechanicalExaminationService().evaluate(
        data.case_id,
        [item.model_dump() for item in data.branches],
        [item.model_dump() for item in data.findings],
    )

from app.modules.clinical_reasoning.application.biomechanical_load_service import BiomechanicalLoadService
from app.modules.clinical_reasoning.schemas.biomechanical_load import BiomechanicalLoadRead, BiomechanicalLoadRequest

@router.post("/biomechanics/load-adaptation", response_model=BiomechanicalLoadRead)
def biomechanics_load_adaptation(data: BiomechanicalLoadRequest):
    return BiomechanicalLoadService().evaluate(
        data.case_id,
        [item.model_dump() for item in data.branches],
        [item.model_dump() for item in data.exposures],
        data.recovery.model_dump() if data.recovery else None,
        [item.model_dump() for item in data.responses],
    )
