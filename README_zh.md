<div align="center">
  <h1>EverMemBench</h1>
  <p><strong>全面量化和诊断大语言模型记忆系统的评估基准</strong></p>
  <p>
    <a href="README.md">English</a> | <a href="README_zh.md">简体中文</a>
  </p>
</div>

## 项目描述
EverMemBench是一个旨在量化和诊断大语言模型记忆系统的评估基准。它首次将记忆系统评估体系定义成为一个三个递进层次构成的评估体系：**细节记忆（Factual Recall）**、**情境应用（Applied Memory）**和**个性化泛化（Personalization Generalization）**。

这种分层方法使研究者能够超越传统的记忆检索评估，对模型能力进行精细化诊断，精准定位其在信息提取、情境推理或风格适应方面的具体性能瓶颈。通过提供一个可复现的、标准化的测试框架，EverMemBench不仅揭示了当前先进模型在实现深度个性化方面的显著不足，也为针对性的记忆系统优化提供了清晰的指导。

## 数据集描述
为系统化、可重复地衡量与诊断大语言模型的记忆能力，我们构建了一个基于真实办公沟通语境的长时序群聊数据集。该数据集以“多角色—多群组—跨语境”的交流环境为核心设定，显式建模个体画像（profile）的动态性与语境依赖性：在实际工作中，个体的行为与表达风格会随时间推移与对话剧情演进产生漂移；同时，同一人物在不同社群/团队中的言行也会因角色关系与权力结构而变化。例如，一位部门总监在直属团队群中可能更为果断与严肃，而在跨部门的战略群里（与同级同僚沟通）则会相对克制。我们将这类“随时间变化”“随社群变化”的人设与互动规律融入数据构建过程，以逼真再现复杂且常见的企业沟通生态。

得益于上述设计，该数据集能够在长对话、多话题并行与频繁上下文切换的条件下，对模型的记忆系统进行细粒度、可诊断的评测。我们将记忆能力的考察概括为三项核心维度：

1. **细节记忆能力 (Fine-grained Detailed Recall).** 用于检验纯检索能力，要求模型从先前上下文中准确复原具体事实。

2. **记忆应用（感知）能力 (Memory Awareness).** 用于评估伴随理解的检索能力，模型需回忆过往事件并将其整合，以生成契合情境的答案。

3. **对用户信息和偏好的理解的能力 (User Profile Understanding).** 关注个性化建模与自适应生成能力。要求模型基于历史交互形成对个体偏好、角色与语气的稳定理解，并据此调整内容与表达，避免输出与人物设定不符或过于泛化的回复。


![主图](./figures/main.png)


## 评测基准数据
Coming Soon...


## 数据集构建流程
Coming Soon...


## 模型在EverMemBench上的表现
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

## 许可证

MIT license
