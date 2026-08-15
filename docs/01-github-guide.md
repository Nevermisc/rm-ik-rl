# Git 与 GitHub：零基础够用指南

## 先分清两个东西

- Git：安装在电脑上的版本管理工具。即使断网，也能记录“谁在什么时候改了什么”，并能回到历史版本。
- GitHub：存放 Git 仓库的网络平台，方便备份、展示、协作、代码审查和运行 CI。

仓库不是普通网盘。它保存文件，也保存一连串有意义的修改记录。对求职项目来说，清晰的 README、可复现命令和逐步提交，比一次性上传最终压缩包更能证明你做过并理解项目。

## 最常用的工作循环

```text
修改文件 → git status → git diff → git add → git commit → git push
```

- `git status`：我改了哪些文件？
- `git diff`：具体改了什么？
- `git add`：选出下一次提交要包含的修改。
- `git commit`：在本地创建一个带说明的版本节点。
- `git push`：把本地提交同步到 GitHub。

## clone、pull、push 分别是什么

- `git clone URL`：第一次把远程仓库完整下载到本地。
- `git pull --ff-only`：把远程新增提交同步到已有本地仓库。
- `git push`：把本地新增提交上传到远程仓库。
- 浏览器的 Download ZIP：只下载当前文件快照，没有完整历史，也不便于后续同步；临时查看可以，做开发不推荐。

## HTTPS 与 SSH

这两种只是“本机如何连接 GitHub”，与 Windows 远程登录 Linux 的 SSH 是同一套安全协议的不同用途。

- HTTPS：公开仓库下载最简单；推送时通常通过浏览器登录或 Personal Access Token 验证。
- SSH：配置一次密钥后，长期在 Linux 上推送更方便。私钥留在本机，GitHub 保存公钥。

初学顺序：先用 HTTPS clone 公共仓库；需要从实验室 Linux 向自己的 GitHub push 时再配置 SSH。

## Linux 上配置 Git 身份

```bash
git config --global user.name "你的 GitHub 显示名"
git config --global user.email "你的 GitHub 邮箱或 noreply 邮箱"
git config --global init.defaultBranch main
```

查看配置：

```bash
git config --global --list
```

## 配置 GitHub SSH key

在实验室 Linux 上生成一对专用于该机器的密钥：

```bash
ssh-keygen -t ed25519 -C "你的 GitHub 邮箱"
```

接受默认路径即可，可以给私钥设置口令。然后显示公钥：

```bash
cat ~/.ssh/id_ed25519.pub
```

只复制以 `ssh-ed25519` 开头的这一整行，到 GitHub `Settings > SSH and GPG keys > New SSH key`。绝不能复制或上传没有 `.pub` 后缀的私钥。

测试：

```bash
ssh -T git@github.com
```

第一次看到 GitHub 主机指纹时，应与 GitHub 官方公布的指纹核对后再接受。

## 把当前本地项目连接到新 GitHub 仓库

1. 在 GitHub 网页新建空仓库，例如 `rm-ik-rl`。
2. 不要勾选自动创建 README、LICENSE 或 `.gitignore`，避免与本地初始提交冲突。
3. 在本地项目根目录运行：

```bash
git remote add origin git@github.com:<GITHUB_USER>/rm-ik-rl.git
git branch -M main
git push -u origin main
```

以后只需：

```bash
git push
```

## 什么应该上传

- 你写的 Python/C++、配置文件、环境定义、启动脚本和测试。
- README、安装步骤、实验命令、结果表和必要的小图。
- 你有权再分发、体积合理、项目运行必需的少量资产。
- 能够复现实验的依赖版本，例如 `requirements.txt` 或环境说明。

## 什么不应该上传

- 密码、Token、SSH 私钥、实验室公网/内网信息和个人账号配置。
- Isaac Sim 安装目录、虚拟环境、缓存、日志。
- 大型模型、数据集、训练 checkpoint、录屏原文件。
- 不清楚许可证的第三方代码与素材。
- 机器特定的绝对路径。

常见做法是在 `.gitignore` 中排除它们，并在 README 说明合法下载方式。

## 提交应该多大

一次提交只表达一个完整的小意图，例如：

- `docs: add environment setup instructions`
- `feat: import RM65 asset`
- `feat: add Lula IK controller`
- `test: evaluate IK on 100 targets`
- `fix: use correct end-effector frame`

不要每天只提交一个 `update`，也不要每敲一行就提交。判断标准是：别人能否只看提交标题就理解项目如何一步步形成。

## AI 帮你写代码时的底线

AI 可以生成初稿，但仓库里的每段代码最终都由你负责。至少做到：

1. 能说清输入、输出和核心数据结构。
2. 能自己运行并解释错误日志。
3. 能修改一个目标位置、关节限制或奖励权重。
4. 有一个最小测试或可重复的验证步骤。
5. README 不写无法证明的性能结论。
