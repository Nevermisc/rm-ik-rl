"""预热 pi0.5-DROID server并检查8维关节动作。"""

import time

import numpy as np
import websockets.sync.client as ws

# 第一次JAX编译可能超过websockets默认的20秒心跳超时。
# 推理请求本身仍然保持阻塞，直到服务器返回结果或连接真正断开。
_original_connect = ws.connect


def _connect_without_keepalive(*args, **kwargs):
    kwargs["ping_interval"] = None
    return _original_connect(*args, **kwargs)


ws.connect = _connect_without_keepalive

from openpi.policies.droid_policy import make_droid_example
from openpi_client.websocket_client_policy import WebsocketClientPolicy


client = WebsocketClientPolicy("127.0.0.1", 8000)
start = time.perf_counter()
actions = np.asarray(client.infer(make_droid_example())["actions"])
elapsed = time.perf_counter() - start
client._ws.close()

if actions.ndim != 2 or actions.shape[1] != 8:
    raise ValueError(f"预期动作形状(时间步,8)，实际为{actions.shape}")
if not np.isfinite(actions).all():
    raise ValueError("预热推理返回NaN或Inf")

print(f"DROID_WARMUP_SECONDS={elapsed:.3f}")
print(f"DROID_ACTION_SHAPE={actions.shape}")
print("PI05_DROID_WARMUP=PASS", flush=True)
