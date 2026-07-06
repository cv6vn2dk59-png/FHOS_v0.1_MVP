"""15 високопріоритетних взаємодій, Phansalkar et al., 2013,
BMC Med Inform Decis Mak 13:65 (CC BY 2.0).

Факти передані власними словами (не текст статті) -- деталі методології
та обговорення дивись у самій статті, тут лише дані для роботи системи.
"""
from app.modules.drug_interactions.domain.entities import (
    DrugInteraction,
    InteractionSeverity,
)

PHANSALKAR_2013_INTERACTIONS: list[DrugInteraction] = [
    DrugInteraction(
        side_a=["amphetamine", "methamphetamine", "dextroamphetamine"],
        side_b=["tranylcypromine", "phenelzine", "isocarboxazid", "selegiline"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Похідні амфетаміну з інгібіторами МАО: ризик гіпертонічного кризу.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["atazanavir"],
        side_b=["omeprazole", "esomeprazole", "lansoprazole", "pantoprazole", "rabeprazole"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Атазанавір з інгібіторами протонної помпи: різке зниження всмоктування атазанавіру.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["febuxostat"],
        side_b=["azathioprine", "mercaptopurine"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Фебуксостат з азатіоприном/меркаптопурином: токсичне накопичення через пригнічення метаболізму.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["fluoxetine", "paroxetine", "citalopram", "escitalopram", "sertraline"],
        side_b=["tranylcypromine", "phenelzine", "isocarboxazid", "selegiline"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="СІЗЗС з інгібіторами МАО: ризик серотонінового синдрому.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["irinotecan"],
        side_b=["ketoconazole", "itraconazole", "voriconazole", "clarithromycin"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Іринотекан з сильними інгібіторами CYP3A4: підвищена токсичність іринотекану.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["meperidine", "methadone", "tapentadol", "fentanyl", "tramadol"],
        side_b=["tranylcypromine", "phenelzine", "isocarboxazid", "selegiline"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Наркотичні анальгетики з інгібіторами МАО: ризик серотонінового синдрому.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["amitriptyline", "nortriptyline", "imipramine", "clomipramine"],
        side_b=["selegiline"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Трициклічні антидепресанти з селегіліном: ризик серотонінового синдрому.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["amiodarone", "sotalol", "quinidine", "dofetilide"],
        side_b=["thioridazine", "pimozide", "droperidol"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Два препарати, що подовжують інтервал QT: сумарний ризик небезпечної аритмії.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["ramelteon"],
        side_b=["fluvoxamine"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Рамелтеон з флувоксаміном: різке підвищення концентрації рамелтеону.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["rifampin", "rifabutin", "rifapentine", "carbamazepine"],
        side_b=["indinavir", "saquinavir", "ritonavir", "nelfinavir", "atazanavir", "lopinavir"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Сильні індуктори CYP3A4 з інгібіторами протеази: втрата ефективності інгібітору протеази.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["simvastatin", "lovastatin"],
        side_b=["indinavir", "saquinavir", "ritonavir", "nelfinavir", "atazanavir", "lopinavir"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Певні статини з інгібіторами протеази: ризик рабдоміолізу.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["clarithromycin", "erythromycin", "ketoconazole", "itraconazole", "voriconazole"],
        side_b=["ergotamine", "dihydroergotamine"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Інгібітори CYP3A4 з препаратами ріжків: ризик тяжкого вазоспазму.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["tizanidine"],
        side_b=["ciprofloxacin"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Тизанідин з ципрофлоксацином: різке підвищення концентрації тизанідину, ризик гіпотензії.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["tranylcypromine"],
        side_b=["procarbazine"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Транілципромін з прокарбазином: сумарне пригнічення МАО.",
        knowledge_source_id="phansalkar_2013",
    ),
    DrugInteraction(
        side_a=["sumatriptan", "zolmitriptan", "rizatriptan"],
        side_b=["tranylcypromine", "phenelzine", "isocarboxazid", "selegiline"],
        severity=InteractionSeverity.CONTRAINDICATED,
        description="Триптани з інгібіторами МАО: ризик серотонінового синдрому.",
        knowledge_source_id="phansalkar_2013",
    ),
]
