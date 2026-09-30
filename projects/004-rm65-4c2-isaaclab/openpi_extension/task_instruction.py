"""Require an explicit language task; never silently substitute a block task."""


def require_task_prompt(observation: dict, default_prompt: str | None = None) -> dict:
    result = dict(observation)
    prompt = result.get('prompt', default_prompt)
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError('a non-empty task prompt is required; no implicit block task')
    result['prompt'] = prompt
    return result


class TaskPromptPolicy:
    def __init__(self, policy, default_prompt=None):
        if default_prompt is not None:
            require_task_prompt({}, default_prompt)
        self._policy = policy
        self._default_prompt = default_prompt

    def infer(self, observation):
        return self._policy.infer(require_task_prompt(observation, self._default_prompt))

    @property
    def metadata(self):
        return self._policy.metadata
