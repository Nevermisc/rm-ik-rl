"""CPU-only proof of whether RM65 proprioception reaches pi0.5 input tokens.

No model weights, training, simulation, or robot communication is used.
The installed OpenPI implementation is fingerprinted alongside the result.
"""
import argparse
import dataclasses
import hashlib
import inspect
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi import transforms
from openpi.models import pi0, pi0_config, tokenizer
from openpi.training.config import ModelTransformFactory
from openpi_extension.rm65_training_config import make_pi05_rm65_lora_config


def probe(model_config):
    group = ModelTransformFactory()(model_config)
    tokenize = next(t for t in group.inputs if isinstance(t, transforms.TokenizePrompt))
    prompt = 'pick up the mug and place it on the tray'
    # State is already normalized, as required at this point in the pipeline.
    samples = [tokenize({'prompt': prompt, 'state': np.full(7, value, dtype=np.float32)})
               for value in (-0.75, 0.75)]
    tokens_differ = not np.array_equal(samples[0]['tokenized_prompt'], samples[1]['tokenized_prompt'])
    mask_differ = not np.array_equal(samples[0]['tokenized_prompt_mask'], samples[1]['tokenized_prompt_mask'])
    return dict(pi05=model_config.pi05, discrete_state_input=model_config.discrete_state_input,
                max_token_len=model_config.max_token_len,
                same_image_prompt_different_state_changes_tokens=tokens_differ,
                changes_mask=mask_differ,
                non_padding_tokens=[int(np.count_nonzero(s['tokenized_prompt_mask'])) for s in samples],
                status='pass' if tokens_differ else 'fail')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('fresh report required')
    config = make_pi05_rm65_lora_config(repo_id='local/audit_only')
    # Candidate is constructed in memory; no saved config or checkpoint changed.
    proposed = dataclasses.replace(config.model, discrete_state_input=True, max_token_len=200)
    sources = {}
    for module in (pi0, pi0_config, tokenizer):
        path = Path(inspect.getfile(module))
        sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = dict(schema='rm65_pi05_state_path_audit_v1', cpu_only=True,
                  weights_loaded=False, checkpoint_changed=False, source_sha256=sources,
                  legacy=probe(config.model), proposed=probe(proposed),
                  interpretation='For pi05, no continuous state token exists in embed_suffix. '
                  'The legacy false setting omits numerical state from the network. '
                  'Delta/absolute action transforms still use state outside the network.',
                  limitations=['Input-token test, not proof of learned sensitivity or task success.',
                               'Two normalized synthetic states; no dataset token budget certification.'])
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
