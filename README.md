<div align="center">
  <h1>EverMemBench</h1>
  <p><strong>A comprehensive benchmark for quantifying and diagnosing memory systems in large language models</strong></p>
  <p>
    <a href="README.md">English</a> | <a href="README_zh.md">简体中文</a>
  </p>
</div>

## Project Description
EverMemBench is a benchmark designed to quantify and diagnose the memory systems of large language models. It introduces, for the first time, a three-tiered evaluation framework for memory systems consisting of: Factual Recall, Applied Memory, and Personalization Generalization.

This layered approach enables researchers to go beyond traditional retrieval-style evaluations and conduct fine-grained diagnostics of model capabilities, precisely locating performance bottlenecks in information extraction, contextual reasoning, or style adaptation. By offering a reproducible and standardized testing framework, EverMemBench not only reveals the significant shortcomings of current state-of-the-art models in achieving deep personalization, but also provides clear guidance for targeted optimization of memory systems.

## Benchmark Description
To systematically and reproducibly assess and diagnose LLM memory capabilities, we construct a long-horizon, multi-party group-chat dataset grounded in realistic workplace communication. The dataset centers on a “multi-role—multi-group—cross-context” communication setting, explicitly modeling the dynamism and context-dependence of individual profiles. In real work scenarios, a person’s behavior and communicative style may drift over time as conversations unfold; at the same time, the same individual may act differently across communities/teams due to role relations and power structures. For example, a department director may be more decisive and stern within a direct-report team chat, yet more restrained in a cross-department strategic group among peers. We embed such “time-varying” and “community-varying” personas and interaction patterns into the data construction process to faithfully reflect the complex and common communication ecology of enterprises.

Benefiting from this design, the dataset supports fine-grained and diagnostic evaluation of model memory systems under conditions of long conversations, concurrent topics, and frequent context switches. We summarize memory capability assessment along three core dimensions:

1. **Fine-grained Detailed Recall.** Tests retrieval ability, requiring the model to accurately reconstruct concrete facts from prior context.

2. **Memory Awareness.** Evaluates retrieval accompanied by understanding: the model must recall past events and integrate them to produce contextually appropriate answers.

3. **User Profile Understanding.** Focuses on personalization and adaptive generation. The model is expected to develop a stable understanding of individual preferences, roles, and tone based on historical interactions, and to adjust content and expression accordingly—avoiding replies that contradict the persona or are overly generic.


![主图](./figures/main.png)


## Benchmark Data
Coming Soon...


## Benchmark Curation Pipeline
Coming Soon...


## Performance on EverMemBench
Coming Soon...


<!-- ## 目录结构

```
EverMemBench/
├── data/                    # 数据文件夹
├── figures/                 # 图表文件夹
├── qa_annotation/           # 问答注释文件夹
├── scripts/                 # 脚本文件夹
├── api_tokens/              # API 密钥文件夹（需创建）
├── .gitignore               # Git 忽略文件
├── LICENSE                  # 许可证文件
├── README.md                # 项目说明文档
├── config.yaml              # 配置文件
├── conversation_infill.py   # 对话填充脚本
├── inference.py             # 推理脚本
├── inference_standalone_openai.py  # 独立的 OpenAI 推理脚本
├── prepare_blocks.py        # 准备数据块的脚本
├── prepare_data.py          # 准备数据的脚本
├── prepare_qa.py            # 准备问答数据的脚本
├── prompts.py               # 提示词脚本
├── query_llm.py             # 查询大型语言模型的脚本
└── requirements.txt         # 依赖项列表
``` -->

<!-- ## 安装

（此处填写安装步骤） -->

<!-- ## 使用说明

（此处填写使用说明） -->


<!-- ## 贡献

（此处填写贡献指南） -->

## License

MIT license
