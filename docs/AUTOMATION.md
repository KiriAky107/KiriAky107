# 主页图片自动更新

工作流：`.github/workflows/profile-refresh.yml`。

## 触发时间

- 每天北京时间 **06:17**（cron 为 UTC `17 22 * * *`）。GitHub 的定时任务可能排队延迟，不保证准点运行。
- 可以在 Actions → **Refresh profile visuals** → **Run workflow** 手动运行，选择 `main`。
- 向 `main` 推送本工作流、3D 配色、图片校验脚本或 `README.md` 的修改时，自动刷新。生成图片自己的提交不匹配这些路径。

## 使用的组件

| 组件 | 固定版本 | 用途 |
| --- | --- | --- |
| [GitHub Readme Stats Action](https://github.com/stats-organization/github-readme-stats-action) | v2.1.0；核心 2.2.0 | 公开统计与仓库语言图，各含明暗两版 |
| [Platane/snk](https://github.com/Platane/snk) | v3.5.0，SVG 入口 | 贡献图贪吃蛇，明暗两版 |
| [GitHub Profile 3D Contrib](https://github.com/yoshi389111/github-profile-3d-contrib) | v0.9.3 | 一张内含明暗配色的 3D 贡献图 |

全部 Actions 都固定到完整 commit SHA，工作流旁注标明版本。Dependabot 每周一检查 Actions 的更新并创建 PR；配置不包含自动合并。统计核心的 `core_version: 2.2.0` 另行手动维护。

## 数据与权限

无需新增 secret、PAT 或外部服务账户，使用 GitHub 自动提供的 `GITHUB_TOKEN`。展示公开数据，不启用私有统计或需要额外权限的评论、讨论等扩展统计字段。若账户已选择在 GitHub 公开匿名私有贡献数量，贡献图可能包含这些公开数量，不会读取私有代码。

生成任务只有 `contents: read`，checkout 不保留 Git 凭据。独立发布任务才获得 `contents: write`；它接收本次运行的图片产物，只提交下面七个文件，并使用正常的 fast-forward push，不强制覆盖分支。

```text
profile/stats-light.svg
profile/stats-dark.svg
profile/top-langs-light.svg
profile/top-langs-dark.svg
profile/snake-light.svg
profile/snake-dark.svg
profile-3d-contrib/profile-custom.svg
```

统计卡的 `hide_rank` 已开启。语言图根据公开仓库内容生成，**不代表个人熟练度**；提交、贡献等数字也不是能力评分。

## 修改外观

- 统计卡与 Snake 的颜色在工作流里，采用朱红与墨色。
- 3D 图在 `.github/profile-3d-settings.json` 中配置，结构参考官方 [green-dual.json](https://github.com/yoshi389111/github-profile-3d-contrib/blob/main/sample-settings/green-dual.json)。`fileName` 必须保留为 `profile-custom.svg`。
- README 引用仓库内的 SVG，不依赖公共统计服务在访问时生成。

## 出错时

统计 Action 已设置 `fail_on_error: true`。上传前执行 `python3 scripts/check_profile.py --generated`，检查七张图片均存在且不是错误 SVG；下载后再校验一次。任一生成或校验步骤失败，发布任务就不会提交，远端继续展示上次成功的图片。

到 Actions 查看失败的步骤后，可重新运行。若发布期间 `main` 又有新提交而出现 push 冲突，重新运行完整工作流即可；工作流不会 force push。修改核心版本、配色或文件名后，也应检查一次实际生成结果。
