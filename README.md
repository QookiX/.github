# QookiX/.github

[QookiX 组织](https://github.com/QookiX) 的公共仓库，用来放组织主页简介与组织级的公共配置。

## 文件说明

| 路径 | 用途 |
| :--- | :--- |
| [`profile/README.md`](profile/README.md) | **组织简介**。GitHub 会自动把公开 `.github` 仓库中的 `profile/README.md` 渲染到组织主页 <https://github.com/QookiX> 上。 |
| [`scripts/update_stats.py`](scripts/update_stats.py) | 抓取组织公开仓库数据（Stars / 提交数 / 语言构成 / 提交活跃度），写回简介中的自动区块。 |
| [`.github/workflows/update-stats.yml`](.github/workflows/update-stats.yml) | 每天 UTC 00:17 运行同步脚本，有变化才提交；也支持手动触发。 |

后续如果需要，也可以在这里添加组织级默认文件，例如 `CONTRIBUTING.md`、`ISSUE_TEMPLATE/`、`CODE_OF_CONDUCT.md`、`FUNDING.yml`，它们会被组织内没有自定义同名文件的仓库继承。

## 修改简介

直接编辑 `profile/README.md`，推送到默认分支后稍等片刻即可在组织主页生效。前提是：仓库名为 `.github`、可见性为 **Public**、文件路径恰好是 `profile/README.md`。

**注意**：文件里由 `<!-- QK:STATS:START -->` / `<!-- QK:LANG:START -->` 标记包住的两块内容是自动生成的，手改会在下次同步时被覆盖。其余部分（介绍、项目矩阵、平台覆盖表、参与方式）可以放心编辑。

## 自动更新的数据

常见统计卡片服务（github-readme-stats 等）只支持个人账号，用 `username=QookiX` 会报 `Could not resolve to a User`，组织主页用不了。所以这里改成自己同步：

- 同步脚本通过 GitHub REST API 读取组织下所有非 fork 的公开仓库，聚合 Stars、Forks、提交总数、各仓库 `languages` 字节数，以及近 12 周的提交活跃度。
- 结果渲染成徽章、字符热力条、Mermaid 饼图和占比表格，写回 `profile/README.md` 的两个标记区块。
- 语言占比、数字、活跃度每天自动更新；**平台覆盖表是产品事实，保持手动维护**。
- 首次推送会触发一次同步，把版式示例数据换成真实数据。也可以在 Actions 页手动运行 **Sync org stats**。
- 本地预览版式（不联网、不写入）：`python scripts/update_stats.py --demo --check`；重新生成示例区块：`python scripts/update_stats.py --demo`。

如果某天 API 请求失败，脚本会直接报错退出且**不修改** README，不会把线上数据清空。

另外，GitHub 会暂停**连续 60 天没有任何仓库活动**的定时任务；若发现数字久不更新，到 Actions 页手动运行一次 **Sync org stats** 即可恢复。

## 一句话简介（组织设置 bio 候选）

> 开源桌面工具组织：纯净、轻量、跨平台。代表作 QookiX Launcher，另有 SSH 客户端、视频编辑器与局域网快传。

更短的版本：

> 做纯净、轻量、跨平台的开源桌面工具 🍪 QookiX Launcher · QookiT · QookiV · QookiL

## 相关链接

- 官网 <https://www.qookix.cn>
- 文档 <https://docs.qookix.cn>
- 联系 <help@qookix.cn>
