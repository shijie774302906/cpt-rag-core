"""Evidence-coverage arithmetic over externally validated evidence identities."""
from collections import Counter
from typing import Any, Mapping, Sequence

class BenchmarkError(ValueError):
    pass

LABELS = {"relevant", "condition_mismatch", "topic_only", "irrelevant", "unjudged"}
PARENT_EQUAL_PROFILE = "equal_parent_needs_fractional_children_v1"

def _ids(values: Any, label: str, *, empty: bool=False) -> list[str]:
    if not isinstance(values, list) or (not values and (not empty)):
        raise BenchmarkError(f"{label} requires a {('possibly empty' if empty else 'nonempty')} list")
    if any((not isinstance(v, str) or not v.strip() for v in values)):
        raise BenchmarkError(f'{label} requires nonempty string IDs')
    return values


def score_evidence_points(rubric: Mapping[str, Any], returned_unit_ids: Sequence[str], *, unit_labels: Mapping[str, str] | None=None) -> dict[str, Any]:
    query_id = rubric.get('query_id')
    if not isinstance(query_id, str) or not query_id.strip():
        raise BenchmarkError('query_id required')
    pool = rubric.get('answer_pool')
    if pool not in {'provisional', 'closed'}:
        raise BenchmarkError('explicit provisional/closed answer_pool required')
    if isinstance(returned_unit_ids, (str, bytes)):
        raise BenchmarkError('returned units must be a sequence of IDs, not text')
    positions = _ids(list(returned_unit_ids), 'returned units', empty=True)
    returned = set(positions)
    labels = dict(unit_labels or {})
    if not set(labels) <= returned or any((v not in LABELS for v in labels.values())):
        raise BenchmarkError('labels must classify returned units with known statuses')
    groups = rubric.get('groups')
    if not isinstance(groups, list) or not groups:
        raise BenchmarkError('nonempty answer groups required')
    results = []
    seen_groups: set[str] = set()
    matched_units: set[str] = set()
    for group in groups:
        if not isinstance(group, Mapping):
            raise BenchmarkError('group must be an object')
        gid = group.get('group_id')
        if not isinstance(gid, str) or not gid.strip() or gid in seen_groups:
            raise BenchmarkError('unique nonempty group_id required')
        seen_groups.add(gid)
        points = _ids(group.get('points'), 'points')
        if len(points) != len(set(points)):
            raise BenchmarkError('duplicate point ID')
        options = group.get('evidence_options')
        if not isinstance(options, list) or not options:
            raise BenchmarkError('nonempty compatible evidence options required')
        option_results = []
        option_ids: set[str] = set()
        for option in options:
            if not isinstance(option, Mapping):
                raise BenchmarkError('option must be an object')
            oid = option.get('option_id')
            if not isinstance(oid, str) or not oid.strip() or oid in option_ids:
                raise BenchmarkError('unique option_id required within group')
            option_ids.add(oid)
            supports = option.get('supports')
            if not isinstance(supports, Mapping) or set(supports) != set(points):
                raise BenchmarkError('option support keys must equal required points')
            hit = []
            for point in points:
                clauses = supports[point]
                if not isinstance(clauses, list) or not clauses:
                    raise BenchmarkError('each point requires alternative support clauses')
                satisfied = False
                for clause in clauses:
                    needed = set(_ids(clause, 'support clause'))
                    if needed <= returned:
                        if any((labels.get(u, 'relevant') != 'relevant' for u in needed)):
                            raise BenchmarkError('positive support contradicts material judgement')
                        matched_units.update(needed)
                        satisfied = True
                if satisfied:
                    hit.append(point)
            option_results.append({'option_id': oid, 'hit_points': sorted(hit)})
        best = sorted(option_results, key=lambda r: (-len(r['hit_points']), r['option_id']))[0]
        count = len(best['hit_points'])
        results.append({'group_id': gid, 'required_points': len(points), 'matched_points': count, 'coverage': count / len(points), 'complete': count == len(points), 'best_option': best['option_id'], 'options': option_results})
    material = Counter({label: 0 for label in sorted(LABELS)})
    for unit in returned:
        material[labels.get(unit, 'relevant' if unit in matched_units else 'unjudged')] += 1
    return {'query_id': query_id, 'answer_pool': pool, 'scope': 'reviewed_reference_pool_only', 'semantic_judgement_performed': False, 'budget_verified': False, 'reference_pool_coverage_percent': 100 * sum((r['coverage'] for r in results)) / len(results), 'complete_group_fraction': sum((r['complete'] for r in results)) / len(results), 'groups': results, 'returned_positions': len(positions), 'unique_returned_units': len(returned), 'duplicate_positions': len(positions) - len(returned), 'material_counts': dict(material), 'material_fractions': {k: v / len(returned) if returned else None for k, v in material.items()}, 'material_denominator': 'unique_common_evaluation_units_not_method_chunks'}


def score_component_evidence(rubric, returned_unit_ids, *, weight_profile):
    if weight_profile != PARENT_EQUAL_PROFILE:
        raise BenchmarkError('explicit supported component weight profile required')
    groups = rubric.get('groups')
    if not isinstance(groups, list) or not groups:
        raise BenchmarkError('nonempty answer groups required')
    if isinstance(returned_unit_ids, (str, bytes)):
        raise BenchmarkError('returned units must be a sequence of IDs, not text')
    positions = _ids(list(returned_unit_ids), 'returned units', empty=True)
    results, seen_groups = ([], set())
    for group in groups:
        gid = group.get('group_id')
        if not isinstance(gid, str) or not gid.strip() or gid in seen_groups:
            raise BenchmarkError('unique nonempty group_id required')
        seen_groups.add(gid)
        parents = _ids(group.get('points'), 'parent needs')
        if len(parents) != len(set(parents)):
            raise BenchmarkError('duplicate parent need')
        options = group.get('evidence_options')
        if not isinstance(options, list) or not options:
            raise BenchmarkError('nonempty compatible evidence options required')
        evaluated, seen_options = ([], set())
        for option in options:
            oid = option.get('option_id')
            if not isinstance(oid, str) or not oid.strip() or oid in seen_options:
                raise BenchmarkError('unique option_id required')
            seen_options.add(oid)
            components = option.get('components')
            if not isinstance(components, Mapping) or set(components) != set(parents):
                raise BenchmarkError('component keys must equal parent needs')
            adapted = []
            for parent in parents:
                children = components[parent]
                if not isinstance(children, list) or not children:
                    raise BenchmarkError('nonempty components required per parent')
                child_ids = _ids([c.get('component_id') for c in children], 'component IDs')
                if len(child_ids) != len(set(child_ids)):
                    raise BenchmarkError('duplicate child component ID')
                adapted.append({'group_id': parent, 'points': child_ids, 'evidence_options': [{'option_id': oid, 'supports': {c['component_id']: c.get('supports') for c in children}}]})
            score = score_evidence_points({'query_id': rubric.get('query_id'), 'answer_pool': rubric.get('answer_pool'), 'groups': adapted}, positions)
            evaluated.append({'option_id': oid, 'coverage': score['reference_pool_coverage_percent'] / 100, 'complete': all((g['complete'] for g in score['groups'])), 'parents': score['groups']})
        best = sorted(evaluated, key=lambda x: (-x['coverage'], x['option_id']))[0]
        results.append({'group_id': gid, 'coverage': best['coverage'], 'complete': best['complete'], 'best_option': best['option_id'], 'options': evaluated})
    return {'query_id': rubric['query_id'], 'answer_pool': rubric['answer_pool'], 'weight_profile': weight_profile, 'scope': 'reviewed_reference_pool_only', 'reference_pool_coverage_percent': 100 * sum((g['coverage'] for g in results)) / len(results), 'complete_group_fraction': sum((g['complete'] for g in results)) / len(results), 'groups': results, 'semantic_judgement_performed': False, 'unlisted_material_rule': 'Unlisted material is unjudged, not negative; review and version new valid evidence for all methods.'}
