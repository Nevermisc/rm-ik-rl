import ast
from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.gripper_stage_targets import gripper_stage_targets


@pytest.mark.parametrize('preshape', [0., .7])
def test_release_is_fully_open_regardless_of_preshape(preshape):
    current = np.full(6, preshape)
    start, close, opened = gripper_stage_targets(current, .8)
    np.testing.assert_array_equal(start, current)
    np.testing.assert_array_equal(close, np.full(6,.8))
    np.testing.assert_array_equal(opened, np.zeros(6))
    opened[:] = .2
    np.testing.assert_array_equal(current, np.full(6,preshape))


@pytest.mark.parametrize('current,close', [([], .8), ([float('nan')],.8), ([.9],.8), ([0],float('nan'))])
def test_invalid(current,close):
    with pytest.raises(ValueError): gripper_stage_targets(current,close)


def test_runner_open_stage_uses_release_target_not_approach_target():
    tree = ast.parse((Path(__file__).parent/'run_pick_place_baseline.py').read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == 'smooth_move' and len(n.args) > 8
             and isinstance(n.args[8], ast.Constant) and n.args[8].value == 'OPEN']
    assert len(calls) == 1
    assert ast.unparse(calls[0].args[6]) == 'open_target'
