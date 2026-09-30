import numpy as np
import pytest
from audit_native_external_cooked_geometry import box_hull, common_interior_witness, normalized_planes
from audit_native_external_cooked_vertex_crosscheck import canonical_vertex_hull


def test_vertex_hull_recovers_box_despite_inconsistent_original_planes():
    original=box_hull([.01,.008,.006])
    original['polygons'][0]['plane'][3]+=.001
    recovered=canonical_vertex_hull(original)
    p=normalized_planes(recovered);v=np.asarray(original['vertices'])
    assert (v@p[:,:3].T+p[:,3]).max()<1e-12
    witness=common_interior_witness(recovered,np.eye(4),[.02,.02,.02])
    assert witness['radius_m']==pytest.approx(.006)
