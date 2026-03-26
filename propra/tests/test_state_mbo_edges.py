import importlib
import json
import re
from pathlib import Path

from propra.graph.builder import add_node, create_graph
from propra.graph.baybo_section_edges import section_6_abstandsflaechen_abstaende
from propra.graph.baybo_section_edges import section_58_genehmigungsfreistellung
from propra.graph.baybo_section_edges import section_57_verfahrensfreie_bauvorhaben_beseitigung_von_anla
from propra.graph.baybo_section_edges import section_59_vereinfachtes_baugenehmigungsverfahren
from propra.graph.baybo_section_edges import section_60_baugenehmigungsverfahren
from propra.graph.baybo_section_edges import section_61_bauvorlageberechtigung
from propra.graph.baybo_section_edges import section_61a_bauvorlageberechtigung_staatsangehoeriger_andere
from propra.graph.baybo_section_edges import section_61b_bauvorlageberechtigung_auswaertiger_dienstleiste
from propra.graph.baybo_section_edges import section_62_bautechnische_nachweise
from propra.graph.baybo_section_edges import section_62a_standsicherheitsnachweis
from propra.graph.baybo_section_edges import section_62b_brandschutznachweis
from propra.graph.baybo_section_edges import section_63_abweichungen
from propra.graph.baybo_section_edges import section_64_bauantrag_bauvorlagen
from propra.graph.baybo_section_edges import section_65_behandlung_des_bauantrags
from propra.graph.baybo_section_edges import section_66_beteiligung_des_nachbarn
from propra.graph.baybo_section_edges import section_66a_beteiligung_der_oeffentlichkeit
from propra.graph.baybo_section_edges import section_67_ersetzung_des_gemeindlichen_einvernehmens
from propra.graph.baybo_section_edges import section_68_baugenehmigung_genehmigungsfiktion_und_baubeginn
from propra.graph.baybo_section_edges import section_69_geltungsdauer_der_baugenehmigung_und_der_teilbau
from propra.graph.baybo_section_edges import section_70_teilbaugenehmigung
from propra.graph.baybo_section_edges import section_71_vorbescheid
from propra.graph.baybo_section_edges import section_72_genehmigung_fliegender_bauten
from propra.graph.baybo_section_edges import section_73_bauaufsichtliche_zustimmung
from propra.graph.baybo_section_edges import section_73a_typengenehmigung
from propra.graph.baybo_section_edges import section_75_einstellung_von_arbeiten
from propra.graph.baybo_section_edges import section_76_beseitigung_von_anlagen_nutzungsuntersagung
from propra.graph.baybo_section_edges import section_77_bauueberwachung
from propra.graph.baybo_section_edges import section_78_bauzustandsanzeigen_aufnahme_der_nutzung
from propra.graph.baybo_section_edges import section_80_rechtsverordnungen
from propra.graph.baybo_section_edges import section_80a_digitale_baugenehmigung_digitale_verfahren
from propra.graph.baybo_section_edges import section_81_oertliche_bauvorschriften
from propra.graph.baybo_section_edges import section_81a_technische_baubestimmungen
from propra.graph.parse_inventory import parse_inventory
from propra.graph.schema import Node
from propra.graph.state_mbo_edges import state_edges_from_mbo

_CURATED_STATE_MODULES = {
    "BayBO": "propra.graph.baybo_section_edges",
    "NBauO": "propra.graph.nbauo_section_edges",
    "BauO_BE": "propra.graph.bauo_be_section_edges",
    "BauO_HE": "propra.graph.bauo_he_section_edges",
    "BauO_NRW": "propra.graph.bauo_nrw_section_edges",
    "BauO_LSA": "propra.graph.bauo_lsa_section_edges",
    "BauO_MV": "propra.graph.bauo_mv_section_edges",
    "HBauO": "propra.graph.hbauo_section_edges",
    "LBO_SH": "propra.graph.lbo_sh_section_edges",
    "LBO_SL": "propra.graph.lbo_sl_section_edges",
    "LBauO_RLP": "propra.graph.lbauo_rlp_section_edges",
    "SaechsBO": "propra.graph.saechsbo_section_edges",
    "ThuerBO": "propra.graph.thuerbo_section_edges",
    "BW_LBO": "propra.graph.bw_lbo_section_edges",
    "BremLBO": "propra.graph.bremlbo_section_edges",
}


def test_state_edges_from_mbo_maps_existing_state_nodes(tmp_path):
    G = create_graph()

    for node in [
        Node(
            id="Test_§1",
            type="anwendungsbereich",
            jurisdiction="DE-XX",
            source_paragraph="§1 Test",
            text="§ 1 Test",
        ),
        Node(
            id="Test_§1_2.1",
            type="anwendungsbereich",
            jurisdiction="DE-XX",
            source_paragraph="§1 Test",
            text="Lead rule",
        ),
        Node(
            id="Test_§1_2.2",
            type="anwendungsbereich",
            jurisdiction="DE-XX",
            source_paragraph="§1 Test",
            text="List item",
        ),
    ]:
        add_node(G, node)

    mapping_path = tmp_path / "Test_mbo_mapping.json"
    mapping_path.write_text(
        json.dumps(
            {
                "state": "Test",
                "mapping": {"1": "1"},
                "review": [],
                "unmatched": [],
            }
        ),
        encoding="utf-8",
    )

    edges = state_edges_from_mbo(G, prefix="Test_", mapping_path=mapping_path)
    as_triples = {(e.source, e.target, e.relation) for e in edges}

    assert ("Test_§1_2.1", "Test_§1", "supplements") in as_triples
    assert ("Test_§1_2.2", "Test_§1_2.1", "sub_item_of") in as_triples


def test_baybo_section_6_curates_list_structure_and_state_specific_edges():
    edges = section_6_abstandsflaechen_abstaende()
    as_triples = {(e.source, e.target, e.relation) for e in edges}

    assert ("BayBO_§6_1.4", "BayBO_§6_1.3", "sub_item_of") in as_triples
    assert ("BayBO_§6_1.5", "BayBO_§6_1.3", "sub_item_of") in as_triples
    assert ("BayBO_§6_1.6", "BayBO_§6_1.3", "sub_item_of") in as_triples
    assert ("BayBO_§6_1.7", "BayBO_§6_1.3", "sub_item_of") in as_triples
    assert ("BayBO_§6_5.3", "BayBO_§6_5.2", "supplements") in as_triples
    assert ("BayBO_§6_5.4", "BayBO_§6_5.1", "exception_of") in as_triples
    assert ("BayBO_§6_5.5", "BayBO_§6_5.4", "exception_of") in as_triples
    assert ("BayBO_§6_5.9", "BayBO_§6_5.8", "sub_item_of") in as_triples
    assert ("BayBO_§6_5.10", "BayBO_§6_5.8", "sub_item_of") in as_triples
    assert ("BayBO_§6_3.3", "BayBO_§2_3.2", "references") in as_triples
    assert ("BayBO_§6_3.3", "BayBO_§2_3.3", "references") in as_triples
    assert ("BayBO_§6_5.4", "BayBO_§2_3.2", "references") in as_triples
    assert ("BayBO_§6_5.4", "BayBO_§2_3.3", "references") in as_triples
    assert ("BayBO_§6_5.4", "BayBO_§2_3.4", "references") in as_triples

    assert ("BayBO_§6_1.4", "BayBO_§6_1.1", "exception_of") not in as_triples
    assert ("BayBO_§6_1.5", "BayBO_§6_1.4", "sub_item_of") not in as_triples
    assert ("BayBO_§6_1.6", "BayBO_§6_1.4", "sub_item_of") not in as_triples
    assert ("BayBO_§6_5.3", "BayBO_§6_5.1", "exception_of") not in as_triples
    assert ("BayBO_§6_5.3", "BayBO_§6_5.2", "exception_of") not in as_triples
    assert ("BayBO_§6_5.3", "BayBO_§2_3.1", "references") not in as_triples
    assert ("BayBO_§6_5.4", "BayBO_§81", "references") not in as_triples


def test_baybo_section_72_curates_workflow_structure():
    edges = section_72_genehmigung_fliegender_bauten()
    as_triples = {(e.source, e.target, e.relation) for e in edges}

    assert ("BayBO_§72_1.2", "BayBO_§72_1.1", "exception_of") in as_triples
    assert ("BayBO_§72_2.2", "BayBO_§72_2.1", "supplements") in as_triples
    assert ("BayBO_§72_2.3", "BayBO_§72_2.1", "supplements") in as_triples
    assert ("BayBO_§72_2.4", "BayBO_§72_2.1", "supplements") in as_triples
    assert ("BayBO_§72_3.1", "BayBO_§72_2.1", "exception_of") in as_triples
    assert ("BayBO_§72_4.1", "BayBO_§72_3.1", "supplements") in as_triples
    assert ("BayBO_§72_4.1", "BayBO_§72_3.5", "references") in as_triples
    assert ("BayBO_§72_4.1", "BayBO_§72_3.8", "references") in as_triples
    assert ("BayBO_§72_5.1", "BayBO_§72_2.1", "supplements") in as_triples
    assert ("BayBO_§72_5.2", "BayBO_§72_5.1", "supplements") in as_triples
    assert ("BayBO_§72_5.3", "BayBO_§72_5.1", "supplements") in as_triples
    assert ("BayBO_§72_5.4", "BayBO_§72_5.3", "sub_item_of") in as_triples
    assert ("BayBO_§72_5.8", "BayBO_§72_5.3", "sub_item_of") in as_triples
    assert ("BayBO_§72_5.9", "BayBO_§72_5.8", "supplements") in as_triples
    assert ("BayBO_§72_6.1", "BayBO_§72_2.1", "supplements") in as_triples
    assert ("BayBO_§72_6.2", "BayBO_§72_6.1", "supplements") in as_triples
    assert ("BayBO_§72_6.3", "BayBO_§72_6.2", "sub_item_of") in as_triples
    assert ("BayBO_§72_6.4", "BayBO_§72_6.2", "sub_item_of") in as_triples
    assert ("BayBO_§72_7.1", "BayBO_§72_2.1", "exception_of") in as_triples
    assert ("BayBO_§72_7.1", "BayBO_§72_6.1", "exception_of") in as_triples
    assert ("BayBO_§72_7.2", "BayBO_§72_7.1", "supplements") in as_triples

    assert ("BayBO_§72_1.2", "BayBO_§72_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§72_5.4", "BayBO_§72_5.1", "sub_item_of") not in as_triples
    assert ("BayBO_§72_5.9", "BayBO_§72_5.1", "sub_item_of") not in as_triples
    assert ("BayBO_§72_6.2", "BayBO_§72_6.1", "sub_item_of") not in as_triples
    assert ("BayBO_§72_6.3", "BayBO_§72_6.1", "sub_item_of") not in as_triples
    assert ("BayBO_§72_7.2", "BayBO_§72_7.1", "sub_item_of") not in as_triples


def test_baybo_section_81_curates_local_bylaw_exceptions():
    edges = section_81_oertliche_bauvorschriften()
    as_triples = {(e.source, e.target, e.relation) for e in edges}

    assert ("BayBO_§81_2.1", "BayBO_§81_1.1", "supplements") in as_triples
    assert ("BayBO_§81_2.2", "BayBO_§81_2.1", "supplements") in as_triples
    assert ("BayBO_§81_3.2", "BayBO_§81_3.1", "supplements") in as_triples
    assert ("BayBO_§81_3.3", "BayBO_§81_3.2", "supplements") in as_triples
    assert ("BayBO_§81_4.1", "BayBO_§81_1.1", "exception_of") in as_triples
    assert ("BayBO_§81_4.1", "BayBO_§81_2.1", "exception_of") in as_triples
    assert ("BayBO_§81_4.1", "BayBO_§81_3.1", "exception_of") in as_triples
    assert ("BayBO_§81_5.1", "BayBO_§81_1.3", "exception_of") in as_triples
    assert ("BayBO_§81_5.1", "BayBO_§81_1.4", "exception_of") in as_triples
    assert ("BayBO_§81_5.1", "BayBO_§81_1.5", "exception_of") in as_triples
    assert ("BayBO_§81_5.1", "BayBO_§81_1.6", "exception_of") in as_triples
    assert ("BayBO_§81_5.1", "BayBO_§81_1.7", "exception_of") in as_triples
    assert ("BayBO_§81_5.1", "BayBO_§57_1.18", "references") in as_triples

    assert ("BayBO_§81_2.2", "BayBO_§81_2.1", "sub_item_of") not in as_triples
    assert ("BayBO_§81_3.2", "BayBO_§81_3.1", "sub_item_of") not in as_triples
    assert ("BayBO_§81_3.3", "BayBO_§81_3.1", "sub_item_of") not in as_triples


def test_baybo_procedure_cluster_curates_sentence_level_links():
    sections = []
    sections.extend(section_58_genehmigungsfreistellung())
    sections.extend(section_63_abweichungen())
    sections.extend(section_64_bauantrag_bauvorlagen())
    sections.extend(section_65_behandlung_des_bauantrags())
    sections.extend(section_66_beteiligung_des_nachbarn())
    sections.extend(section_67_ersetzung_des_gemeindlichen_einvernehmens())
    sections.extend(section_68_baugenehmigung_genehmigungsfiktion_und_baubeginn())
    sections.extend(section_69_geltungsdauer_der_baugenehmigung_und_der_teilbau())
    as_triples = {(e.source, e.target, e.relation) for e in sections}

    assert ("BayBO_§58_2.3", "BayBO_§58_2.2", "exception_of") in as_triples
    assert ("BayBO_§58_2.6", "BayBO_§58_2.5", "exception_of") in as_triples
    assert ("BayBO_§58_3.1", "BayBO_§58_1.6", "supplements") in as_triples
    assert ("BayBO_§63_2.2", "BayBO_§63_2.1", "supplements") in as_triples
    assert ("BayBO_§64_1.2", "BayBO_§64_1.1", "supplements") in as_triples
    assert ("BayBO_§64_2.2", "BayBO_§64_2.1", "supplements") in as_triples
    assert ("BayBO_§65_1.3", "BayBO_§65_1.2", "supplements") in as_triples
    assert ("BayBO_§66_2.4", "BayBO_§66_2.3", "supplements") in as_triples
    assert ("BayBO_§66_2.5", "BayBO_§66_2.4", "supplements") in as_triples
    assert ("BayBO_§67_3.2", "BayBO_§67_3.1", "supplements") in as_triples
    assert ("BayBO_§68_8.1", "BayBO_§68_6.4", "supplements") in as_triples
    assert ("BayBO_§69_2.2", "BayBO_§69_2.1", "supplements") in as_triples

    assert ("BayBO_§64_1.2", "BayBO_§64_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§65_1.3", "BayBO_§65_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§66_2.4", "BayBO_§66_2.1", "sub_item_of") not in as_triples
    assert ("BayBO_§67_3.2", "BayBO_§67_3.1", "sub_item_of") not in as_triples
    assert ("BayBO_§68_7.2", "BayBO_§68_7.1", "sub_item_of") not in as_triples
    assert ("BayBO_§69_2.2", "BayBO_§69_2.1", "sub_item_of") not in as_triples


def test_baybo_section_57_61_62_add_precise_notice_and_follow_on_links():
    sections = []
    sections.extend(section_57_verfahrensfreie_bauvorhaben_beseitigung_von_anla())
    sections.extend(section_61_bauvorlageberechtigung())
    sections.extend(section_62_bautechnische_nachweise())
    as_triples = {(e.source, e.target, e.relation) for e in sections}

    assert ("BayBO_§57_7.1", "BayBO_§57_1.19", "supplements") in as_triples
    assert ("BayBO_§57_7.1", "BayBO_§57_4.2", "supplements") in as_triples
    assert ("BayBO_§61_6.2", "BayBO_§61_6.1", "supplements") in as_triples
    assert ("BayBO_§61_5.1", "BayBO_§61_2.3", "references") in as_triples
    assert ("BayBO_§62_1.2", "BayBO_§62_1.1", "supplements") in as_triples
    assert ("BayBO_§62_1.3", "BayBO_§62_1.1", "supplements") in as_triples
    assert ("BayBO_§62_3.2", "BayBO_§62_3.1", "supplements") in as_triples
    assert ("BayBO_§62_3.3", "BayBO_§62_3.1", "supplements") in as_triples
    assert ("BayBO_§62_3.4", "BayBO_§62_3.1", "supplements") in as_triples

    assert ("BayBO_§61_6.2", "BayBO_§61_6.1", "sub_item_of") not in as_triples
    assert ("BayBO_§62_1.2", "BayBO_§62_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§62_1.3", "BayBO_§62_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§62_3.2", "BayBO_§62_3.1", "sub_item_of") not in as_triples


def test_baybo_qualification_and_proof_cluster_curates_split_sentences():
    sections = []
    sections.extend(section_61a_bauvorlageberechtigung_staatsangehoeriger_andere())
    sections.extend(section_61b_bauvorlageberechtigung_auswaertiger_dienstleiste())
    sections.extend(section_62a_standsicherheitsnachweis())
    sections.extend(section_62b_brandschutznachweis())
    as_triples = {(e.source, e.target, e.relation) for e in sections}

    assert ("BayBO_§61a_1.2", "BayBO_§61a_1.1", "supplements") in as_triples
    assert ("BayBO_§61a_1.1", "BayBO_§61_5.2", "references") in as_triples
    assert ("BayBO_§61a_2.5", "BayBO_§61a_2.4", "sub_item_of") in as_triples
    assert ("BayBO_§61a_3.2", "BayBO_§61a_3.1", "supplements") in as_triples
    assert ("BayBO_§61a_3.3", "BayBO_§61a_3.2", "supplements") in as_triples
    assert ("BayBO_§61a_4.2", "BayBO_§61a_4.1", "supplements") in as_triples
    assert ("BayBO_§61a_4.3", "BayBO_§61a_4.2", "sub_item_of") in as_triples
    assert ("BayBO_§61a_5.3", "BayBO_§61a_5.1", "supplements") in as_triples
    assert ("BayBO_§61a_8.1", "BayBO_§61_7.1", "references") in as_triples
    assert ("BayBO_§61b_2.2", "BayBO_§61b_2.1", "exception_of") in as_triples
    assert ("BayBO_§61b_2.4", "BayBO_§61b_2.3", "sub_item_of") in as_triples
    assert ("BayBO_§61b_3.3", "BayBO_§61b_3.1", "exception_of") in as_triples
    assert ("BayBO_§61b_6.2", "BayBO_§61b_6.1", "supplements") in as_triples
    assert ("BayBO_§62a_2.4", "BayBO_§62a_2.1", "exception_of") in as_triples
    assert ("BayBO_§62a_2.5", "BayBO_§62a_2.1", "exception_of") in as_triples
    assert ("BayBO_§62b_1.2", "BayBO_§61_1.1", "references") in as_triples
    assert ("BayBO_§62b_2.5", "BayBO_§62b_2.4", "supplements") in as_triples

    assert ("BayBO_§61a_1.2", "BayBO_§61a_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§61a_2.5", "BayBO_§61a_2.1", "sub_item_of") not in as_triples
    assert ("BayBO_§61a_4.3", "BayBO_§61a_4.1", "sub_item_of") not in as_triples
    assert ("BayBO_§61b_2.2", "BayBO_§61b_2.1", "sub_item_of") not in as_triples
    assert ("BayBO_§61b_2.4", "BayBO_§61b_2.1", "sub_item_of") not in as_triples
    assert ("BayBO_§62a_2.4", "BayBO_§62a_2.1", "sub_item_of") not in as_triples
    assert ("BayBO_§62b_2.5", "BayBO_§62b_2.1", "sub_item_of") not in as_triples


def _assert_curated_edge_ids_exist(state: str, module_name: str) -> None:
    inventory_path = Path(f"propra/data/node inventory/{state}_node_inventory_fine.md")
    prefix = f"{state}_"
    nodes = parse_inventory(inventory_path, node_prefix=prefix, source_suffix=state)
    valid_ids = {node.id for node in nodes}
    headings = re.findall(r"^###\s+(§[^—\n]+?)(?:\s*—|\s*$)", inventory_path.read_text(encoding="utf-8"), re.MULTILINE)
    for heading in headings:
        normalized = re.sub(r"(§§?)\s+", r"\1", heading.strip())
        valid_ids.add(f"{prefix}{normalized}")

    module = importlib.import_module(module_name)
    for name in dir(module):
        if not name.startswith("section_"):
            continue
        section_fn = getattr(module, name)
        if not callable(section_fn):
            continue
        for edge in section_fn():
            assert edge.source in valid_ids, f"{name}: missing source {edge.source}"
            assert edge.target in valid_ids, f"{name}: missing target {edge.target}"


def test_curated_state_modules_match_current_fine_inventories():
    for state, module_name in _CURATED_STATE_MODULES.items():
        _assert_curated_edge_ids_exist(state, module_name)


def test_baybo_later_procedure_cluster_curates_follow_on_rules():
    sections = []
    sections.extend(section_70_teilbaugenehmigung())
    sections.extend(section_71_vorbescheid())
    sections.extend(section_73_bauaufsichtliche_zustimmung())
    sections.extend(section_73a_typengenehmigung())
    sections.extend(section_75_einstellung_von_arbeiten())
    sections.extend(section_76_beseitigung_von_anlagen_nutzungsuntersagung())
    as_triples = {(e.source, e.target, e.relation) for e in sections}

    assert ("BayBO_§70_1.2", "BayBO_§70_1.1", "supplements") in as_triples
    assert ("BayBO_§70_1.2", "BayBO_§67", "references") in as_triples
    assert ("BayBO_§71_1.2", "BayBO_§71_1.1", "supplements") in as_triples
    assert ("BayBO_§71_1.3", "BayBO_§71_1.2", "supplements") in as_triples
    assert ("BayBO_§71_1.4", "BayBO_§69_2.2", "references") in as_triples
    assert ("BayBO_§73_1.4", "BayBO_§73_1.3", "sub_item_of") in as_triples
    assert ("BayBO_§73_2.2", "BayBO_§73_2.1", "supplements") in as_triples
    assert ("BayBO_§73_2.4", "BayBO_§73_2.2", "sub_item_of") in as_triples
    assert ("BayBO_§73_2.4", "BayBO_§66a_2.1", "references") in as_triples
    assert ("BayBO_§73_3.2", "BayBO_§73_3.1", "supplements") in as_triples
    assert ("BayBO_§73_5.2", "BayBO_§73_5.1", "supplements") in as_triples
    assert ("BayBO_§73a_1.2", "BayBO_§73a_1.1", "supplements") in as_triples
    assert ("BayBO_§73a_2.3", "BayBO_§63_1.1", "references") in as_triples
    assert ("BayBO_§73a_6.1", "BayBO_§81_1.2", "exception_of") in as_triples
    assert ("BayBO_§75_1.2", "BayBO_§75_1.1", "supplements") in as_triples
    assert ("BayBO_§75_1.3", "BayBO_§75_1.2", "sub_item_of") in as_triples
    assert ("BayBO_§75_2.1", "BayBO_§75_1.1", "supplements") in as_triples
    assert ("BayBO_§76_1.2", "BayBO_§76_1.1", "supplements") in as_triples
    assert ("BayBO_§76_1.3", "BayBO_§76_1.1", "supplements") in as_triples

    assert ("BayBO_§70_1.2", "BayBO_§70_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§71_1.2", "BayBO_§71_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§71_1.4", "BayBO_§71_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§73_1.4", "BayBO_§73_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§73_2.4", "BayBO_§73_2.1", "sub_item_of") not in as_triples
    assert ("BayBO_§73_4.2", "BayBO_§73_4.1", "sub_item_of") not in as_triples
    assert ("BayBO_§73a_1.2", "BayBO_§73a_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§73a_6.2", "BayBO_§73a_6.1", "sub_item_of") not in as_triples
    assert ("BayBO_§75_1.2", "BayBO_§75_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§75_1.3", "BayBO_§75_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§76_1.2", "BayBO_§76_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§76_1.4", "BayBO_§76_1.1", "sub_item_of") not in as_triples


def test_baybo_supervision_and_rulemaking_cluster_curates_nested_lists():
    sections = []
    sections.extend(section_77_bauueberwachung())
    sections.extend(section_78_bauzustandsanzeigen_aufnahme_der_nutzung())
    sections.extend(section_80_rechtsverordnungen())
    sections.extend(section_80a_digitale_baugenehmigung_digitale_verfahren())
    sections.extend(section_81a_technische_baubestimmungen())
    as_triples = {(e.source, e.target, e.relation) for e in sections}

    assert ("BayBO_§77_3.2", "BayBO_§77_3.1", "exception_of") in as_triples
    assert ("BayBO_§77_3.3", "BayBO_§77_3.2", "sub_item_of") in as_triples
    assert ("BayBO_§77_2.2", "BayBO_§62a_2.1", "references") in as_triples
    assert ("BayBO_§77_2.3", "BayBO_§62b_2.1", "references") in as_triples
    assert ("BayBO_§78_1.2", "BayBO_§78_1.1", "supplements") in as_triples
    assert ("BayBO_§78_2.2", "BayBO_§78_2.1", "supplements") in as_triples
    assert ("BayBO_§78_2.3", "BayBO_§78_2.2", "sub_item_of") in as_triples
    assert ("BayBO_§78_2.4", "BayBO_§62b_2.1", "references") in as_triples
    assert ("BayBO_§80_2.9", "BayBO_§80_2.8", "sub_item_of") in as_triples
    assert ("BayBO_§80_2.11", "BayBO_§62_3.1", "references") in as_triples
    assert ("BayBO_§80_3.2", "BayBO_§80_3.1", "supplements") in as_triples
    assert ("BayBO_§80_3.3", "BayBO_§80_3.2", "sub_item_of") in as_triples
    assert ("BayBO_§80_6.2", "BayBO_§80_6.1", "supplements") in as_triples
    assert ("BayBO_§80_6.3", "BayBO_§80_6.1", "supplements") in as_triples
    assert ("BayBO_§80a_1.2", "BayBO_§80a_1.1", "supplements") in as_triples
    assert ("BayBO_§80a_1.3", "BayBO_§80a_1.1", "supplements") in as_triples
    assert ("BayBO_§81a_1.2", "BayBO_§81a_1.1", "exception_of") in as_triples
    assert ("BayBO_§81a_1.3", "BayBO_§81a_1.1", "supplements") in as_triples

    assert ("BayBO_§77_3.2", "BayBO_§77_3.1", "sub_item_of") not in as_triples
    assert ("BayBO_§77_3.3", "BayBO_§77_3.1", "sub_item_of") not in as_triples
    assert ("BayBO_§78_1.2", "BayBO_§78_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§78_2.3", "BayBO_§78_2.1", "sub_item_of") not in as_triples
    assert ("BayBO_§78_3.2", "BayBO_§78_3.1", "sub_item_of") not in as_triples
    assert ("BayBO_§80_2.9", "BayBO_§80_2.1", "sub_item_of") not in as_triples
    assert ("BayBO_§80_3.2", "BayBO_§80_3.1", "sub_item_of") not in as_triples
    assert ("BayBO_§80_6.2", "BayBO_§80_6.1", "sub_item_of") not in as_triples
    assert ("BayBO_§80a_1.2", "BayBO_§80a_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§81a_1.2", "BayBO_§81a_1.1", "sub_item_of") not in as_triples


def test_baybo_review_and_publicity_sections_add_precise_cross_links():
    sections = []
    sections.extend(section_59_vereinfachtes_baugenehmigungsverfahren())
    sections.extend(section_60_baugenehmigungsverfahren())
    sections.extend(section_66a_beteiligung_der_oeffentlichkeit())
    as_triples = {(e.source, e.target, e.relation) for e in sections}

    assert ("BayBO_§59_1.2", "BayBO_§6", "references") in as_triples
    assert ("BayBO_§59_1.2", "BayBO_§81_1.1", "references") in as_triples
    assert ("BayBO_§59_1.3", "BayBO_§63_1.1", "references") in as_triples
    assert ("BayBO_§59_1.4", "BayBO_§62a", "references") in as_triples
    assert ("BayBO_§60_1.4", "BayBO_§62b", "references") in as_triples
    assert ("BayBO_§66a_1.2", "BayBO_§66a_1.1", "supplements") in as_triples
    assert ("BayBO_§66a_1.6", "BayBO_§66a_1.1", "supplements") in as_triples
    assert ("BayBO_§66a_1.7", "BayBO_§66a_1.6", "sub_item_of") in as_triples
    assert ("BayBO_§66a_2.4", "BayBO_§66a_2.3", "sub_item_of") in as_triples
    assert ("BayBO_§66a_1.5", "BayBO_§66_1.1", "references") in as_triples
    assert ("BayBO_§66a_2.2", "BayBO_§58_1.1", "references") in as_triples

    assert ("BayBO_§66a_1.2", "BayBO_§66a_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§66a_1.7", "BayBO_§66a_1.1", "sub_item_of") not in as_triples
    assert ("BayBO_§66a_2.4", "BayBO_§66a_2.1", "sub_item_of") not in as_triples
