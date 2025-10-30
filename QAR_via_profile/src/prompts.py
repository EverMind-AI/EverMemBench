"""
QAR生成相关的Prompt模板
"""

from typing import Dict, Any

# 通用基础质量要求模板
COMMON_QUALITY_REQUIREMENTS = """
<basic_quality_requirements>
**基础质量要求（所有QAR类型通用）：**
1. **结合evidence和Q能选对正确选项A**：正确答案必须基于提供的支撑证据，能够通过证据内容推理得出
2. **所有选项长度和信息密度相近**：所有选项字符数必须严格控制在±5%以内，包含相似数量的细节和解释
3. **问题不能出现信息泄露**：问题不能直接通过问题内容就能答对，必须结合evidence才能得出正确答案
4. **Q的可回答性**：问题避免过于宽泛或模糊的表述，必须明确具体，能通过R的内容得出明确答案
5. **A的质量**：答案避免回避问题或答非所问，必须直接回答Q的核心问题，不能模糊或间接
6. **结构一致性**：所有选项使用相同的句式结构和表达方式
7. **避免直接猜测**：所有选项都不能被直接猜测答对，需要有相似的信息密度和格式
8. **错误选项质量**：错误选项必须看起来合理且专业，不能过于明显错误
</basic_quality_requirements>
"""

def build_data_explanation(data):
    """
    构建数据解释部分，帮助大模型理解输入数据的结构和含义
    
    Args:
        data: 输入数据字典
        
    Returns:
        str: 数据解释字符串
    """
    explanation = "**数据说明：**\n"
    explanation += "你正在将QAR主观题转换为QAR选择题。核心是Reference（R），Question（Q）和Answer（A）都可以根据需要进行改写。\n\n"
    
    # 解释reasoning字段
    if 'reasoning' in data:
        explanation += f"**推理过程（reasoning）**：{data['reasoning']}\n"
        explanation += "这是原始QAR的推理过程，展示了从初始事实到最终结论的逻辑链条。\n\n"
    
    # 解释complex_question和ground_truth_answer
    if 'complex_question' in data:
        explanation += f"**原始问题（complex_question）**：{data['complex_question']}\n"
    if 'ground_truth_answer' in data:
        explanation += f"**原始答案（ground_truth_answer）**：{data['ground_truth_answer']}\n"
    explanation += "这些是原始QAR的问题和答案，你可以根据需要进行改写。\n\n"
    
    # 解释supporting_evidence
    if 'supporting_evidence' in data and data['supporting_evidence']:
        explanation += "**支撑证据（supporting_evidence）**：\n"
        for i, evidence in enumerate(data['supporting_evidence'], 1):
            explanation += f"证据{i}：\n"
            if 'character_name' in evidence:
                explanation += f"  - 角色：{evidence['character_name']}\n"
            if 'timestamp' in evidence:
                explanation += f"  - 时间：{evidence['timestamp']}\n"
            if 'content' in evidence and 'dialogue' in evidence['content']:
                explanation += f"  - 对话内容：{evidence['content']['dialogue']}\n"
            if 'type' in evidence:
                explanation += f"  - 类型：{evidence['type']}\n"
        explanation += "\n这些证据包含了角色、时间戳、对话内容等关键信息，是生成选择题的重要依据。\n\n"
    
    return explanation

def get_qa_prompts(data, action):
    """
    获取QAR生成相关的prompt模板
    
    Args:
        data: 输入数据字典
        action: 操作类型 ('constraint_qa', 'progress_continuation_qa', 'conflict_resolution_qa', 'active_reminder_qa', 'profile_adaptive_qa')
    
    Returns:
        str: 格式化的prompt字符串
    """
    
    # 构建数据解释部分
    data_explanation = build_data_explanation(data)
    
    if action == 'constraint_qa':
        # 1. 约束型内容生成 (Q和R主题差别大，间接关联) - 2.1.json
        prompt = f"{data_explanation}" \
                 "<task_type>\n" \
                 "约束型内容生成（基于历史约束的新建议推荐）\n" \
                 "</task_type>\n\n" \
                 "<design_philosophy>\n" \
                 "recommendation类型设计策略：\n" \
                 "- 评判标准：是否通过推荐内容本身体现了对历史约束的记忆\n" \
                 "- 核心原则：选项中**不要显式提到R的具体内容**（如不说'考虑到你拔牙'）\n" \
                 "- 体现方式：通过推荐的事物本身来隐式体现是否应用了约束\n" \
                 "- 错误选项：对一般人都是合理建议，只是不适合有此约束的用户\n" \
                 "</design_philosophy>\n\n" \
                 "<concrete_example>\n" \
                 "场景：R='拔牙了'，Q='推荐餐厅'\n" \
                 "\n" \
                 "T: '推荐XX粥品餐厅，他们家的皮蛋瘦肉粥和海鲜粥都炖得很细腻软糯，口感温润。环境也温馨雅致，适合聚会，人均60左右。'\n" \
                 "   → 通过推荐'粥''软糯'体现记住约束，不说'因为你拔牙'\n" \
                 "\n" \
                 "F1: '推荐XX家常菜馆，他们家的红烧排骨和糖醋里脊都做得很入味，分量足实惠。环境温馨适合聚会，人均65左右。'\n" \
                 "   → 完全忽略约束，推荐普通菜品（对一般人合理，但不适合拔牙）\n" \
                 "\n" \
                 "F2: '推荐XX川菜馆，他们家的回锅肉和麻婆豆腐很有特色，味道正宗地道。环境也不错适合聚会，人均80左右。'\n" \
                 "   → 违反约束（川菜可能硬/辣），但对一般人是好推荐\n" \
                 "\n" \
                 "F3: '推荐XX网红烧烤店，年轻人聚会氛围特别好，他们家的烤串和烤肉都很受欢迎。环境时尚适合拍照，人均90左右。'\n" \
                 "   → 基于场景刻板印象（年轻人聚会→烧烤），忽略个人约束\n" \
                 "</concrete_example>\n\n" \
                 "<option_design_strategy>\n" \
                 "**1. 正确答案（T）- 正确应用约束但不显式提及**\n" \
                 "   设计要素：\n" \
                 "   - 推荐的具体事物本身符合约束（如：软食→粥）\n" \
                 "   - 可用模糊表述暗示（如'适合你现在的情况'），但不说R的具体内容\n" \
                 "   - 推荐新的、具体的方案（具体名称+特色描述）\n" \
                 "   - 补充其他维度信息（环境/价格等）保持完整性\n" \
                 "\n" \
                 "**2. 错误选项F1 - 完全忽略约束（记忆缺失）**\n" \
                 "   设计要素：\n" \
                 "   - 推荐通用的、对一般人合理的方案\n" \
                 "   - 不体现任何个性化，像是给陌生人的建议\n" \
                 "   - 不违反约束（不是明显错误），只是没有针对性\n" \
                 "   - 同样包含完整的描述（特色+环境+价格）\n" \
                 "\n" \
                 "**3. 错误选项F2 - 违反约束但对他人合理**\n" \
                 "   设计要素：\n" \
                 "   - 推荐的内容违反了R中的约束\n" \
                 "   - 但推荐本身对没有此约束的人是好建议\n" \
                 "   - 不是荒谬的、明显错误的推荐\n" \
                 "   - 同样包含完整的描述\n" \
                 "\n" \
                 "**4. 错误选项F3 - 基于刻板印象忽略个人**\n" \
                 "   设计要素：\n" \
                 "   - 基于Q中的场景/人群特征做推荐\n" \
                 "   - 用群体刻板印象代替个人历史约束\n" \
                 "   - 常见刻板印象：年轻人→网红店，聚会→热闹，冬天→火锅\n" \
                 "   - 同样包含完整的描述\n" \
                 "</option_design_strategy>\n\n" \
                 "<critical_principles>\n" \
                 "1. **所有选项都是对Q的完整回答**\n" \
                 "   - 不是列举四种不同类型的事物（粥/川菜/烧烤/火锅）\n" \
                 "   - 而是四种不同程度应用R约束的推荐\n" \
                 "\n" \
                 "2. **选项中不显式提到R的内容**\n" \
                 "   - ❌ 不说：'考虑到你拔牙''因为你拔了智齿'\n" \
                 "   - ✅ 可说：'适合你现在的情况'（模糊暗示）\n" \
                 "   - ✅ 主要通过推荐内容本身体现（推荐软食=记住约束）\n" \
                 "\n" \
                 "3. **'合理但错误'原则**\n" \
                 "   - F1/F2/F3对一般人都是合理建议\n" \
                 "   - 只是不适合有此特殊约束的用户\n" \
                 "   - 避免荒谬的、明显错误的选项\n" \
                 "\n" \
                 "4. **形式严格一致**\n" \
                 "   - 所有选项长度±10%以内\n" \
                 "   - 所有选项都包含：推荐对象+特色描述+其他维度（环境/价格）\n" \
                 "   - 避免通过形式线索判断答案\n" \
                 "</critical_principles>\n\n" \
                 f"{COMMON_QUALITY_REQUIREMENTS}\n" \
                 "<output_format>\n" \
                 "{\n" \
                 '    "Question": "问题文本（如：推荐个餐厅）",\n' \
                 '    "Correct_Answer": "推荐XX，具体特色描述（隐式体现约束），环境价格等",\n' \
                 '    "Incorrect_Answers": [\n' \
                 '        "推荐YY，通用描述（未体现约束），环境价格等",\n' \
                 '        "推荐ZZ，违反约束的描述（但对他人合理），环境价格等",\n' \
                 '        "推荐WW，刻板印象描述（基于场景而非个人），环境价格等"\n' \
                 '    ]\n' \
                 "}\n" \
                 "</output_format>"
                 
    elif action == 'progress_continuation_qa':
        # 2. 历史目标承接与进度延续 (Q和R主题相近) - 2.2.json
        prompt = f"{data_explanation}" \
                 "<task_type>\n" \
                 "历史目标承接与进度延续（基于历史反馈的后续计划）\n" \
                 "</task_type>\n\n" \
                 "<design_philosophy>\n" \
                 "recall_sequence策略：\n" \
                 "- 评判标准：后续计划是否正确承接了历史进度和反馈\n" \
                 "- 核心原则：**不要显式总结历史**（如不说'上次你说了X'）\n" \
                 "- 体现方式：通过后续计划的起点和方向，隐式体现对历史的理解\n" \
                 "- 错误选项：计划本身合理，只是与历史进度脱节\n" \
                 "</design_philosophy>\n\n" \
                 "<concrete_example>\n" \
                 "场景：R='第一阶段已完成模拟脚本验证，效果不错'，Q='下一步怎么做'\n" \
                 "\n" \
                 "T: '建议推进第二阶段的真实环境验证，可以先在测试集群小范围部署动态调度模块，监控性能指标和稳定性，根据数据反馈调整参数配置。'\n" \
                 "   → 通过'推进第二阶段''真实环境'体现承接，不说'你上次完成了模拟'\n" \
                 "\n" \
                 "F1: '建议先完善模拟脚本的验证工作，增加更多边界场景测试，确保调度逻辑在各种负载下都稳定可靠后再考虑下一步。'\n" \
                 "   → 忽略历史进度，重复已完成的工作\n" \
                 "\n" \
                 "F2: '建议开始准备生产环境的全面部署方案，制定详细的迁移计划和回滚策略，同步推进监控告警系统的升级工作。'\n" \
                 "   → 跨越中间步骤，过度前瞻（应该先小范围验证）\n" \
                 "\n" \
                 "F3: '建议重新评估整体技术路线，考虑是否有更合适的调度算法，同时调研业界最新的实践方案作为参考。'\n" \
                 "   → 方向偏离，忽视已有进展\n" \
                 "</concrete_example>\n\n" \
                 "<option_design_strategy>\n" \
                 "**1. 正确答案（T）- 正确承接历史但不显式总结**\n" \
                 "   设计要素：\n" \
                 "   - 后续计划的起点正确（接续历史终点）\n" \
                 "   - 可用序数词暗示（如'第二阶段''接下来'），不详述历史\n" \
                 "   - 计划具体可行，包含方法、目标、注意事项\n" \
                 "   - 体现对历史反馈的理解（如R说'效果好'→T说'推进'）\n" \
                 "\n" \
                 "**2. 错误选项F1 - 忽略历史进度（记忆缺失）**\n" \
                 "   设计要素：\n" \
                 "   - 建议重复已完成的工作\n" \
                 "   - 计划本身合理，只是与历史脱节\n" \
                 "   - 像是没看过历史对话的人给的建议\n" \
                 "   - 同样包含具体方法和目标\n" \
                 "\n" \
                 "**3. 错误选项F2 - 过度前瞻（理解偏差）**\n" \
                 "   设计要素：\n" \
                 "   - 跨越了应有的中间步骤\n" \
                 "   - 计划过于激进，忽视循序渐进\n" \
                 "   - 对历史阶段的判断错误（以为比实际更成熟）\n" \
                 "   - 计划本身不荒谬，只是时机不对\n" \
                 "\n" \
                 "**4. 错误选项F3 - 方向偏离（理解错误）**\n" \
                 "   设计要素：\n" \
                 "   - 提出的方向与历史主线不一致\n" \
                 "   - 可能忽视已有进展，建议重新开始\n" \
                 "   - 或转向其他分支，偏离原有目标\n" \
                 "   - 建议本身有道理，只是不符合当前语境\n" \
                 "</option_design_strategy>\n\n" \
                 "<critical_principles>\n" \
                 "1. **不显式总结历史**\n" \
                 "   - ❌ 不说：'根据你上次说的''你之前完成了模拟验证'\n" \
                 "   - ✅ 可说：'第二阶段''接下来''在此基础上'\n" \
                 "   - ✅ 主要通过计划的起点和方向体现对历史的理解\n" \
                 "\n" \
                 "2. **所有选项都是完整的后续计划**\n" \
                 "   - 包含：具体方法+阶段目标+实施要点\n" \
                 "   - 不是简单的一句话，而是完整的计划描述\n" \
                 "\n" \
                 "3. **'合理但不合时'原则**\n" \
                 "   - 错误选项的计划本身都合理\n" \
                 "   - 只是与历史进度不匹配（太早/太晚/方向错）\n" \
                 "\n" \
                 "4. **形式一致性**\n" \
                 "   - 长度±10%\n" \
                 "   - 都包含：方法+目标+细节\n" \
                 "   - 语气和专业度统一\n" \
                 "</critical_principles>\n\n" \
                 f"{COMMON_QUALITY_REQUIREMENTS}\n" \
                 "<output_format>\n" \
                 "{\n" \
                 '    "Question": "问题文本（如：下一步怎么推进）",\n' \
                 '    "Correct_Answer": "建议推进XX，具体方法和目标（隐式承接历史）",\n' \
                 '    "Incorrect_Answers": [\n' \
                 '        "建议重复YY，具体描述（忽略历史进度）",\n' \
                 '        "建议直接ZZ，具体描述（过度前瞻）",\n' \
                 '        "建议转向WW，具体描述（方向偏离）"\n' \
                 '    ]\n' \
                 "}\n" \
                 "</output_format>"
                 
    elif action == 'conflict_resolution_qa':
        # 3. 矛盾记忆的推理选择 (哪条记忆更符合现在语境) - 2.3.json
        prompt = f"{data_explanation}" \
                 "<task_type>\n" \
                 "矛盾记忆的推理选择（基于最新信息的推理结论）\n" \
                 "</task_type>\n\n" \
                 "<design_philosophy>\n" \
                 "tracking_preference_updates策略：\n" \
                 "- 评判标准：推理结论是否基于最新、最准确的信息\n" \
                 "- 核心原则：**不要罗列历史变化**（如不说'你先说A后说B'）\n" \
                 "- 体现方式：通过结论本身体现对最新状态的把握\n" \
                 "- 错误选项：推理逻辑合理，只是基于了错误的时间点\n" \
                 "</design_philosophy>\n\n" \
                 "<concrete_example>\n" \
                 "场景：R1='之前倾向方案A'，R2='最新讨论后改为方案B'，Q='最终用哪个方案'\n" \
                 "\n" \
                 "T: '采用方案B，在分布式架构下性能更优，且能更好支持后续的弹性扩展需求。建议先在测试环境验证关键路径。'\n" \
                 "   → 直接给出基于最新信息的结论，不说'你从A改到了B'\n" \
                 "\n" \
                 "F1: '采用方案A，在单体架构下实现简单，能快速完成MVP验证。后续可根据实际负载情况再考虑优化。'\n" \
                 "   → 基于过时信息（旧方案），推理本身合理\n" \
                 "\n" \
                 "F2: '采用A和B的混合方案，前期用A保证快速上线，同时并行准备B的架构改造，逐步迁移过渡。'\n" \
                 "   → 部分理解更新但推理错误（已明确选B，不需混合）\n" \
                 "\n" \
                 "F3: '采用方案C，综合考虑A和B的优点，采用云原生架构配合服务网格，能更好应对未来的复杂场景。'\n" \
                 "   → 过度推理，引入不存在的选项\n" \
                 "</concrete_example>\n\n" \
                 "<option_design_strategy>\n" \
                 "**1. 正确答案（T）- 基于最新信息但不罗列历史**\n" \
                 "   设计要素：\n" \
                 "   - 结论基于最新、最准确的状态\n" \
                 "   - 直接陈述结论和理由，不回顾变化过程\n" \
                 "   - 包含具体的实施建议和注意事项\n" \
                 "   - 推理逻辑严密，与当前语境匹配\n" \
                 "\n" \
                 "**2. 错误选项F1 - 基于过时信息（记忆未更新）**\n" \
                 "   设计要素：\n" \
                 "   - 结论基于早期的、已被更新的信息\n" \
                 "   - 推理逻辑本身合理，只是时间点错了\n" \
                 "   - 像是没看到最新讨论的人给的建议\n" \
                 "   - 同样包含具体的理由和建议\n" \
                 "\n" \
                 "**3. 错误选项F2 - 部分理解但推理错误**\n" \
                 "   设计要素：\n" \
                 "   - 知道有更新，但对更新的含义理解错误\n" \
                 "   - 可能试图调和矛盾（实际已有明确结论）\n" \
                 "   - 推理有一定道理，但不符合实际状态\n" \
                 "   - 同样包含完整的论述\n" \
                 "\n" \
                 "**4. 错误选项F3 - 过度推理添加信息**\n" \
                 "   设计要素：\n" \
                 "   - 在已有信息基础上过度延伸\n" \
                 "   - 引入历史中不存在的新选项或结论\n" \
                 "   - 推理看似深入，但脱离实际讨论范围\n" \
                 "   - 听起来专业，但不接地气\n" \
                 "</option_design_strategy>\n\n" \
                 "<critical_principles>\n" \
                 "1. **不罗列历史变化**\n" \
                 "   - ❌ 不说：'你之前说A，后来改成B''经过讨论从A转向B'\n" \
                 "   - ✅ 直接说：'采用B方案，理由是...'\n" \
                 "   - ✅ 通过结论本身体现对最新状态的把握\n" \
                 "\n" \
                 "2. **所有选项都是完整的推理结论**\n" \
                 "   - 包含：明确结论+支撑理由+实施建议\n" \
                 "   - 不是简单选择题，而是完整的论述\n" \
                 "\n" \
                 "3. **'合理但时点错'原则**\n" \
                 "   - 错误选项的推理逻辑都合理\n" \
                 "   - 只是基于了错误的时间点/状态\n" \
                 "\n" \
                 "4. **形式一致性**\n" \
                 "   - 长度±10%\n" \
                 "   - 都包含：结论+理由+建议\n" \
                 "   - 论述的深度和专业度统一\n" \
                 "</critical_principles>\n\n" \
                 f"{COMMON_QUALITY_REQUIREMENTS}\n" \
                 "<output_format>\n" \
                 "{\n" \
                 '    "Question": "问题文本（如：最终采用哪个方案）",\n' \
                 '    "Correct_Answer": "采用XX，理由和建议（基于最新信息）",\n' \
                 '    "Incorrect_Answers": [\n' \
                 '        "采用YY，理由和建议（基于过时信息）",\n' \
                 '        "采用YY+XX混合，理由和建议（部分理解但错误）",\n' \
                 '        "采用ZZ，理由和建议（过度推理添加信息）"\n' \
                 '    ]\n' \
                 "}\n" \
                 "</output_format>"
                 
    elif action == 'active_reminder_qa':
        # 4. 主动提醒/偏好矫正 (间接关联，需要错误诱导) - 2.4.json
        prompt = f"{data_explanation}" \
                 "<task_type>\n" \
                 "主动提醒/偏好矫正（基于历史教训的主动纠偏）\n" \
                 "</task_type>\n\n" \
                 "<design_philosophy>\n" \
                 "recall_preference策略：\n" \
                 "- 评判标准：是否通过提醒内容体现了对历史教训的记忆\n" \
                 "- 核心原则：**不要详述历史过程**（如不说'你上次因为X被批评了'）\n" \
                 "- 体现方式：通过提醒点和替代建议本身体现对历史的记忆\n" \
                 "- 错误选项：提醒本身合理，只是针对了错误的历史或过度/不足\n" \
                 "</design_philosophy>\n\n" \
                 "<concrete_example>\n" \
                 "场景：R='上次直接跳过测试环境部署到生产，被批评'，Q='这次能直接上线吗'\n" \
                 "\n" \
                 "T: '建议先在测试环境验证功能和性能，确认稳定后再发布到生产。可以用灰度发布降低风险，整个流程预计需要2-3天。'\n" \
                 "   → 通过'先测试环境''灰度发布'体现记住教训，不说'上次你被批评了'\n" \
                 "\n" \
                 "F1: '建议遵循标准发布流程，需要先经过代码审查和安全扫描，然后提交变更申请，等待审批通过后才能部署，预计需要一周时间。'\n" \
                 "   → 过度提醒，引入了历史中不存在的流程要求\n" \
                 "\n" \
                 "F2: '注意这次要走正规流程，建议先在测试环境部署，但如果很紧急的话，也可以先上生产再补测试。'\n" \
                 "   → 部分提醒但建议自相矛盾（又允许违反）\n" \
                 "\n" \
                 "F3: '可以直接上线，功能改动不大，应该不会有问题。上线后密切关注监控指标，有异常及时回滚就行。'\n" \
                 "   → 完全忽略历史教训，认可了错误做法\n" \
                 "</concrete_example>\n\n" \
                 "<option_design_strategy>\n" \
                 "**1. 正确答案（T）- 正确提醒但不详述历史**\n" \
                 "   设计要素：\n" \
                 "   - 明确要求纠正当前的错误倾向\n" \
                 "   - 通过替代方案体现对历史教训的记忆\n" \
                 "   - 可用委婉表述（如'建议遵循标准流程'），不详述历史\n" \
                 "   - 给出具体可行的替代建议和时间预期\n" \
                 "\n" \
                 "**2. 错误选项F1 - 过度提醒（记忆混淆）**\n" \
                 "   设计要素：\n" \
                 "   - 有提醒意识，但引用了错误的规则或教训\n" \
                 "   - 或夸大了约束的严重性和复杂度\n" \
                 "   - 要求过于严格，超出了实际需要\n" \
                 "   - 同样包含完整的建议和时间预期\n" \
                 "\n" \
                 "**3. 错误选项F2 - 部分提醒但建议矛盾**\n" \
                 "   设计要素：\n" \
                 "   - 能识别到需要提醒\n" \
                 "   - 但给出的替代建议不合理或自相矛盾\n" \
                 "   - 或提醒后又留了违规的口子\n" \
                 "   - 看似负责但实际不够坚定\n" \
                 "\n" \
                 "**4. 错误选项F3 - 完全忽略教训（记忆缺失）**\n" \
                 "   设计要素：\n" \
                 "   - 完全没有提醒，直接认可用户的错误倾向\n" \
                 "   - 像是不知道历史教训的人给的建议\n" \
                 "   - 可能包含风险缓解措施（如监控），但不纠正根本错误\n" \
                 "   - 听起来务实，但忽视了历史\n" \
                 "</option_design_strategy>\n\n" \
                 "<critical_principles>\n" \
                 "1. **不详述历史过程**\n" \
                 "   - ❌ 不说：'你上次因为跳过测试被批评了''记得上次的教训吗'\n" \
                 "   - ✅ 可说：'建议先在测试环境验证''遵循标准流程'\n" \
                 "   - ✅ 通过提醒点和替代方案体现对历史的记忆\n" \
                 "\n" \
                 "2. **所有选项都是完整的回复**\n" \
                 "   - 包含：态度表达+具体建议+时间/风险评估\n" \
                 "   - T/F1/F2都有提醒元素，只是准确度不同\n" \
                 "\n" \
                 "3. **'负责但方向错'原则**\n" \
                 "   - F1过度负责（要求太严）\n" \
                 "   - F2表面负责（提醒但矛盾）\n" \
                 "   - F3看似务实（直接同意）\n" \
                 "   - 都像是负责任的回复，但只有T真正基于历史\n" \
                 "\n" \
                 "4. **形式一致性**\n" \
                 "   - 长度±10%\n" \
                 "   - 都包含：态度+建议+预期\n" \
                 "   - 语气的专业度和关切度统一\n" \
                 "</critical_principles>\n\n" \
                 f"{COMMON_QUALITY_REQUIREMENTS}\n" \
                 "<output_format>\n" \
                 "{\n" \
                 '    "Question": "问题文本（如：能直接这样做吗）",\n' \
                 '    "Correct_Answer": "建议先XX，具体方案和理由（隐式体现历史教训）",\n' \
                 '    "Incorrect_Answers": [\n' \
                 '        "建议遵循YY流程，具体方案（过度要求或记忆混淆）",\n' \
                 '        "注意要ZZ，但如果紧急也可以...（提醒但矛盾）",\n' \
                 '        "可以直接做，注意监控就行（完全忽略教训）"\n' \
                 '    ]\n' \
                 "}\n" \
                 "</output_format>"
                 
    elif action == 'profile_adaptive_qa':
        # 处理对话内容
        dialogue_text = ""
        if data['dialogue_content']:
            dialogue_lines = []
            for item in data['dialogue_content']:
                dialogue_lines.append(f"- {item['character_name']}: {item['dialogue']}")
            dialogue_text = "\n".join(dialogue_lines)
        else:
            dialogue_text = "无对话内容"
        
        prompt = f"""<task>
基于完整的Reference事件和选中角色的Profile生成自适应QAR问题
</task>

<reference_data>
**完整Reference事件：**
事件类型：{data['reference_type']}
事件描述：{data['event_description']}
关键信息：{data['key_information']}
对话内容：
{dialogue_text}
</reference_data>

<profile_data>
**选中角色的Profile：**
姓名：{data['character_name']}
职业：{data['character_occupation']}

**沟通风格详细分析：**
{data['communication_style']}

**沟通风格字段含义解释：**
- **正式程度 (formality)**: 高（正式商务）| 中（平衡）| 低（随意轻松）
- **话量程度 (verbosity)**: 高（详细）| 中（适中）| 低（简洁）
- **幽默感 (humor)**: 有 | 无
- **行话使用 (jargon_usage)**: 高（大量术语）| 中（适度）| 低（通俗）
- **口语使用 (casual_language_usage)**: 高（口语化）| 中（适度）| 低（书面语）

专业技能：{data['domain_knowledge']}
</profile_data>

<question_requirements>
<format>
问题格式：使用'我（{data['character_name']}）要XXX，你帮我XXX吧'的格式
</format>

<content_constraints>
- 问题中只能出现人名、事件简称、时间点、地点等区分信息
- 问题中不能出现完整的Reference内容和Profile特征
- 问题中不能出现Reference的具体指标、详细内容、Profile的沟通风格等需要测试的信息
</content_constraints>

<task_design>
- 基于Reference事件设计一个该角色可能遇到的具体任务
- 通过答案选项来体现Profile风格和Reference具体内容
- 让答题者无法只通过问题和答案就能判断正确答案，需要结合额外的上下文才能正确答对
</task_design>
</question_requirements>

<answer_options>
<gradient_design>
<T_option>
**T (正确答案)**：必须同时体现Profile沟通风格和Reference具体内容
- 同时满足Profile风格和Reference内容，缺一不可
- 正确地满足问题的要求，并且体现角色的沟通风格和包含了事件的具体信息
</T_option>

<F1_option>
**F1 (错误答案)**：符合Reference内容但不符合Profile沟通风格
- **设计方法：切换到“另一个自然的人设”**
- 1. **(Ref内容正确)**：首先，完整复制T选项中的**所有核心事实和细节**。
- 2. **(Profile风格错误)**：然后，选择一个与原Profile（如‘严肃/低口语’）风格相反但**同样自然**的人设（如‘热情/高能量/口语化’）。
- 3. **(重写)**：用这个新的人设风格，将所有事实**完全重写**一遍。
- 4. **(禁止)**：**禁止**使用夸张、非自然的标签化词语（如'🎉'、'稳得很'、'妥妥的'）或表情符号。目标是创造一个听起来像*另一个真实的人*写的答案，而不是一个拙劣的模仿。
</F1_option>

<F2_option>
**F2 (错误答案)**：符合Profile沟通风格但不符合Reference具体内容
- **设计方法：设计一个“貌似合理的替代方案”**
- 1. **(Profile风格正确)**：保持与T选项完全一致的Profile沟通风格（如严肃、专业）。
- 2. **(Ref内容错误)**：设计一个在**核心逻辑或方案**上与Reference完全不同，但**同样详细、貌似合理**的“替代方案”。
- 3. **(禁止)**：**绝对禁止**仅仅修改Reference中的数字或单个关键词（例如，把‘30%’改成‘15%’）。
- 4. **(要求)**：必须在方案的*根本逻辑*上制造错误（例如，将‘两阶段验证’改成‘单阶段A/B测试’，将‘模拟脚本’改成‘真实环境部署’）。
- 5. **(目标)**：确保F2选项在*详细程度、专业术语和长度*上与T选项高度一致。
</F2_option>

<FF_option>
**FF (错误答案)**：既不符合Profile沟通风格也不符合Reference具体内容
- **设计方法：结合F1和F2的错误**
- 1. **(Profile风格错误)**：采用F1的“切换人设”方法（使用一个与原Profile相反的、自然的风格）。
- 2. **(Ref内容错误)**：采用F2的“替代方案”方法（使用一个错误的核心逻辑方案）。
- 3. **(目标)**：确保该选项在长度和复杂度上与T选项相近。
</FF_option>
</gradient_design>

<quality_requirements>
<anti_cheating>
- **绝对要求：** 所有选项（T, F1, F2, FF）的长度必须高度相近（±5%以内）。
- **绝对要求：** 所有选项的详细程度和复杂度必须一致。
- 选项不能有明显的语法错误或格式差异。
- 避免通过标点符号数量来区分答案。
- 确保所有选项都看起来是合理且专业的回复。
</anti_cheating>

<content_quality>
- 请勿偷懒！T, F1, F2, FF的生成难度是递增的，必须确保F1, F2, FF的质量。
- **F2/FF质量检查：** 错误是否是“方案级”的？还是仅仅改了“数字”？（后者无效）
- **F1/FF质量检查：** 风格是否“自然”？还是“夸张/标签化”？（后者无效）
</content_quality>
</quality_requirements>
</answer_options>

<examples>
<correct_format>
✅ 正确格式：'我（{data['character_name']}）要给全公司发一封邮件宣布项目A上线，你帮我起草一个初稿吧。'
✅ 正确格式：'我（{data['character_name']}）需要向高层汇报方舟项目的技术方案，你帮我写个摘要吧。'
</correct_format>

<incorrect_format>
❌ 错误格式：'我（{data['character_name']}）要写一个正式的报告，包含分阶段验证策略和KPI...'（泄露了Reference具体内容）
❌ 错误格式：'我（{data['character_name']}）要用活泼幽默的风格写邮件...'（泄露了Profile特征）
</incorrect_format>

<high_quality_example>
**Reference (事实):** "方舟项目"的技术路线采用分阶段验证方案：
1. 用轻量级模拟脚本验证调度策略（目标：降低30%构建等待时间）；
2. 在真实环境中小范围落地动态权重调整方案。

**Profile (陈默):** `正式程度: 中`, `话多程度: 中`, `幽默感: 无`, `专业术语使用: 中`, `口语使用: 低`
(风格总结：严肃、专业、书面语、不幽默)

**Question:** "我（陈默）要准备方舟项目技术路线的验证方案汇报，你帮我写个简要的总结先发群里吧。"

---
**T (正确答案) (Profile: 陈默, Reference: 正确方案)**
"方舟项目的技术路线将采用分阶段验证方案。第一阶段使用轻量级模拟脚本验证调度策略的可行性，第二阶段在真实环境中进行小范围落地动态权重调整方案，以降低30%构建等待时间为关键目标。"

**F1 (错误答案) (Profile: 相反人设-热情/高口语, Reference: 正确方案)**
"方舟项目的路线图很清晰：两步走。第一步，咱们用模拟脚本快速验证调度策略；第二步，直接上真实环境小范围开跑动态权重调整方案，必须拿下30%的等待时间缩减！"

**F2 (错误答案) (Profile: 陈默, Reference: 错误方案)**
"方舟项目的技术路线将采用**单阶段验证**方案。我们将**直接在真实环境中部署A/B测试**，以验证**静态优先级队列**方案的可行性，关键目标是降低30%构建等待时间。"

**FF (错误答案) (Profile: 相反人设-热情/高口语, Reference: 错误方案)**
"关于方舟项目，这个方案咱们一步到位！**直接全量上线A/B测试**，看看那个**静态队列**的效果。我拍板了，目标就是把等待时间砍掉15%，必须搞定！"
---

**设计说明：**
- **T vs F1 (Profile测试):** F1的风格（“咱们”、“开跑”、“拿下”）与T（“可行性”、“小范围落地”）截然不同，但两者描述的*事实方案*（两阶段、模拟脚本、动态权重、30%）完全一致。
- **T vs F2 (Reference测试):** F2的风格与T完全一致（都是陈默的专业风格），但*事实方案*（“单阶段”、“A/B测试”、“静态队列”）与T（“两阶段”、“模拟脚本”、“动态权重”）完全不同。
- **长度和复杂度：** 所有四个选项的长度、专业术语使用量和信息复杂度都高度一致，无法通过“选最长的”来作弊。

</high_quality_example>
</examples>

<final_check_and_revision>
**最终质量与长度修正（必须执行）**

1.  **生成所有选项：** 首先，按照T, F1, F2, FF的要求生成所有四个选项。
2.  **计算基准长度：** 计算 "Correct_Answer" (T) 的总字符数 (L_T)。
3.  **逐一检查并修正（±5% 规则）：**
    a.  计算 F1, F2, FF 的字符数。
    b.  **如果某个选项的长度 (L_X) 不在 [L_T * 0.95, L_T * 1.05] 范围内，必须修正它。**
    c.  **修正策略（如何增加长度）：**
        -   **修正 F1 (Ref✓, Profile✗)：** 在**不改变其错误风格**的前提下，从Reference中**补充更多次要但相关的细节**（例如，补充“评估稳定性”相关内容），并用*错误*的风格重写。
        -   **修正 F2 (Ref✗, Profile✓)：** 在**不改变其正确风格**的前提下，为你编造的“错误方案”**补充更多貌似合理、专业的细节**（例如，为“A/B测试”增加一个“对照组描述”或“评估周期”）。
        -   **修正 FF (Ref✗, Profile✗)：** 结合上述两者，为你编造的“错误方案”**补充更多细节**，并用**错误的风格**来写。
    d.  **修正策略（如何减少长度）：** 同理，精简次要的细节描述。
4.  **最终输出：** 仅输出经过长度修正后的最终JSON。
</final_check_and_revision>

<output_format>
严格按照JSON格式输出，使用双引号，不要添加任何解释性文字：

{{
    "Question": "任务问题文本",
    "Correct_Answer": "正确答案（Profile+Reference）",
    "Incorrect_Answers": [
        "错误选项1（Reference但非Profile）",
        "错误选项2（Profile但非Reference）",
        "错误选项3（非Profile非Reference）"
    ]
}}
</output_format>"""
                 
    elif action == 'test_question_leakage':
        prompt = f"""你是一个没有任何上下文信息的AI助手。你只能看到以下问题和选项，没有任何其他背景信息。

请基于你看到的问题和选项，选择一个你认为最合适的答案。

问题：{data['question']}

选项：
{chr(10).join(data['options'])}

重要说明：
1. 你没有任何上下文信息，只能基于问题本身和选项内容进行判断
2. 如果问题涉及特定的人物、事件或背景信息，而你无法从问题本身获得这些信息，请随机选择一个选项
3. 请只回答选项字母（如 a、b、c、d），不要包含任何解释或其他内容

你的答案："""
    
    elif action == 'dual_output_leakage_test':
        prompt = f"""请仔细阅读以下问题和选项（不要使用任何外部知识）。

问题：{data['question']}

选项：
{chr(10).join(data['options'])}

---
任务：
请仔细阅读以上问题和选项（不要使用任何外部知识）。
1. 仅凭问题和选项的措辞，哪一个选项看起来是"最合理的"答案？
2. 仅凭问题和选项的措辞，哪一个选项看起来是"最不合理"（例如：最像稻草人、事实错误或最容易被排除）的答案？

请按以下格式回答：
最合理: (x)
最不合理: (y)"""
    
    elif action == 'rewrite_option_for_balance':
        prompt = f"""任务：请改写指定的选项，使其在保持核心含义（特别是保持其"错误性"）不变的前提下，在"长度"、"结构复杂度"和"信息密度"上与参考选项保持一致。

问题：{data['question']}

所有选项：
{chr(10).join(data['all_options'])}

参考选项（请模仿其风格和复杂度）：
"{data['target_option']}"

待改写选项（请改写这个）：
"{data['option_to_rewrite']}"

要求：
1. 保持选项的核心错误逻辑不变
2. 在长度、结构复杂度和信息密度上与参考选项保持一致
3. 使用相似的表达风格和句式结构
4. 确保改写后的选项看起来专业且合理
5. 改写后的选项应该与问题和其他选项在语义上协调

改写后的选项："""
    
    elif action == 'rewrite_multiple_options_for_balance':
        prompt = f"""任务：请改写指定的多个选项，使它们在保持核心含义（特别是保持其"错误性"）不变的前提下，在"长度"、"结构复杂度"和"信息密度"上与参考选项保持一致。

问题：{data['question']}

所有选项：
{chr(10).join(data['all_options'])}

参考选项（请模仿其风格和复杂度）：
"{data['target_option']}"

待改写选项列表：
{chr(10).join([f"{i+1}. {option}" for i, option in enumerate(data['options_to_rewrite'])])}

要求：
1. 保持每个选项的核心错误逻辑不变
2. 在长度、结构复杂度和信息密度上与参考选项保持一致
3. 使用相似的表达风格和句式结构
4. 确保改写后的选项看起来专业且合理
5. 改写后的选项应该与问题和其他选项在语义上协调
6. 保持选项之间的差异化，避免过于相似

请按以下格式输出改写后的选项：
1. [改写后的选项1]
2. [改写后的选项2]
3. [改写后的选项3]
..."""
    
    elif action == 'rewrite_with_leakage_feedback':
        prompt = f"""任务：基于泄漏检测反馈，改写指定的多个选项，解决质量问题。

问题：{data['question']}

所有选项：
{chr(10).join(data['all_options'])}

参考选项（请模仿其风格和复杂度）：
"{data['target_option']}"

待改写选项列表：
{chr(10).join([f"{i+1}. {option}" for i, option in enumerate(data['options_to_rewrite'])])}

⚠️ 泄漏检测反馈：
泄漏类型：{data['leakage_type']}
修正指令：{data['correction_instruction']}

要求：
1. 保持每个选项的核心错误逻辑不变
2. 在长度、结构复杂度和信息密度上与参考选项保持一致
3. 使用相似的表达风格和句式结构
4. 确保改写后的选项看起来专业且合理
5. 改写后的选项应该与问题和其他选项在语义上协调
6. 保持选项之间的差异化，避免过于相似
7. **重要**：根据泄漏反馈调整选项，确保不再出现信息泄漏或稻草人问题

请按以下格式输出改写后的选项：
1. [改写后的选项1]
2. [改写后的选项2]
3. [改写后的选项3]
..."""
        
    elif action == 'qa_self_evaluation':
        # QAR自我评估prompt
        question = data.get('question', '')
        correct_answer = data.get('correct_answer', '')
        incorrect_answers = data.get('incorrect_answers', [])
        original_prompt = data.get('original_prompt', '')
        qa_type = data.get('qa_type', 'unknown')
        key_constraints = data.get('key_constraints', '无明确约束')
        
        # 计算选项长度
        all_options = [correct_answer] + incorrect_answers
        option_lengths = [len(opt) for opt in all_options]
        max_len = max(option_lengths)
        min_len = min(option_lengths)
        length_variance = ((max_len - min_len) / max_len * 100) if max_len > 0 else 0
        
        # 根据QA类型添加特定的评估要点
        type_specific_checks = ""
        if qa_type == 'constraint_qa':
            type_specific_checks = """
**约束型QA特定检查（最重要）：**
- 这是**约束型内容生成**：Reference中有明确约束，Q和R主题差别大
- **核心约束遵守检查**：
  * 所有选项（包括错误选项）是否都遵守了Reference中的硬性约束？
  * 例如：如果约束是"只能喝粥/流食"，那么所有选项都不应推荐"蒸蛋"、"豆腐"等非流食
  * 例如：如果约束是"不能吃辣"，那么所有选项都不应推荐辣味餐厅
- **错误选项合理性**：
  * F1应该忽略约束但不违反（推荐通用但符合约束的内容）
  * F2应该部分理解约束（推荐约束边缘的内容，但未完全违反）
  * F3应该过度理解约束（过于严格但不荒谬）
"""
        elif qa_type == 'active_reminder_qa':
            type_specific_checks = """
**主动提醒型QA特定检查（最重要）：**
- 这是**主动提醒/偏好矫正**：Q试图违反R中提到的规则，AI需主动提醒
- **规则引用检查**：
  * 正确答案是否正确引用了Reference中的规则？
  * F1如果引用错误规则，这个规则是否是**真实存在但不相关**的规则？（不能虚构）
  * 规则编号是否合理？（如果Reference中提到"AI知识库已知XXX规则"，可以使用）
- **提醒主动性检查**：
  * T应该主动提醒并要求纠正
  * F1应该主动提醒但引用错误规则
  * F2应该被动回应，不主动提醒
  * F3应该部分提醒但接受变通方案
"""
        elif qa_type == 'progress_continuation_qa':
            type_specific_checks = """
**进度延续型QA特定检查：**
- 这是**历史目标承接与进度延续**：Q和R主题相近，需承接历史反馈
- **历史承接检查**：
  * 正确答案是否正确承接了Reference中的历史反馈和短板？
  * 错误选项是否合理地偏离了方向（重复已完成/方向偏离/过度前瞻）？
"""
        elif qa_type == 'conflict_resolution_qa':
            type_specific_checks = """
**矛盾推理型QA特定检查：**
- 这是**矛盾记忆的推理选择**：存在矛盾信息，需要推理最新/最准确的信息
- **信息更新检查**：
  * 正确答案是否正确识别了最新信息？
  * 错误选项是否合理地基于过时信息或部分理解？
"""
        
        prompt = f"""你是一个QAR选择题质量评估专家。请评估以下生成的QAR选择题是否合理，并决定是否需要改写。

**QA类型：{qa_type}**
{type_specific_checks}

**核心约束信息（来自Reference）：**
{key_constraints}

**原始生成要求：**
{original_prompt}

**生成的QAR选择题：**
问题：{question}

正确答案：{correct_answer}

错误选项：
1. {incorrect_answers[0] if len(incorrect_answers) > 0 else 'N/A'}
2. {incorrect_answers[1] if len(incorrect_answers) > 1 else 'N/A'}
3. {incorrect_answers[2] if len(incorrect_answers) > 2 else 'N/A'}

**选项长度统计：**
- 正确答案长度：{len(correct_answer)} 字符
- 错误选项1长度：{len(incorrect_answers[0]) if len(incorrect_answers) > 0 else 0} 字符
- 错误选项2长度：{len(incorrect_answers[1]) if len(incorrect_answers) > 1 else 0} 字符
- 错误选项3长度：{len(incorrect_answers[2]) if len(incorrect_answers) > 2 else 0} 字符
- 长度差异率：{length_variance:.1f}%

<evaluation_criteria>
**评估维度（必须逐项检查）：**

1. **选项长度一致性**（严格要求）
   - 所有选项长度差异必须在±10%以内
   - 当前差异率：{length_variance:.1f}%
   - 判断：{'✓ 合格' if length_variance <= 10 else '✗ 不合格 - 需要调整选项长度'}

2. **选项信息密度一致性**
   - 所有选项包含的信息量应该相近
   - 检查是否有选项明显过于简单或过于复杂
   - 检查是否有选项包含过多或过少的细节

3. **问题信息泄露检测**
   - 问题本身是否包含了答案的提示
   - 是否可以不看选项就能猜测答案方向
   - 问题措辞是否暗示了某个选项

4. **选项合理性**
   - 所有错误选项是否看起来合理且专业
   - 是否存在明显的"稻草人"选项（一眼就能排除的错误选项）
   - 错误选项是否与问题相关且有一定迷惑性

5. **结构一致性**
   - 所有选项是否使用相同的句式结构
   - 是否使用相似的表达方式和语气
   - 是否保持相同的详细程度

6. **可区分性**
   - 选项之间是否有明确的区别
   - 是否存在两个选项过于相似的情况
   - 正确答案是否因为某些特征（如长度、详细程度）而显得突出
</evaluation_criteria>

<output_format>
请按以下JSON格式输出评估结果：

{{
    "overall_quality": "excellent/good/needs_improvement",
    "needs_refresh": true/false,
    "evaluation_details": {{
        "length_consistency": {{
            "score": "pass/fail",
            "issue": "具体问题描述（如果有）",
            "suggestion": "改进建议（如果需要）"
        }},
        "information_density": {{
            "score": "pass/fail",
            "issue": "具体问题描述（如果有）",
            "suggestion": "改进建议（如果需要）"
        }},
        "question_leakage": {{
            "score": "pass/fail",
            "issue": "具体问题描述（如果有）",
            "suggestion": "改进建议（如果需要）"
        }},
        "option_reasonableness": {{
            "score": "pass/fail",
            "issue": "具体问题描述（如果有）",
            "suggestion": "改进建议（如果需要）"
        }},
        "structural_consistency": {{
            "score": "pass/fail",
            "issue": "具体问题描述（如果有）",
            "suggestion": "改进建议（如果需要）"
        }},
        "distinguishability": {{
            "score": "pass/fail",
            "issue": "具体问题描述（如果有）",
            "suggestion": "改进建议（如果需要）"
        }}
    }},
    "refresh_instruction": "如果需要改写，请提供具体的改写指导"
}}
</output_format>

请严格按照上述格式输出评估结果。"""
        
    elif action == 'qa_refresh':
        # QAR改写prompt
        question = data.get('question', '')
        correct_answer = data.get('correct_answer', '')
        incorrect_answers = data.get('incorrect_answers', [])
        original_prompt = data.get('original_prompt', '')
        evaluation_result = data.get('evaluation_result', {})
        refresh_instruction = data.get('refresh_instruction', '')
        reference = data.get('reference', {})
        key_constraints = data.get('key_constraints', '无明确约束')
        qa_type = data.get('qa_type', 'unknown')
        
        # 根据QA类型添加特定的改写要求
        type_specific_requirements = ""
        if qa_type == 'constraint_qa':
            type_specific_requirements = """
**约束型QA改写要点（最重要）：**
1. **严格遵守约束**：这是约束型QA，Reference中有明确的约束（如"只能喝粥/流食"、"不能吃辣"）
2. **错误选项设计**：
   - F1（忽略约束）：推荐通用内容，**不提及约束但也不违反约束**
     * 错误示例：约束是"只能流食"，F1推荐"蒸蛋豆腐餐厅"（违反了）
     * 正确示例：约束是"只能流食"，F1推荐"环境舒适的家常菜馆"（忽略但不违反）
   - F2（部分理解）：推荐约束边缘的内容，**理解不充分但未完全违反**
     * 错误示例：约束是"只能流食"，F2推荐"软面条"（面条不是流食）
     * 正确示例：约束是"只能流食"，F2推荐"软烂的米粥配蒸蛋"（包含流食但也有固体）
   - F3（过度理解）：推荐过于严格的内容，**但不能荒谬到完全不合理**
     * 错误示例：约束是"只能流食"，F3推荐"只喝营养液"（太极端）
     * 正确示例：约束是"只能流食"，F3推荐"只喝纯流质，连米粒都避免"（严格但不荒谬）
3. **避免重复**：各选项推荐不同类型的餐厅/食物，不要重复推荐相似的
"""
        elif qa_type == 'active_reminder_qa':
            type_specific_requirements = """
**主动提醒型QA改写要点（最重要）：**
1. **规则引用合理性**：
   - T应该正确引用Reference中提到的规则（包括"AI知识库已知"的规则）
   - F1应该引用**真实存在但不相关**的规则，不要虚构
   - 如果Reference提到"AI知识库已知财务SOP 4.1"，那么T可以引用它，F1可以引用其他真实的SOP
2. **提醒主动性梯度**：
   - T：主动提醒，正确引用规则，要求纠正
   - F1：主动提醒，但引用错误规则或夸大后果
   - F2：被动回应，不主动提醒（但可提供执行信息）
   - F3：部分提醒但接受变通方案（如"先做后补"）
"""
        elif qa_type == 'progress_continuation_qa':
            type_specific_requirements = """
**进度延续型QA改写要点：**
1. **历史承接准确性**：T应该正确承接Reference中的历史反馈和短板
2. **错误选项方向**：
   - F1：重复已完成的工作，忽略新反馈
   - F2：方向偏离，未解决关键短板
   - F3：过度前瞻，忽略当前需要解决的问题
"""
        elif qa_type == 'conflict_resolution_qa':
            type_specific_requirements = """
**矛盾推理型QA改写要点：**
1. **最新信息识别**：T应该正确识别最新/更准确的信息
2. **错误选项设计**：
   - F1：基于过时信息
   - F2：部分理解更新但推理错误
   - F3：过度推理，添加不存在的信息
"""
        
        prompt = f"""你是一个QAR选择题改写专家。基于质量评估结果，请改写以下QAR选择题。

**QA类型：{qa_type}**
{type_specific_requirements}

**⚠️ 核心约束（必须严格遵守）：**
{key_constraints}

**重要提醒：**
1. 上述约束信息来自Reference证据，是生成选项时的**硬性限制**
2. 所有选项（包括错误选项）都**不能违反**这些基本约束
3. 错误选项的"错误"应该体现在**理解程度、应用方式**上，而不是**完全违反约束**
4. 请仔细阅读上方针对**{qa_type}**类型的特定改写要点

**原始生成要求：**
{original_prompt}

**当前QAR选择题（存在问题）：**
问题：{question}

正确答案：{correct_answer}

错误选项：
1. {incorrect_answers[0] if len(incorrect_answers) > 0 else 'N/A'}
2. {incorrect_answers[1] if len(incorrect_answers) > 1 else 'N/A'}
3. {incorrect_answers[2] if len(incorrect_answers) > 2 else 'N/A'}

**质量评估结果：**
{_format_evaluation_result(evaluation_result)}

**改写指导：**
{refresh_instruction}

<refresh_requirements>
**改写要求（优先级从高到低）：**

**优先级1 - 内容合理性（最重要）：**
1. **严格遵守Reference中的核心约束**（见上方"核心约束"部分）
2. **所有选项都必须在约束范围内**，不能推荐明显违反约束的内容
3. **错误选项的错误设计：**
   - F1：完全忽略约束（推荐通用内容，但不违反约束）
   - F2：部分理解约束但不充分（例如：约束说"只能喝粥"，F2可能推荐"软面条"）
   - F3：过度理解约束（例如：约束说"不能吃硬的"，F3可能过度到"只能喝水"）
4. **避免选项之间的核心建议重复**（例如：正确答案推荐"粥"，错误选项就不应再推荐"粥"、"米糊"等相似食物）

**优先级2 - 形式要求：**
5. **严格控制选项长度在±5%以内**
6. **确保所有选项信息密度相近**
7. **保持所有选项的结构和表达方式一致**
8. **消除问题中的信息泄露**
9. **确保所有错误选项合理且有迷惑性**

**优先级3 - 灵活性：**
10. **Question、Correct_Answer都可以根据需要改写**
11. **保持原始生成要求中的核心内容和逻辑**
</refresh_requirements>

<output_format>
请按以下JSON格式输出改写后的QAR：

{{
    "Question": "改写后的问题",
    "Correct_Answer": "改写后的正确答案",
    "Incorrect_Answers": [
        "改写后的错误选项1",
        "改写后的错误选项2",
        "改写后的错误选项3"
    ],
    "refresh_notes": "改写说明（简要说明做了哪些调整）"
}}
</output_format>

请严格按照上述格式输出改写结果。"""
    
    else:
        raise ValueError(f"Invalid action: {action}")
        
    return prompt

def _format_evaluation_result(evaluation_result: Dict[str, Any]) -> str:
    """
    格式化评估结果为可读文本
    
    Args:
        evaluation_result: 评估结果字典
        
    Returns:
        str: 格式化后的文本
    """
    if not evaluation_result:
        return "无评估结果"
    
    formatted = []
    evaluation_details = evaluation_result.get('evaluation_details', {})
    
    for dimension, details in evaluation_details.items():
        if isinstance(details, dict):
            score = details.get('score', 'unknown')
            issue = details.get('issue', '')
            suggestion = details.get('suggestion', '')
            
            formatted.append(f"- {dimension}: {score}")
            if issue:
                formatted.append(f"  问题：{issue}")
            if suggestion:
                formatted.append(f"  建议：{suggestion}")
    
    return '\n'.join(formatted)