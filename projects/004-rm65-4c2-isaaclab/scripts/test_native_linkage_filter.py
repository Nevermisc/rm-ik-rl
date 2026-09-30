import copy
import pytest
from derive_native_linkage_filter import REVIEWED_HINGES, validate_evidence


def evidence():
    return {'urdf_sha256':'source', 'pairs':[
        {'links':list(pair), 'plausible_kinematic_hinge':True, 'max_pivot_coincidence_error_m':1e-15,
         'source_cylinder_profiles':{name:[{'angular_coverage_deg':330,'interpretation':'hole_candidate'}] for name in pair}}
        for pair in REVIEWED_HINGES]}


def test_only_four_reviewed_internal_pairs():
    assert len(validate_evidence(evidence(), 'source')) == 4
    assert ('tool_r_1','tool_r_2') not in REVIEWED_HINGES
    assert all(a.startswith('tool_') and b.startswith('tool_') for a,b in REVIEWED_HINGES)


@pytest.mark.parametrize('kind', ['hash','missing','residual','hole'])
def test_incomplete_geometric_evidence_is_rejected(kind):
    proof = evidence()
    if kind == 'hash': proof['urdf_sha256'] = 'changed'
    elif kind == 'missing': proof['pairs'].pop()
    elif kind == 'residual': proof['pairs'][0]['max_pivot_coincidence_error_m'] = .01
    elif kind == 'hole': proof['pairs'][0]['source_cylinder_profiles'] = {}
    with pytest.raises(ValueError): validate_evidence(proof, 'source')
