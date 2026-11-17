# 接入

从团队根目录运行既有 verify3b/pipeline 命令，指定 `--paper-side paperside/handoffs/paper-side-v2/flexprefill/paper_side.json`，整合阶段指定 `--paper-dir paperside/handoffs/paper-side-v2/flexprefill`。其余 PDF、repo 与输入文件按实际环境提供。

离线验证：从 paperside 运行 `python scripts/validate_delivery.py handoffs/paper-side-v2/flexprefill`。原 v1 调用日志没有重新生成；真实模型调用和目标执行均为零。
