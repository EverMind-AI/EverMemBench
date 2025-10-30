# QAR系统示例脚本

本目录包含QAR系统的示例脚本，演示不同类型QAR的完整处理流程。

## 支持的QAR类型

系统支持以下5类QAR题型：

1. **`profile_adaptive`** - 基于角色配置的自适应QAR
2. **`constraint_qa`** - 约束型内容生成（间接关联）
3. **`progress_continuation_qa`** - 历史目标承接与进度延续
4. **`conflict_resolution_qa`** - 矛盾记忆的推理选择
5. **`active_reminder_qa`** - 主动提醒/偏好矫正

## 示例脚本

### 1. example_group3_qa.py
**功能**: 演示记忆应用能力QAR的完整处理流程

**处理内容**:
- 读取group3下的四个QAR文件（2.1-2.4.json）
- 生成四种不同类型的记忆应用QAR选择题：
  - `constraint_qa`: 约束型内容生成（间接关联）
  - `progress_continuation_qa`: 历史目标承接与进度延续
  - `conflict_resolution_qa`: 矛盾记忆的推理选择
  - `active_reminder_qa`: 主动提醒/偏好矫正（间接关联）

**运行方式**:
```bash
cd examples
python example_group3_qa.py
```

**输出**:
- 格式化选择题（JSON/CSV）
- 原始QAR条目（JSON/CSV）
- 质量检测报告（JSON）

### 2. example_group1_profile_qa.py
**功能**: 演示基于角色配置的自适应QAR（profile_adaptive）的完整处理流程

**处理内容**:
- 读取group1的reference数据（multi_hop.json）
- 读取group1的profile数据（group1.json）
- 生成profile_adaptive QAR选择题（结合角色沟通风格和领域知识）

**运行方式**:
```bash
cd examples
python example_group1_profile_qa.py
```

**输出**:
- 格式化选择题（JSON/CSV）
- 原始QAR条目（JSON/CSV）
- 质量检测报告（JSON）

## 项目结构

```
QAR_via_profile/
├── src/                    # 核心代码
│   ├── core/              # 核心组件
│   │   ├── qa_generator.py    # QAR生成器
│   │   └── formatter.py       # 格式处理器
│   ├── utils/             # 工具组件
│   │   ├── data_loader.py     # 数据加载器
│   │   └── file_handler.py    # 文件处理器
│   ├── llm_interface.py   # 大模型接口
│   ├── prompts.py         # Prompt模板
│   └── quality_control.py # 质量检测
├── examples/              # 示例脚本
│   ├── example_group3_qa.py
│   ├── example_group1_profile_qa.py
│   └── README.md
├── data/                  # 数据文件
│   ├── reference_data/    # Reference数据
│   └── profile_data/      # Profile数据
└── output/                # 输出结果
```

## 质量检测

所有示例脚本都包含完整的质量检测流程：

1. **基础质量要求**:
   - 结合evidence和Q能选对正确选项A
   - 所有选项长度和信息密度相近
   - 问题不能出现信息泄露
   - Q的可回答性
   - A的质量
   - 结构一致性
   - 避免直接猜测
   - 错误选项质量

2. **质量统计**:
   - 总QAR条目数
   - 有效/无效条目数
   - 通过率统计
   - 详细错误报告

## 注意事项

1. 运行前确保已安装所有依赖包
2. 确保数据文件路径正确
3. 输出目录会自动创建
4. 所有结果都会包含时间戳以便区分不同运行
