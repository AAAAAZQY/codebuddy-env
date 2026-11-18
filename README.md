# codebuddy-env-config

自创规则和长期记忆仓库。只保存用户自己维护的规则/记忆，不保存 CodeBuddy 本身环境文件、插件安装目录、缓存、工程源码副本。

## 范围

- `rules/` <- `C:\Users\myages2026\.codebuddy\rules\edit-visibility.mdc`
- `memory/` <- `D:\Codebuddy\memories\*.md`
- `codebuddy-project-memory/` <- `C:\Users\myages2026\.codebuddy\projects\**\memory\MEMORY.md`

## 同步

```bat
python D:\Codebuddy\git-repos\codebuddy-env-config\sync_config.py
```

同步后在本仓库内执行 `git status --short` 检查差异。
