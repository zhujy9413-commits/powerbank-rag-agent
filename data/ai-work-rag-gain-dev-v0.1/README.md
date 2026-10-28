# AI Work RAG 开发材料 v0.1

16个开发场景：12份PDF、4份离线JSON夹具。当前只有材料核验结果，应用行为与RAG实验尚未执行。全部为模拟材料。

详细入口见 docs/ai-work/rag-gain-dev-sample-pack-v0.1.md、rag-gain-dev-reference-v0.1.md、rag-gain-dev-material-audit-v0.1.md。

application-inputs仅提供当前任务事实、双来源语料、通用查询和附件。不要将外层cases、author-source、reference-annotations或eval-results传入应用。PDF位于output/pdf/rag-gain-dev-v0.1。

原文路径相对解压根目录。material-manifest.json登记材料内容SHA-256，不包含其自身；ZIP中另附package-manifest.json及verify-package.py用于离线逐字节核对。完整仓库的材料校验脚本额外对账Git历史与88份旧冻结资产。

开发材料已公开给实现者，不能作为留出集。后续32个留出场景尚未制作。离线夹具使用虚拟时钟且禁止网络，须等待候选适配器；immutable_seed只是构造种子，不是实际A0结果。
