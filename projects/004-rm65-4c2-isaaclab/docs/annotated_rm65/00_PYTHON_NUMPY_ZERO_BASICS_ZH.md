# RM65 + π0.5 代码零基础预备课

这份预备课解决一个问题：看到代码时，你不只知道“这一块大概做什么”，还知道 Python 按什么顺序执行每个符号，以及数据怎样从 IsaacLab 流进 π0.5，再变成 RM65 仿真动作。

## 1. 先认识整个项目的数据流水线

```text
RM65 URDF + 4C2 URDF
        ↓ 合并、修正、导入
RM65+4C2 USD 仿真资产
        ↓ IsaacLab 创建场景、相机、方块
脚本专家执行抓取放置
        ↓ 每帧记录
两路 RGB + 6 个关节角 + 1 个夹爪值 + 7 维动作 + 文字指令
        ↓ 转换
LeRobot 数据集
        ↓ RM65Inputs / DeltaActions / Normalize
π0.5 微调
        ↓ checkpoint
OpenPI WebSocket 推理服务
        ↓ 返回未来 10×7 动作块
action guard 限位、限步长
        ↓
IsaacLab 执行动作并重新观察
        ↓
成功判定和 20 条批量评测
```

你读任何一行代码时，都要问四个问题：输入是什么；这一行做什么；输出的类型和形状是什么；谁会在后面使用它。

## 2. Python 中最常见的符号

| 符号 | 名称 | 基础作用 | 本项目示例 |
|---|---|---|---|
| `=` | 赋值 | 先算右边，再把结果保存到左边 | `joints = ...` |
| `==` | 相等比较 | 比较两边是否相等，结果是 True/False | `status == "pass"` |
| `!=` | 不等比较 | 比较两边是否不相等 | `joints.shape != (6,)` |
| `.` | 属性访问 | 从模块或对象中取成员 | `np.asarray`、`robot.data` |
| `(...)` | 圆括号 | 调用函数、组合运算或表示元组 | `np.asarray(...)`、`(6,)` |
| `[...]` | 方括号 | 字典取值、数组索引、切片或创建列表 | `data["actions"]`、`actions[:, :6]` |
| `{...}` | 花括号 | 创建字典；在 f-string 中插入变量 | `{"state": state}` |
| `:` | 冒号 | 类型标注、切片、字典键值分隔或打开缩进块 | `data: dict`、`:6`、`if ...:` |
| `,` | 逗号 | 分隔参数/元素；单元素元组必须有逗号 | `(6,)` |
| `->` | 返回类型提示 | 告诉读者函数预计返回什么类型 | `-> dict` |
| `#` | 注释 | 这一行后面的内容不执行 | `# current joints` |
| `@` | 装饰器 | 在类或函数创建时添加行为 | `@dataclass` |

同一个符号会因位置不同而含义不同。你不能只背“冒号是什么意思”，需要看它位于参数、切片、字典还是 `if` 行末。

## 3. 怎样读多层括号

看这一行：

```python
joints = np.asarray(data["observation/joint_position"])
```

不要从左到右硬读，按照“从最里面向外”执行：

1. `"observation/joint_position"`：这是普通字符串。引号表示里面是文字，不是变量名。
2. `data[...]`：`data` 是字典，方括号要求按键取值。因此这里从字典取出六个 RM65 关节角。
3. `np.asarray(...)`：`np` 是 NumPy 模块的简称；点号取得 `asarray` 函数；圆括号表示调用，并把第 2 步的结果作为参数。
4. `np.asarray` 返回一个 NumPy `ndarray`。已有输入若就是合适数组，通常不复制；列表则会被包装/转换成数组。
5. `=`：把第 4 步结果绑定到变量名 `joints`。

完整数据流是：

```text
data 字典
  └─ 键 observation/joint_position
       └─ 原始六关节数据
            └─ np.asarray 转成 ndarray
                 └─ joints，期望 shape=(6,)
```

## 4. 函数定义为什么有这么多符号

```python
def __call__(self, data: dict) -> dict:
```

- `def`：现在开始定义函数，还没有执行函数体。
- `__call__`：特殊方法名。类实现它以后，`transform(data)` 会自动转成 `transform.__call__(data)`。
- 第一对圆括号：写“形参”，也就是调用者需要提供什么。
- `self`：当前 `RM65Inputs` 对象。通过它可以读取 `self.model_type`。
- 逗号：分隔两个形参。
- `data`：调用者传进来的样本字典。
- `data: dict`：参数名仍是 `data`；冒号后的 `dict` 只是类型提示，不会自动检查内容。
- `-> dict`：函数预计返回字典，同样主要帮助读者和编辑器。
- 最后的冒号：下一行开始是函数体，必须缩进。

调用过程类似：

```python
transform = RM65Inputs(model_type=ModelType.PI05)
result = transform(data)
```

第二行实际上触发 `transform.__call__(data)`。

## 5. 字典、列表、元组和 NumPy 数组

### 字典 dict

字典按“键”查找数据：

```python
observation = {
    "observation/joint_position": current_arm,
    "prompt": "pick up the cube",
}
```

读取：

```python
current_arm = observation["observation/joint_position"]
```

这里的 `/` 只是键名字符串的一部分，不是除法，也不代表真实文件夹。

### 列表 list

```python
names = ["joint_1", "joint_2", "joint_3"]
```

列表有顺序，可以修改。`names[0]` 取得第一个元素，因为 Python 索引从 0 开始。

### 元组 tuple

```python
shape = (6,)
```

`(6,)` 是单元素元组。逗号不能省略；`(6)` 只是数字 6 外面套了普通运算括号。

### NumPy ndarray

NumPy 数组适合批量数值计算，并带有：

- `shape`：每个维度的长度；
- `dtype`：元素类型，例如 `float32`、`uint8`；
- 切片：一次选择多行多列；
- 向量运算：不用手写循环就能加减、裁剪和计算距离。

本项目常见形状：

| shape | 含义 |
|---|---|
| `(6,)` | 当前 RM65 六个关节角 |
| `(1,)` | 一个归一化 4C2 夹爪值 |
| `(7,)` | 六关节加一个夹爪的单步状态/动作 |
| `(10, 7)` | π0.5 一次预测未来 10 步，每步 7 维 |
| `(224, 224, 3)` | 高×宽×RGB 三通道图像 |

## 6. 索引和切片

```python
arm_actions = actions[:, :6]
```

从内向外解释：

- `actions[...]`：从数组取一部分；
- 方括号里有两个维度，中间逗号分隔；
- 第一个 `:` 表示第一维全部时间步；
- 第二个 `:6` 表示第二维从开头取到索引 6 之前，即第 0～5 列；
- 结果因此是所有时间步的六个 RM65 关节动作；夹爪第 7 列没有包含。

```python
gripper_actions = actions[:, 6]
```

第一维仍取全部时间步，第二维只取索引 6，也就是第 7 列夹爪动作。

## 7. 类型提示不会替你验证数据

```python
def __call__(self, data: dict) -> dict:
```

`dict` 是提示，并不能保证字典里一定有正确字段。因此代码还需要运行时检查：

```python
if joints.shape != (6,):
    raise ValueError(...)
```

这两层职责不同：

- 类型提示帮助读代码和编辑器检查；
- `if`、`shape`、`raise` 真正在运行时拒绝错误数据。

## 8. 类、对象和 self

类像设计图，对象是根据设计图创建的实例：

```python
class RM65Inputs(...):
    model_type: ModelType

    def __call__(self, data):
        ...
```

```python
transform = RM65Inputs(model_type=ModelType.PI05)
```

- `RM65Inputs` 是类；
- `transform` 是对象；
- `self` 在方法执行时就是这个 `transform`；
- `self.model_type` 是这个对象保存的模型类型。

## 9. NumPy 与 Torch 为什么同时存在

- NumPy 主要用于数据文件、图像、统计量和 OpenPI 输入输出转换；
- Torch 主要用于 IsaacLab 的 GPU 仿真状态和关节目标；
- `.detach().cpu().numpy()` 把不再需要梯度的 GPU Torch 张量移到 CPU，再转为 NumPy；
- `torch.as_tensor(array, device=..., dtype=...)` 把 NumPy 数组变成 Isaac 控制器所在设备的 Torch 张量。

二者转换时要同时检查 shape、dtype 和 device。只看数值内容相似，并不能保证 API 可以直接接收。

## 10. 20 个程序的学习顺序

第一轮只学习数据流：

1. `rm65_policy.py`：一条观测怎样变成 π0.5 输入，输出怎样变回七维动作；
2. `expert_episode.py`：一条专家轨迹在磁盘中长什么样；
3. `convert_expert_episodes_to_lerobot.py`：轨迹怎样变成训练集；
4. `rm65_training_config.py`：训练 transform、delta action 和 LoRA 怎样连起来；
5. `train_rm65_pi05.py`：怎样启动官方训练器；
6. `serve_rm65_policy.py`：checkpoint 怎样成为可请求的服务；
7. `action_guard.py`：模型动作怎样变成允许执行的仿真动作；
8. `run_pick_place_baseline.py`：IsaacLab 怎样观察、请求、执行和重新观察。

第二轮补齐工程：URDF/USD、批量采集、norm stats、checkpoint 验证、闭环 suite 和报告验收。

每读完一个函数，请自己写出：

```text
函数名：
输入变量、类型、shape、单位：
关键中间变量：
返回值、类型、shape、单位：
谁调用它：
它调用谁：
错误数据怎样被拒绝：
```

当你能不看注释回答这些问题，再尝试修改一个参数、预测影响、运行验证并解释结果。这样得到的是可以迁移到新机械臂和新数据集的能力。
