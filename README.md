# codebuddy-tools

自创工具脚本仓库。

## 范围

- `tools/toolbox/` <- `D:\Codebuddy\toolbox\`
- `extensions/` <- `D:\Codebuddy\ext-src\` 下的插件源码
- `archive/legacy-tools/` <- `D:\Codebuddy\tools\`

不收录 CodeBuddy 本体安装目录、临时目录、备份目录、工程明文副本、缓存、编译产物。

## 同步

```bat
python D:\Codebuddy\git-repos\codebuddy-tools\sync_tools.py
```

同步后在本仓库内执行 `git status --short` 检查差异。
