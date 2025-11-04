"""
提示词文件
存储 GPT-5 API 调用的提示词模板
"""

from typing import List, Dict, Optional


def get_employee_generation_prompt(total_count: int, teams: List[str]) -> str:
    """
    生成完整员工数据的主提示词
    采用单次调用策略，一次性生成所有员工信息

    参数:
        total_count: 总员工数
        teams: 团队列表

    返回:
        格式化的提示词字符串
    """
    import config

    prompt = f"""你是一位人力资源专家，需要为一家中国科技公司设计完整的员工名单和组织架构。

任务要求：
1. 生成 {total_count} 名员工的完整信息
2. 所有姓名必须是真实的中文姓名，且完全不重复
3. 姓名要多样化，避免使用过于常见的名字，包含不同的姓氏和名字组合

组织架构要求：
- 公司共有 {len(teams)} 个部门：{', '.join(teams)}
- 职别 (Rank) 分为三级：
  * Rank 1（{config.RANKS[1]}）：{config.TOP_LEADER_COUNT}人，是整个公司的最高领导
  * Rank 2（{config.RANKS[2]}）：{len(teams)}人，每个部门各1人，负责管理各自的部门
  * Rank 3（{config.RANKS[3]}）：{total_count - 1 - len(teams)}人，分配到各个部门

职位 (Title) 设计要求：
- Rank 1：公司级别的高层职位（如：首席执行官、总裁、董事长等）
- Rank 2：部门级别的管理职位（如：技术总监、市场总监、人力资源总监等），需要与所在部门匹配
- Rank 3：具体的执行职位（如：高级软件工程师、市场专员、产品经理等），需要与所在部门和工作内容匹配

部门分配要求：
- 每个部门都必须有员工
- 每个部门恰好有1名 Rank 2 的团队领导
- Rank 1 的大领导可以不属于任何特定部门，Team字段设为 "高层管理"
- 普通员工要合理分配到各个部门，确保每个部门都有足够的人员

输出格式要求：
请以 JSON 格式输出，包含一个 employees 数组，每个员工对象包含以下字段：
- name: 中文姓名（字符串）
- team: 所属团队（字符串，必须是以下之一：{', '.join(['高层管理'] + teams)}）
- rank: 职别（整数，1/2/3）
- title: 职位名称（字符串）

示例输出格式：
```json
{{
  "employees": [
    {{
      "name": "张伟华",
      "team": "高层管理",
      "rank": 1,
      "title": "首席执行官"
    }},
    {{
      "name": "李明",
      "team": "技术研发部",
      "rank": 2,
      "title": "技术总监"
    }},
    {{
      "name": "王芳",
      "team": "技术研发部",
      "rank": 3,
      "title": "高级软件工程师"
    }},
    {{
      "name": "陈静",
      "team": "市场部",
      "rank": 2,
      "title": "市场总监"
    }},
    {{
      "name": "刘洋",
      "team": "市场部",
      "rank": 3,
      "title": "市场专员"
    }}
  ]
}}
```

重要提醒：
1. 确保所有 {total_count} 个姓名完全不同，不能有任何重复
2. 确保职别分配严格符合要求：{config.TOP_LEADER_COUNT}个Rank 1，{len(teams)}个Rank 2，{total_count - 1 - len(teams)}个Rank 3
3. 确保每个部门都有1个Rank 2的领导
4. 职位名称要专业、真实、符合中国企业的习惯
5. 姓名要自然、多样化，体现中国姓名的丰富性
6. 只返回JSON数据，不要包含任何其他说明文字

现在请生成完整的 {total_count} 名员工数据。"""

    return prompt


def get_batch_employee_prompt(batch_num: int, batch_size: int, teams: List[str], existing_names: List[str], needs_leaders: bool = False) -> str:
    """
    分批生成员工数据的提示词

    参数:
        batch_num: 当前批次号（从1开始）
        batch_size: 每批生成的员工数量
        teams: 团队列表
        existing_names: 已生成的员工姓名列表（避免重复）
        needs_leaders: 是否需要生成领导（第1批需要）

    返回:
        格式化的提示词字符串
    """
    import config

    if needs_leaders:
        # 第1批：包含大领导和团队领导
        prompt = f"""你是一位人力资源专家，需要为一家中国科技公司生成员工信息。

这是第 {batch_num} 批数据，需要生成 {batch_size} 名员工：
- 1名 Rank 1（{config.RANKS[1]}）：公司最高领导
- {config.TEAM_LEADER_COUNT}名 Rank 2（{config.RANKS[2]}）：每个部门各1人
- {batch_size - (config.TOP_LEADER_COUNT + config.TEAM_LEADER_COUNT)}名 Rank 3（{config.RANKS[3]}）：分配到各个部门

部门列表：{', '.join(teams)}

要求：
1. 生成 {batch_size} 个不重复的真实中文姓名
2. 姓名要多样化，避免常见重复
3. 确保职别分配准确
4. 每个部门都要有1名团队领导
5. 普通员工要合理分配到各部门

输出格式（JSON）：
```json
{{
  "employees": [
    {{"name": "张伟华", "team": "高层管理", "rank": 1, "title": "首席执行官"}},
    {{"name": "李明", "team": "技术研发部", "rank": 2, "title": "技术总监"}},
    {{"name": "王芳", "team": "技术研发部", "rank": 3, "title": "高级软件工程师"}},
    ...
  ]
}}
```

重要：只返回JSON数据，不要其他文字。"""
    else:
        # 后续批次：只生成普通员工
        existing_names_str = ", ".join(existing_names) if existing_names else "无"
        prompt = f"""你是一位人力资源专家，需要为一家中国科技公司生成员工信息。

这是第 {batch_num} 批数据，需要生成 {batch_size} 名普通员工（Rank 3）。

部门列表：{', '.join(teams)}

已生成的员工姓名：{existing_names_str}

要求：
1. 生成 {batch_size} 个不重复的真实中文姓名
2. 姓名必须与已有姓名完全不同
3. 全部为 Rank 3（{config.RANKS[3]}）
4. 合理分配到各个部门
5. 职位要与部门匹配且多样化

输出格式（JSON）：
```json
{{
  "employees": [
    {{"name": "赵强", "team": "技术研发部", "rank": 3, "title": "前端工程师"}},
    {{"name": "刘芳", "team": "市场部", "rank": 3, "title": "市场专员"}},
    ...
  ]
}}
```

重要：只返回JSON数据，不要其他文字。生成恰好 {batch_size} 名员工。"""

    return prompt


# ========== Hard Skill 相关提示词 ==========

def get_skill_universe_prompt(unique_titles: List[str], teams: List[str]) -> str:
    """
    生成技能集合的提示词

    目标：生成一个闭合的、互斥的Hard Skill集合

    参数:
        unique_titles: 所有唯一职位列表
        teams: 团队列表

    返回:
        格式化的提示词字符串
    """

    # 导入配置（避免循环导入）
    import config

    # 展示所有职位
    title_display = unique_titles

    import config
    prompt = f"""你是一位人力资源和技能管理专家。现在需要为一家中国科技公司的{config.TOTAL_EMPLOYEES}名员工建立完整的Hard Skill（硬技能）体系。

## 任务背景
公司有 {len(teams)} 个部门：{', '.join(teams)}
共有约 {len(unique_titles)} 种不同的职位。

## 所有职位（共{len(unique_titles)}个）
{chr(10).join([f"- {title}" for title in title_display])}


## 核心任务
请分析以上所有职位，生成一个**闭合的Hard Skill集合**，用于后续为每个员工分配技能。

## 严格要求

### 1. 互斥性（Mutual Exclusivity）- 最重要！
技能之间必须**完全互斥**，不能有以下情况：

❌ **禁止父子关系**:
- 不能同时包含 "Python" 和 "Python3"
- 不能同时包含 "Java" 和 "Java8"
- 不能同时包含 "编程" 和 "Python"（"Python"是"编程"的子类）
- 不能同时包含 "数据处理" 和 "数据分析"（概念重叠）

❌ **禁止重复**:
- 不能同时包含 "Excel" 和 "Microsoft Excel"
- 不能同时包含 "Photoshop" 和 "PS"

✅ **正确示例**:
- 编程语言类: ["Python", "Java", "JavaScript", "Go", "C++", "Rust"] （平级技能）
- 前端技术: ["React", "Vue.js", "Angular"] （平级框架）
- 数据库: ["MySQL", "PostgreSQL", "MongoDB", "Redis"] （平级产品）

### 2. 技能集合大小
- 总计需要 **{config.MIN_SKILL_UNIVERSE_SIZE}-{config.MAX_SKILL_UNIVERSE_SIZE}** 个互斥的Hard Skill
- 覆盖所有职位所需的技能范围
- 既不能太少（覆盖不全），也不能太多（难以管理）

### 3. 技能分类
请将技能按以下类别组织：

**技术类**:
- 编程语言（如 Python, Java）
- 前端技术（如 React, Vue.js）
- 后端技术（如 Spring Boot, Django）
- 数据库（如 MySQL, MongoDB）
- 云计算与DevOps（如 AWS, Docker）
- 数据科学（如 数据分析, 机器学习）

**业务类**:
- 市场营销（如 SEO优化, 内容营销）
- 销售能力（如 客户关系管理, 商务谈判）
- 设计能力（如 UI设计, UX设计）
- 财务能力（如 财务分析, 预算管理）

**管理类**:
- 项目管理（如 敏捷开发, Scrum）
- 团队管理（如 团队建设, 绩效管理）
- 战略规划（如 商业模式设计, 战略分析）

**工具类**:
- 办公软件（如 Excel, PowerPoint）
- 协作工具（如 Jira, Slack）
- 设计工具（如 Figma, Photoshop）

### 4. 技能粒度
- 技能应该是**具体的、可验证的**
- 不要太宽泛（❌"技术能力"）
- 不要太具体（❌"Python 3.9.5"）
- 适中粒度（✅"Python", ✅"React", ✅"数据分析"）

## 输出格式

请严格按照以下 JSON 格式输出：

```json
{{
  "skill_universe": [
    {{
      "category": "编程语言",
      "skills": ["Python", "Java", "JavaScript", "Go", "C++", "Rust", "PHP", "Ruby"]
    }},
    {{
      "category": "前端技术",
      "skills": ["React", "Vue.js", "Angular", "HTML5", "CSS3", "TypeScript"]
    }},
    {{
      "category": "后端技术",
      "skills": ["Spring Boot", "Django", "Flask", "Express", "Node.js"]
    }},
    {{
      "category": "数据库",
      "skills": ["MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch"]
    }},
    {{
      "category": "云计算与DevOps",
      "skills": ["AWS", "Azure", "Docker", "Kubernetes", "Jenkins", "Git"]
    }},
    {{
      "category": "数据科学",
      "skills": ["数据分析", "机器学习", "深度学习", "数据可视化", "统计分析"]
    }},
    ... （其他类别）
  ],
  "total_count": 52,
  "validation": {{
    "no_duplicates": true,
    "no_parent_child": true,
    "mutually_exclusive": true,
    "explanation": "所有技能均为平级技能，无父子关系，无重复，完全互斥"
  }}
}}
```

## 重要提醒
1. **必须确保技能完全互斥** - 这是最核心的要求！
2. 技能名称使用中文或常用英文（如 Python, React）
3. 只返回JSON数据，不要包含任何其他说明文字
4. 技能总数控制在 {config.MIN_SKILL_UNIVERSE_SIZE}-{config.MAX_SKILL_UNIVERSE_SIZE} 之间

现在请生成完整的技能集合。"""

    return prompt


def get_skill_assignment_prompt(batch_employees: List[Dict],
                                  skill_universe: List[str],
                                  batch_num: int) -> str:
    """
    为一批员工分配技能的提示词

    参数:
        batch_employees: 员工信息列表
        skill_universe: 可用技能集合
        batch_num: 批次号

    返回:
        格式化的提示词字符串
    """

    # 导入配置
    import config

    # 构建员工信息列表
    employee_info = []
    for emp in batch_employees:
        rank_info = f"Rank {emp['rank']}"
        if emp['rank'] == 1:
            rank_info += " (大领导)"
        elif emp['rank'] == 2:
            rank_info += " (团队领导)"
        else:
            rank_info += " (普通员工)"

        employee_info.append(
            f"- {emp['name']} | {emp['title']} | {emp['team']} | {rank_info}"
        )

    prompt = f"""你是一位人力资源和技能管理专家。现在需要为以下 {len(batch_employees)} 名员工分配Hard Skill（硬技能）。

## 员工信息（批次 {batch_num}）
{chr(10).join(employee_info)}

## 可用技能集合（从以下列表中选择）
{', '.join(skill_universe)}

## 分配规则

### 1. 技能数量与强度要求

#### 技能强度等级定义
每个技能必须标注能力强度等级：
- **strong（精通）**: 核心专长，能够独立解决复杂问题，指导他人
- **medium（熟练）**: 能够熟练使用该技能完成工作任务
- **low（了解）**: 具备基础知识，能够在指导下使用

#### 根据员工职别分配技能
- **Rank 1（{config.RANKS[1]}）**: 分配 {config.SKILL_COUNT_BY_RANK[1]['min']}-{config.SKILL_COUNT_BY_RANK[1]['max']} 个技能
  * 包含战略管理类技能（如 商业模式设计、战略分析）
  * 包含团队管理类技能（如 团队建设、绩效管理）
  * 可包含部分技术或业务技能（体现综合能力）
  * 强度分布: {config.SKILL_LEVEL_DISTRIBUTION[1]['strong'][0]}-{config.SKILL_LEVEL_DISTRIBUTION[1]['strong'][1]}个strong, {config.SKILL_LEVEL_DISTRIBUTION[1]['medium'][0]}-{config.SKILL_LEVEL_DISTRIBUTION[1]['medium'][1]}个medium, {config.SKILL_LEVEL_DISTRIBUTION[1]['low'][0]}-{config.SKILL_LEVEL_DISTRIBUTION[1]['low'][1]}个low

- **Rank 2（{config.RANKS[2]}）**: 分配 {config.SKILL_COUNT_BY_RANK[2]['min']}-{config.SKILL_COUNT_BY_RANK[2]['max']} 个技能
  * 包含团队管理类技能
  * 包含本部门核心专业技能
  * 可包含项目管理类技能
  * 强度分布: {config.SKILL_LEVEL_DISTRIBUTION[2]['strong'][0]}-{config.SKILL_LEVEL_DISTRIBUTION[2]['strong'][1]}个strong, {config.SKILL_LEVEL_DISTRIBUTION[2]['medium'][0]}-{config.SKILL_LEVEL_DISTRIBUTION[2]['medium'][1]}个medium, {config.SKILL_LEVEL_DISTRIBUTION[2]['low'][0]}-{config.SKILL_LEVEL_DISTRIBUTION[2]['low'][1]}个low

- **Rank 3（{config.RANKS[3]}）**: 分配 {config.SKILL_COUNT_BY_RANK[3]['min']}-{config.SKILL_COUNT_BY_RANK[3]['max']} 个技能
  * 专注于本职工作相关的专业技能
  * 技能应与职位高度匹配
  * 强度分布: {config.SKILL_LEVEL_DISTRIBUTION[3]['strong'][0]}-{config.SKILL_LEVEL_DISTRIBUTION[3]['strong'][1]}个strong, {config.SKILL_LEVEL_DISTRIBUTION[3]['medium'][0]}-{config.SKILL_LEVEL_DISTRIBUTION[3]['medium'][1]}个medium, {config.SKILL_LEVEL_DISTRIBUTION[3]['low'][0]}-{config.SKILL_LEVEL_DISTRIBUTION[3]['low'][1]}个low

### 2. 技能匹配原则
- **技术研发部**: 优先分配编程语言、前后端技术、数据库、云计算等技术类技能
- **市场部**: 优先分配市场营销、内容营销、社交媒体运营等市场类技能
- **产品设计部**: 优先分配 UI设计、UX设计、Figma、原型设计等设计类技能
- **销售部**: 优先分配销售能力、客户关系管理、商务谈判等销售类技能
- **运营部**: 优先分配数据分析、项目管理、流程优化等运营类技能
- **财务部**: 优先分配财务分析、预算管理、成本控制等财务类技能
- **人力资源部**: 优先分配团队管理、绩效管理、人才培养等HR类技能

- **具体职位**: 技能必须与Title精确匹配
  * 例如："前端工程师" → React(strong), HTML5(medium), CSS3(medium), JavaScript(low)
  * 例如："数据分析师" → 数据分析(strong), Python(medium), Excel(medium), 数据可视化(low)
  * 例如："产品经理" → 原型设计(strong), 需求分析(strong), Figma(medium), 项目管理(low)

### 3. 技能强度分配原则
- **strong 技能**: 应该是员工的核心专长，与职位最相关的1-3个技能
- **medium 技能**: 是工作中经常使用的技能，构成技能集合的主体
- **low 技能**: 辅助性技能，了解但不精通
- 强度分配要合理：不能所有技能都是strong，也不能所有都是low

### 4. 重要约束
- **只能从提供的技能集合中选择**，不能创造新技能
- **每个员工的技能不能重复**（员工内部去重）
- **每个技能必须标注强度等级**: strong, medium, 或 low
- 技能选择要合理、真实、符合中国企业实际情况

## 输出格式

请严格按照以下 JSON 格式输出（注意每个技能包含skill和level两个字段）：

```json
{{
  "assignments": [
    {{
      "name": "张昱宸",
      "title": "技术总监",
      "rank": 2,
      "hard_skills": [
        {{"skill": "Python", "level": "strong"}},
        {{"skill": "Java", "level": "strong"}},
        {{"skill": "Docker", "level": "medium"}},
        {{"skill": "MySQL", "level": "medium"}},
        {{"skill": "团队管理", "level": "medium"}},
        {{"skill": "敏捷开发", "level": "low"}}
      ]
    }},
    {{
      "name": "王芳",
      "title": "前端工程师",
      "rank": 3,
      "hard_skills": [
        {{"skill": "React", "level": "strong"}},
        {{"skill": "Vue.js", "level": "medium"}},
        {{"skill": "TypeScript", "level": "medium"}},
        {{"skill": "HTML5", "level": "low"}}
      ]
    }},
    ... （其他员工）
  ]
}}
```

## 重要提醒
1. 必须为所有 {len(batch_employees)} 名员工分配技能
2. 技能数量必须符合职别要求
3. 技能必须与职位和团队高度相关
4. 每个技能必须包含 skill 和 level 两个字段
5. 只返回JSON数据，不要包含任何其他说明文字

现在请为这批员工分配技能。"""

    return prompt


# ========== Communication Style 相关提示词 ==========

def get_communication_style_assignment_prompt(batch_employees: List[Dict],
                                               communication_style_universe: Dict,
                                               batch_num: int) -> str:
    """
    为一批员工分配Communication Style的提示词

    参数:
        batch_employees: 员工信息列表（包含姓名、职位、团队、硬技能）
        communication_style_universe: 完整的沟通风格维度定义
        batch_num: 批次号

    返回:
        格式化的提示词字符串
    """

    # 提取维度信息
    dimensions = communication_style_universe.get("communication_style_universe", [])

    # 格式化维度说明
    dimension_descriptions = []
    for dim in dimensions:
        dim_name = dim["dimension"]
        dim_desc = dim["description"]
        levels = dim["levels"]

        level_desc = f"""
**{dim_name}** ({dim_desc}):
- High: {levels["high"]["label"]} - {levels["high"]["description"]}
- Medium: {levels["medium"]["label"]} - {levels["medium"]["description"]}
- Low: {levels["low"]["label"]} - {levels["low"]["description"]}"""
        dimension_descriptions.append(level_desc)

    dimensions_text = "\n".join(dimension_descriptions)

    # 格式化员工信息
    employee_info_list = []
    for i, emp in enumerate(batch_employees, 1):
        # 兼容大小写键名
        name = emp.get("Name") or emp.get("name", "未知")
        title = emp.get("Title") or emp.get("title", "未知")
        team = emp.get("Team") or emp.get("team", "未知")
        rank = emp.get("Rank") or emp.get("rank", 3)

        # 解析硬技能（如果有）
        hard_skills = emp.get("Hard_Skills") or emp.get("hard_skills", [])
        if isinstance(hard_skills, str):
            import json
            try:
                hard_skills = json.loads(hard_skills)
            except:
                hard_skills = []

        # 展示所有技能
        skills_summary = []
        for skill_item in hard_skills:
            if isinstance(skill_item, dict):
                skill_name = skill_item.get("skill", "")
                skill_level = skill_item.get("level", "")
                skills_summary.append(f"{skill_name}({skill_level})")

        skills_text = ", ".join(skills_summary) if skills_summary else "无技能信息"

        rank_label = "大领导" if rank == 1 else ("团队领导" if rank == 2 else "普通员工")

        employee_info_list.append(
            f"{i}. {name} | {title} | {team} | Rank {rank}({rank_label}) | 技能: {skills_text}"
        )

    employees_text = "\n".join(employee_info_list)

    # 计算总批次数
    import config
    total_batches = (config.TOTAL_EMPLOYEES + config.COMMUNICATION_STYLE_BATCH_SIZE - 1) // config.COMMUNICATION_STYLE_BATCH_SIZE

    # 获取实际的维度数量
    num_dimensions = len(dimensions)

    prompt = f"""你是一位专业的组织行为学专家。请基于员工的职位、团队、硬技能等信息，为每位员工分配{num_dimensions}个沟通风格维度的级别。

## 沟通风格维度说明
{dimensions_text}

## 分配原则

### 1. 基于职位特征推断
- **高管/管理层** (Rank 1-2)：倾向于 Formal、Concise、Direct、Probing
- **技术人员**：倾向于 Technical、Minimal humor、Probing
- **销售/市场人员**：倾向于 Warm、Frequent emoji、Friendly
- **设计师**：倾向于 Casual、Detailed、Occasional humor、Clarifying
- **财务/HR人员**：倾向于 Semi-formal、Balanced、Neutral

### 2. 基于团队文化推断
- **技术研发部**：Direct、Technical、Minimal humor、Rare emoji
- **产品设计部**：Balanced、Moderate verbosity、Clarifying、Occasional humor
- **市场部/销售部**：Warm、Frequent emoji、Friendly
- **运营部**：Semi-formal、Moderate、Balanced
- **财务部/人力资源部**：Formal、Concise、Neutral、Accepting

### 3. 基于硬技能推断
- **技术编程技能** (如 Python, Java, React)：Technical jargon、Concise、Direct
- **数据分析技能** (如 数据分析, Excel)：Detailed、Probing、Meticulous
- **设计技能** (如 Figma, Photoshop)：Moderate verbosity、Occasional humor、Balanced
- **管理技能** (如 团队管理, 项目管理)：Semi-formal、Balanced directness、Clarifying
- **销售/市场技能** (如 客户关系管理, 内容营销)：Warm、Friendly

### 4. 基于职别推断
- **Rank 1 (大领导)**：Formal、Concise、Direct、Neutral
- **Rank 2 (团队领导)**：Semi-formal、Balanced、Clarifying
- **Rank 3 (普通员工)**：根据具体职位和团队灵活分配，保持多样性

### 5. 保持多样性
- 避免所有员工都是相同的风格组合
- 即使是同一团队，不同职位的员工也应该有差异
- 考虑个体差异，不要完全按模板分配

## 员工信息

**批次**: {batch_num}/{total_batches}
**本批次员工数**: {len(batch_employees)}

{employees_text}

## 输出格式

请严格按照以下 JSON 格式输出（不要添加任何其他文字）：

**重要**: "name" 字段必须使用上面列出的员工实际姓名，不要使用"员工1"、"员工2"等编号！

```json
{{
  "batch_number": {batch_num},
  "assignments": [
    {{
      "name": "{batch_employees[0].get('name') or batch_employees[0].get('Name', '张伟') if batch_employees else '张伟'}",
      "communication_style": {{
        "Formality": "Formal/Semi-formal/Casual",
        "Verbosity": "Detailed/Moderate/Concise",
        "Humor": "Frequent/Occasional/Minimal",
        "Jargon_Usage": "Technical/Balanced/Plain",
        "Emoji_Usage": "Frequent/Occasional/Rare",
        "Directness": "Direct/Balanced/Indirect",
        "Warmth": "Warm/Friendly/Neutral",
        "Questioning_Style": "Probing/Clarifying/Accepting"
      }},
      "reasoning": "简要说明为什么这样分配（1-2句话）"
    }},
    {{
      "name": "{batch_employees[1].get('name') or batch_employees[1].get('Name', '李明') if len(batch_employees) > 1 else '李明'}",
      "communication_style": {{
        ...
      }},
      "reasoning": "..."
    }}
    // ... 继续为剩余的 {len(batch_employees)} 位员工分配
  ]
}}
```

## 重要提示

1. **"name" 字段必须使用员工的实际中文姓名（如上面员工信息中列出的），不要使用"员工1"、"员工姓名"等占位符**
2. **每个维度必须精确使用指定的三个级别之一的英文标签**（区分大小写）
3. **确保为所有 {len(batch_employees)} 位员工分配**
4. **reasoning字段帮助理解分配逻辑，但不会存入最终数据**
5. **综合考虑职位、团队、技能、职别等多个因素**
6. **只返回JSON数据，不要包含任何其他说明文字**

现在请为这批员工分配沟通风格。"""

    return prompt


class PromptTemplate:
    """
    提示词模板管理类
    """

    @staticmethod
    def get_main_prompt(total_count: int, teams: List[str]) -> str:
        """获取主提示词（一次性生成）"""
        return get_employee_generation_prompt(total_count, teams)

    @staticmethod
    def get_batch_prompt(batch_num: int, batch_size: int, teams: List[str], existing_names: List[str], needs_leaders: bool = False) -> str:
        """获取分批生成提示词"""
        return get_batch_employee_prompt(batch_num, batch_size, teams, existing_names, needs_leaders)

    @staticmethod
    def get_skill_universe_prompt(unique_titles: List[str], teams: List[str]) -> str:
        """获取技能集合生成提示词"""
        return get_skill_universe_prompt(unique_titles, teams)

    @staticmethod
    def get_skill_assignment_prompt(batch_employees: List[Dict], skill_universe: List[str], batch_num: int) -> str:
        """获取技能分配提示词"""
        return get_skill_assignment_prompt(batch_employees, skill_universe, batch_num)

    @staticmethod
    def get_communication_style_assignment_prompt(batch_employees: List[Dict], communication_style_universe: Dict, batch_num: int) -> str:
        """获取沟通风格分配提示词"""
        return get_communication_style_assignment_prompt(batch_employees, communication_style_universe, batch_num)

    # ==================== Phase 4: Task Generation Prompts ====================

    @staticmethod
    def get_communication_style_adjustment_prompt(project_topic: str, project_description: str, team_members: List[Dict]) -> str:
        """获取沟通风格调整提示词（根据项目架构调整communication style）"""
        return get_communication_style_adjustment_prompt_phase4(project_topic, project_description, team_members)

    # ==================== Phase 4 (New): Topic-Driven Task Generation Prompts ====================

    @staticmethod
    def get_major_topics_generation_prompt() -> str:
        """获取大 Topic 生成提示词（Stage 1）"""
        return get_major_topics_generation_prompt_new()

    @staticmethod
    def get_sub_topics_generation_prompt(major_topic: Dict) -> str:
        """获取小 Topic 生成提示词（Stage 2）"""
        return get_sub_topics_generation_prompt_new(major_topic)

    @staticmethod
    def get_team_selection_prompt(sub_topic: Dict, all_employees: List[Dict]) -> str:
        """获取团队选择提示词（Stage 3）"""
        return get_team_selection_prompt_new(sub_topic, all_employees)

    @staticmethod
    def get_subtask_generation_and_sequencing_prompt(sub_topic: Dict, team_members: List[Dict]) -> str:
        """获取 Subtask 生成和排序提示词（Stage 4）"""
        return get_subtask_generation_and_sequencing_prompt_new(sub_topic, team_members)

    @staticmethod
    def get_subtask_assignment_prompt(sequenced_subtasks: List[Dict], team_members: List[Dict]) -> str:
        """获取 Subtask 分配提示词（Stage 5）"""
        return get_subtask_assignment_prompt_new(sequenced_subtasks, team_members)
def get_communication_style_adjustment_prompt_phase4(project_topic: str, project_description: str, team_members: List[Dict]) -> str:
    """
    Prompt 3: 根据项目架构调整团队成员的沟通风格
    """
    import config

    # 格式化团队成员及其原始沟通风格
    members_info = []
    for i, member in enumerate(team_members, 1):
        cs = member['communication_style']
        cs_details = "\n     ".join([f"* {k}: {v}" for k, v in cs.items()])
        
        members_info.append(f"""{i}. {member['user_name']} - {member['title']} (Rank {member['rank']})
   原始沟通风格（来自Phase 3的通用评估）:
     {cs_details}""")
    
    members_text = "\n\n".join(members_info)

    # 统计团队架构
    rank_counts = {}
    rank_names = {1: [], 2: [], 3: []}
    for member in team_members:
        rank = member['rank']
        rank_counts[rank] = rank_counts.get(rank, 0) + 1
        rank_names[rank].append(member['user_name'])

    prompt = f"""# 任务：根据项目架构调整团队成员的沟通风格

## 核心理念

员工的沟通风格不是固定不变的，而是会根据项目的团队架构动态调整：
- 在只有1个总监的项目中，总监会更权威、更直接
- 在有多个总监的项目中，总监之间需要更多协作和妥协
- CEO在不同架构下的沟通方式也会调整
- 基层员工的沟通风格受到上层架构的影响

## 项目信息
- 项目主题: {project_topic}
- 项目描述: {project_description}

## 团队成员及原始沟通风格

{members_text}

## 团队架构分析
- Rank 1: {rank_counts.get(1, 0)}人 - {', '.join(rank_names[1])}
- Rank 2: {rank_counts.get(2, 0)}人 - {', '.join(rank_names[2])}
- Rank 3: {rank_counts.get(3, 0)}人 - {', '.join(rank_names[3])}
- 总人数: {len(team_members)}人

## 调整指导原则

**架构影响因素**：
1. **总监数量影响**：
   - 只有1个总监：该总监更权威、更直接、更formal
   - 2-3个总监：需要协作，略微降低directness，增加warmth
   - 4+个总监：需要大量协调，显著增加warmth

2. **CEO影响**：
   - 1个CEO配1个总监：CEO更直接，更有决策权
   - 1个CEO配多个总监：CEO需要平衡各方

3. **团队规模影响**：
   - 小团队({config.SUB_TOPIC_TEAM_SIZE['min']}-{config.SUB_TOPIC_TEAM_SIZE['min'] + (config.SUB_TOPIC_TEAM_SIZE['max'] - config.SUB_TOPIC_TEAM_SIZE['min']) // 3}人)：更casual，更direct
   - 中团队({config.SUB_TOPIC_TEAM_SIZE['min'] + (config.SUB_TOPIC_TEAM_SIZE['max'] - config.SUB_TOPIC_TEAM_SIZE['min']) // 3 + 1}-{config.SUB_TOPIC_TEAM_SIZE['min'] + 2 * (config.SUB_TOPIC_TEAM_SIZE['max'] - config.SUB_TOPIC_TEAM_SIZE['min']) // 3}人)：balanced
   - 大团队({config.SUB_TOPIC_TEAM_SIZE['min'] + 2 * (config.SUB_TOPIC_TEAM_SIZE['max'] - config.SUB_TOPIC_TEAM_SIZE['min']) // 3 + 1}+人)：更formal，更structured

**调整幅度**：
- 每个维度可以调整1-2个级别（例如：Casual → Semi-formal → Formal）
- 不是所有维度都需要调整
- 如果原始风格已经很适合，可以保持不变

## 8个沟通风格维度

以下是Communication Style的8个维度及其3个级别：

1. **Formality（正式程度）**: Formal / Semi-formal / Casual
2. **Verbosity（详细程度）**: Detailed / Moderate / Concise
3. **Humor（幽默程度）**: Frequent / Occasional / Minimal
4. **Jargon_Usage（术语使用）**: Technical / Balanced / Plain
5. **Emoji_Usage（表情符号使用）**: Frequent / Occasional / Rare
6. **Directness（直接程度）**: Direct / Balanced / Indirect
7. **Warmth（温暖程度）**: Warm / Friendly / Neutral
8. **Questioning_Style（提问风格）**: Probing / Clarifying / Accepting

## 输出格式

请严格按照以下JSON格式输出（不要添加任何其他文字）：

```json
{{
  "project_architecture_summary": "简要描述这个项目的架构特点（1个总监、10人小团队等）",
  "adjusted_styles": [
    {{
      "user_name": "顾行远",
      "rank": 1,
      "original_style": {{
        "Formality": "Semi-formal",
        "Verbosity": "Moderate",
        "Humor": "Minimal",
        "Jargon_Usage": "Balanced",
        "Emoji_Usage": "Rare",
        "Directness": "Balanced",
        "Warmth": "Neutral",
        "Questioning_Style": "Probing"
      }},
      "adjusted_style": {{
        "Formality": "Formal",
        "Verbosity": "Moderate",
        "Humor": "Minimal",
        "Jargon_Usage": "Balanced",
        "Emoji_Usage": "Rare",
        "Directness": "Direct",
        "Warmth": "Neutral",
        "Questioning_Style": "Probing"
      }},
      "adjustments_made": {{
        "Formality": {{
          "from": "Semi-formal",
          "to": "Formal",
          "reason": "作为唯一Rank 1，在小团队中需要更formal的权威"
        }},
        "Directness": {{
          "from": "Balanced",
          "to": "Direct",
          "reason": "决策链短，需要更direct的沟通"
        }}
      }},
      "overall_reasoning": "整体调整理由（1-2句话）"
    }}
  ]
}}
```

## 重要提示

- **必须为所有 {len(team_members)} 名成员都返回调整结果**（即使某个成员不需要调整，也要包含在 adjusted_styles 数组中）
- 如果某个成员的风格已经很适合，adjusted_style 可以和 original_style 保持一致，但必须包含该成员
- 不要大幅度改变所有维度，只调整受架构影响明显的维度
- 主要调整的维度：Formality, Directness, Warmth
- 次要调整的维度：Verbosity, Questioning_Style
- 较少调整的维度：Humor, Emoji_Usage, Jargon_Usage
- user_name必须是实际存在的员工姓名
- 所有维度的值必须严格使用上述定义的标签（区分大小写）
- 如果某个维度不需要调整，在adjustments_made中不要包含它
- 只返回JSON数据，不要包含任何其他说明文字

现在请根据项目架构调整团队成员的沟通风格。记住：adjusted_styles 数组必须包含全部 {len(team_members)} 名成员！"""
    
    return prompt

# ==================== Phase 5: 任务时间线分配 ====================

def get_task_timeline_assignment_prompt(
    project_info: dict,
    members_with_subtasks: list,
    start_date: str = "2025-01-01",
    end_date: str = "2025-12-31"
) -> str:
    """
    生成任务时间线分配的prompt

    Args:
        project_info: 项目信息字典 (project_number, project_topic, project_description)
        members_with_subtasks: 成员和任务列表
        start_date: 项目开始日期
        end_date: 项目结束日期

    Returns:
        完整的prompt字符串
    """
    import config
    import json

    # 构建任务列表信息
    all_tasks = []
    for member in members_with_subtasks:
        user_name = member.get('user_name')
        rank = member.get('rank')
        for subtask in member.get('subtasks', []):
            # 安全地获取 subtask_id，如果缺少则跳过
            subtask_id = subtask.get('subtask_id')
            if subtask_id is None:
                print(f"  ⚠ 警告: 成员 {user_name} 的 subtask 缺少 subtask_id: {subtask.get('subtask', 'N/A')}")
                continue

            all_tasks.append({
                'subtask_id': subtask_id,
                'user_name': user_name,
                'rank': rank,
                'subtask': subtask.get('subtask', 'N/A'),
                'phase': subtask.get('phase', 'Unknown'),
                'required_skills': subtask.get('required_skills', [])
            })

    total_tasks = len(all_tasks)

    prompt = f"""
你是一位专业的项目管理专家，擅长制定项目时间线和任务排序。

# 项目信息
- **项目编号**: {project_info.get('project_number')}
- **项目名称**: {project_info.get('project_topic')}
- **项目描述**: {project_info.get('project_description')}
- **项目时间范围**: {start_date} 至 {end_date} （共365天）
- **任务总数**: {total_tasks} 个subtasks

# 你的任务
请根据项目特性和任务内容，为以下所有subtasks分配合理的deadline（截止日期）。

# 任务列表
{json.dumps(all_tasks, ensure_ascii=False, indent=2)}

# 排序和时间分配要求

## 1. **Phase 顺序（最重要！）**

每个任务都有一个 `phase` 字段，表示它所属的项目阶段。**必须严格按照以下 phase 顺序分配 deadline**：

1. **Strategy & Planning**（战略与规划）
   - 时间段建议：项目开始后 0-2 个月
   - 包括：战略规划、需求调研、市场分析、项目规划

2. **Design & Architecture**（设计与架构）
   - 时间段建议：项目开始后 1-4 个月
   - 包括：系统架构设计、数据库设计、UI/UX设计、技术选型

3. **Development & Implementation**（开发与实现）
   - 时间段建议：项目开始后 3-9 个月
   - 包括：功能开发、API开发、前端/后端实现、集成开发

4. **Testing & Optimization**（测试与优化）
   - 时间段建议：项目开始后 8-11 个月
   - 包括：功能测试、性能优化、安全测试、Bug修复

5. **Deployment & Launch**（部署与上线）
   - 时间段建议：项目开始后 10-12 个月
   - 包括：环境部署、数据迁移、用户培训、上线发布

**⚠️ 关键规则**：
- 后一个 phase 的所有任务 deadline 必须晚于前一个 phase
- 同一 phase 内的任务可以有重叠的 deadline（并行执行）
- Phase 之间可以有适当重叠（如 Design 和 Development），但必须保持总体顺序

## 2. 其他排序原则

- **Rank 级别考虑**:
  - Rank 1（高层）任务通常在每个 phase 的早期
  - Rank 2（总监）任务在 phase 的中期
  - Rank 3（员工）任务根据具体内容分布

- **合理性原则**:
  - 任务deadline应合理分布在365天内
  - 避免所有任务集中在某个时间段
  - 考虑任务复杂度：复杂任务给予更长的准备时间
  - 考虑团队负载：同一个人的多个任务不应deadline过于集中

## 3. ⚠️ 硬性约束
- **所有deadline必须在 {start_date} 到 {end_date} 之间（包含边界）**
- **每个subtask必须分配一个deadline，不能遗漏**
- **deadline格式必须为 YYYY-MM-DD**
- **必须严格遵守 phase 顺序：Strategy & Planning → Design & Architecture → Development & Implementation → Testing & Optimization → Deployment & Launch**
- **同一 phase 内的任务，Rank 1 的 deadline 应早于或等于 Rank 3 的 deadline**

# 输出格式要求

请以JSON格式返回结果，格式如下：

```json
{{
  "project_number": {project_info.get('project_number')},
  "project_topic": "{project_info.get('project_topic')}",
  "timeline_summary": {{
    "start_date": "{start_date}",
    "end_date": "{end_date}",
    "total_tasks": {total_tasks},
    "phase_breakdown": {{
      "前期（1-3月）": <任务数>,
      "中期（4-8月）": <任务数>,
      "后期（9-12月）": <任务数>
    }}
  }},
  "task_timeline": [
    {{
      "subtask_id": 1,
      "user_name": "张伟华",
      "deadline": "2025-02-15",
      "phase": "前期",
      "reasoning": "CEO战略规划任务，需在项目初期完成以指导后续工作"
    }},
    {{
      "subtask_id": 2,
      "user_name": "陈慧兰",
      "deadline": "2025-03-20",
      "phase": "前期",
      "reasoning": "UX设计需在战略明确后开始，为开发提供设计依据"
    }},
    ...（所有{total_tasks}个任务）
  ]
}}
```

**重要提示**：
1. `task_timeline` 数组必须**严格包含**上面任务列表中的所有 {total_tasks} 个任务，一个都不能少，一个都不能多
2. 每个任务必须有 `subtask_id`, `user_name`, `deadline`, `phase`, `reasoning` 五个字段
3. `subtask_id` 是整数，必须与输入的任务列表中的 `subtask_id` **完全一致**
4. **禁止重复**：每个 `subtask_id` 只能出现一次，不能重复
5. **禁止遗漏**：输入列表中的每个任务都必须在输出中出现
6. **禁止创造**：不能添加输入列表中不存在的 `subtask_id`
7. `deadline` 必须是 YYYY-MM-DD 格式的字符串
8. `phase` 必须是 "前期"、"中期" 或 "后期" 之一
9. `reasoning` 简要说明（10-30字）为什么这个任务安排在这个时间点
10. **只返回 JSON 数据，不要包含任何其他说明文字**

**验证清单**（在返回前自查）：
✓ task_timeline 数组长度 = {total_tasks}
✓ 所有 subtask_id 都在输入列表中
✓ 没有重复的 subtask_id
✓ 没有遗漏任何任务

请开始分配任务时间线。记住：只输出上述格式的 JSON，不要添加任何解释或说明文字。
"""
    return prompt


# ==================== Phase 4 (New): Topic-Driven Task Generation Prompt Functions ====================

def get_major_topics_generation_prompt_new() -> str:
    """
    Stage 1: 生成大 Topic

    要求：
    1. 生成 NUM_MAJOR_TOPICS 个大项目主题
    2. 每个主题跨度大、互不重复
    3. 适合科技公司的业务场景
    4. 每个主题包含 topic 和 description

    返回格式：
    {
      "major_topics": [
        {
          "topic_id": "MAJOR_001",
          "topic": "智能制造平台",
          "description": "构建覆盖生产设备监控、质量追溯、供应链协同的智能制造解决方案..."
        },
        ...
      ]
    }
    """
    import config

    prompt = f"""你是一位资深的项目规划专家。现在需要为一家中国科技公司规划多个大型项目主题。

## 公司背景
这是一家综合性科技公司，拥有以下部门：
- 技术研发部：负责软件开发、系统架构、技术创新
- 产品设计部：负责产品规划、用户体验、界面设计
- 市场部：负责市场推广、品牌建设、用户增长
- 销售部：负责商务拓展、客户关系、销售管理
- 运营部：负责业务运营、流程优化、数据分析
- 财务部：负责财务管理、成本控制、投资决策
- 人力资源部：负责招聘、培训、绩效管理

公司员工共 300 人，涵盖技术、产品、管理、运营等多个领域。

## 核心任务
请生成 **{config.NUM_MAJOR_TOPICS}** 个大型项目主题（Major Topics），这些主题将作为公司的战略级项目。

## 严格要求

### 1. 主题多样性和跨度
项目主题必须跨度大、类型多样，覆盖不同的业务领域和技术方向。

✅ **正确示例**（跨度大、类型多样）：
- 智能制造平台（制造业+IoT）
- 企业资产管理系统（企业服务+财务）
- 跨境电商平台（电商+国际化）
- 智慧医疗系统（医疗+AI）
- 供应链金融平台（金融+供应链）

❌ **禁止**（主题重复、跨度小）：
- 智能客服系统
- 智能推荐系统
- 智能分析系统
（都是"智能xxx"，类型单一）

### 2. 业务场景要求
每个主题必须：
- 是完整的、可独立运作的业务系统
- 有明确的目标用户和应用场景
- 需要跨部门协作完成
- 具有商业价值和技术挑战

### 3. 描述要求
每个主题的 description 需要包含：
- 项目的核心目标和价值（2-3句话）
- 主要功能模块或业务范围（3-5点）
- 预期覆盖的用户群体或应用场景

description 长度：150-300字

## 输出格式

请严格按照以下 JSON 格式输出：

```json
{{
  "major_topics": [
    {{
      "topic_id": "MAJOR_001",
      "topic": "智能制造平台",
      "description": "构建覆盖生产设备监控、质量追溯、供应链协同的智能制造解决方案。核心功能包括：实时设备监控与预警、生产数据采集与分析、质量管理与追溯、供应链协同管理、生产计划优化。面向制造企业提供数字化转型解决方案，帮助企业提升生产效率、降低运营成本。"
    }},
    {{
      "topic_id": "MAJOR_002",
      "topic": "企业资产管理系统",
      "description": "开发全生命周期的企业资产管理平台，涵盖资产采购、使用、维护、报废全流程管理。核心功能包括：资产登记与编码、资产分配与调拨、维护保养计划、资产盘点与审计、折旧计算与报表。面向中大型企业的资产管理部门，提高资产利用率和管理效率。"
    }},
    ...（共{config.NUM_MAJOR_TOPICS}个）
  ]
}}
```

## 重要提醒
1. 必须生成恰好 **{config.NUM_MAJOR_TOPICS}** 个主题
2. topic_id 格式：MAJOR_001, MAJOR_002, ..., MAJOR_{config.NUM_MAJOR_TOPICS:03d}
3. 每个主题的 topic 名称要简洁（4-8个字）
4. 每个主题的 description 要详细（150-300字）
5. 主题之间要有明显的区别，不能重复或重叠
6. 只返回 JSON 数据，不要包含任何其他说明文字

请开始生成 {config.NUM_MAJOR_TOPICS} 个大型项目主题。
"""
    return prompt


def get_sub_topics_generation_prompt_new(major_topic: Dict) -> str:
    """
    Stage 2: 拆分小 Topic

    输入：
    - major_topic: {"topic_id": "MAJOR_001", "topic": "...", "description": "..."}

    要求：
    1. 生成 NUM_SUB_TOPICS_PER_MAJOR 个小 topic
    2. 小 topic 之间必须互不重复、非父子关系
    3. 每个小 topic 是独立的、可并行的项目

    返回格式：
    {
      "sub_topics": [
        {
          "sub_topic_id": "SUB_001_001",
          "parent_topic_id": "MAJOR_001",
          "topic": "生产设备实时监控系统",
          "description": "...",
          "reasoning": "..."
        },
        ...
      ]
    }
    """
    import config

    topic_id = major_topic.get('topic_id', 'MAJOR_XXX')
    topic = major_topic.get('topic', '未命名主题')
    description = major_topic.get('description', '')

    # 提取主题编号（例如 MAJOR_001 -> 001）
    topic_number = topic_id.replace('MAJOR_', '')

    prompt = f"""你是一位资深的项目拆解专家。现在需要将一个大型项目主题拆分为多个可并行执行的子项目。

## 大型项目主题

**主题ID**: {topic_id}
**主题名称**: {topic}
**主题描述**: {description}

## 核心任务

请将这个大型主题拆分为 **{config.NUM_SUB_TOPICS_PER_MAJOR}** 个小型项目（Sub Topics）。每个小型项目是一个独立的、可并行开发的子系统或模块。

## 严格要求

### 1. 互斥性和独立性（最重要！）

小 topic 之间必须**完全互斥**、**独立并行**，不能有以下情况：

❌ **禁止父子关系**：
- 大 topic: "智能制造平台"
  - ✗ 错误拆分: "开发制造执行系统" 和 "开发制造执行系统的生产排程模块"
    （后者是前者的子模块，存在父子关系）

  - ✓ 正确拆分: "生产设备实时监控系统"、"质量追溯管理系统"、"供应链协同平台"
    （三个独立的子系统，可以并行开发）

❌ **禁止重复或重叠**：
- ✗ 错误: "用户管理系统" 和 "用户权限管理系统"（功能重叠）
- ✓ 正确: "用户管理系统" 和 "订单管理系统"（功能独立）

❌ **禁止依赖关系**：
- ✗ 错误: "数据采集模块" 和 "数据分析模块"（后者依赖前者）
- ✓ 正确: "设备监控系统" 和 "质量管理系统"（可并行）

### 2. 完整性要求

每个小 topic 必须：
- 是一个完整的、可独立部署的子系统
- 有明确的功能边界和目标
- 有自己的用户界面或API接口
- 可以独立测试和上线

### 3. 与大主题的关系

所有小 topic 加起来应该：
- 覆盖大 topic 的主要功能范围
- 但不需要100%覆盖（可以聚焦核心功能）
- 每个小 topic 都是大 topic 的重要组成部分

### 4. 描述和推理要求

- **description**: 150-250字，详细说明该子项目的功能范围、核心模块、目标用户
- **reasoning**: 50-100字，解释为什么这是一个独立的子项目，以及它在大主题中的作用

## 输出格式

请严格按照以下 JSON 格式输出：

```json
{{
  "sub_topics": [
    {{
      "sub_topic_id": "SUB_{topic_number}_001",
      "parent_topic_id": "{topic_id}",
      "topic": "生产设备实时监控系统",
      "description": "开发覆盖工厂全域的设备实时监控平台，实现设备状态采集、异常预警、远程控制等功能。核心模块包括：设备数据采集、实时监控看板、异常检测与预警、设备远程控制、历史数据分析。面向生产管理人员和设备维护人员，帮助企业及时发现设备问题，减少停机时间。",
      "reasoning": "设备监控是智能制造的基础，需要独立的数据采集和监控系统，可以作为独立子系统并行开发和部署。"
    }},
    {{
      "sub_topic_id": "SUB_{topic_number}_002",
      "parent_topic_id": "{topic_id}",
      "topic": "质量追溯管理系统",
      "description": "构建产品全生命周期的质量管理和追溯平台，实现从原材料到成品的全程质量跟踪。核心模块包括：质量数据采集、批次管理、缺陷记录与分析、追溯查询、质量报表。面向质量管理部门，提升产品质量管控能力，满足合规要求。",
      "reasoning": "质量管理是独立的业务流程，与设备监控并行但不依赖，可以独立开发和部署。"
    }},
    ...（共{config.NUM_SUB_TOPICS_PER_MAJOR}个）
  ]
}}
```

## 重要提醒

1. 必须生成恰好 **{config.NUM_SUB_TOPICS_PER_MAJOR}** 个小 topic
2. sub_topic_id 格式：SUB_{topic_number}_001, SUB_{topic_number}_002, ..., SUB_{topic_number}_{config.NUM_SUB_TOPICS_PER_MAJOR:03d}
3. 每个 topic 名称要清晰具体（6-12个字）
4. 每个 description 要详细（150-250字）
5. 每个 reasoning 要简明（50-100字）
6. 小 topic 之间必须独立、互不重复、无父子关系
7. 只返回 JSON 数据，不要包含任何其他说明文字

请开始拆分 "{topic}" 为 {config.NUM_SUB_TOPICS_PER_MAJOR} 个独立的子项目。
"""
    return prompt


def get_team_selection_prompt_new(sub_topic: Dict, all_employees: List[Dict]) -> str:
    """
    Stage 3: 选择团队成员

    输入：
    - sub_topic: {"sub_topic_id": "SUB_001_001", "topic": "...", "description": "..."}
    - all_employees: 所有员工的完整信息（300人）

    要求：
    1. 根据 sub_topic 需求从 all_employees 中选择合适团队
    2. 必须至少 1 个 Rank 1 + 1 个 Rank 2
    3. 团队规模在配置范围内
    4. 优先选择技能匹配的成员

    返回格式：
    {
      "sub_topic_id": "SUB_001_001",
      "selected_members": [
        {
          "user_name": "张伟华",
          "selection_reason": "作为CEO，具备战略分析能力..."
        },
        ...
      ]
    }
    """
    import config

    sub_topic_id = sub_topic.get('sub_topic_id', 'SUB_XXX_XXX')
    topic = sub_topic.get('topic', '未命名项目')
    description = sub_topic.get('description', '')

    # 格式化员工信息（只保留关键字段，优化 token 使用）
    employees_info = []
    for i, emp in enumerate(all_employees, 1):
        # 格式化 hard_skills
        skills_str = ", ".join([f"{s['skill']}({s['proficiency']})" for s in emp.get('hard_skills', [])])

        # 简化 communication_style（只显示关键维度）
        cs = emp.get('communication_style', {})
        cs_brief = f"{cs.get('Formality', 'N/A')}/{cs.get('Directness', 'N/A')}/{cs.get('Warmth', 'N/A')}"

        employees_info.append(f"{i}. {emp['user_name']} | {emp['title']} | Rank {emp['rank']} | {emp['team']}")
        employees_info.append(f"   技能: {skills_str}")
        employees_info.append(f"   风格: {cs_brief}")

    employees_list = "\n".join(employees_info)

    prompt = f"""你是一位资深的团队组建专家。现在需要为一个项目从公司全体员工中选择合适的团队成员。

## 项目信息

**项目ID**: {sub_topic_id}
**项目名称**: {topic}
**项目描述**: {description}

## 团队配置要求

### 1. 团队规模
- 总人数：{config.SUB_TOPIC_TEAM_SIZE['min']} ~ {config.SUB_TOPIC_TEAM_SIZE['max']} 人
- **必须**至少有 **{config.SUB_TOPIC_TEAM_SIZE['rank_1_min']}** 个 Rank 1 成员（公司高层领导）
- **必须**至少有 **{config.SUB_TOPIC_TEAM_SIZE['rank_2_min']}** 个 Rank 2 成员（部门总监）
- 其余为 Rank 3 成员（普通员工）

### 2. 技能匹配原则
- 优先选择 hard_skills 与项目需求匹配的成员
- 确保团队具备项目所需的核心技能
- 技能的 proficiency 越高越好（strong > medium > low）

### 3. Communication Style 考虑
- 团队成员的沟通风格要互补
- Rank 1/2 通常更 Formal、Direct
- 考虑团队协作的有效性

### 4. 部门多样性
- 优先考虑跨部门协作
- 根据项目需求选择相关部门的成员

## 可选员工列表（共{len(all_employees)}人）

{employees_list}

## 输出格式

请严格按照以下 JSON 格式输出：

```json
{{
  "sub_topic_id": "{sub_topic_id}",
  "selected_members": [
    {{
      "user_name": "张伟华",
      "selection_reason": "作为CEO（Rank 1），具备商业模式画布、战略分析等strong级技能，适合领导智能制造平台的战略规划和整体推进。沟通风格Formal且Direct，能有效指导项目方向。"
    }},
    {{
      "user_name": "李明",
      "selection_reason": "作为技术总监（Rank 2），拥有系统架构、云计算等strong级技能，能够设计设备监控系统的技术架构。作为技术研发部负责人，能调动技术资源支持项目。"
    }},
    {{
      "user_name": "王芳",
      "selection_reason": "作为高级软件工程师（Rank 3），精通Java、Python等编程语言，以及数据库设计，能够负责监控系统的核心功能开发。"
    }},
    ...（共 {config.SUB_TOPIC_TEAM_SIZE['min']} ~ {config.SUB_TOPIC_TEAM_SIZE['max']} 人）
  ],
  "team_summary": {{
    "total_members": 25,
    "rank_1_count": 1,
    "rank_2_count": 2,
    "rank_3_count": 22,
    "key_skills_covered": ["系统架构", "Java", "Python", "数据库设计", "前端开发", "测试", "项目管理"]
  }}
}}
```

## 重要提醒

1. **必须**选择至少 {config.SUB_TOPIC_TEAM_SIZE['rank_1_min']} 个 Rank 1 和 {config.SUB_TOPIC_TEAM_SIZE['rank_2_min']} 个 Rank 2
2. 团队总人数必须在 {config.SUB_TOPIC_TEAM_SIZE['min']} ~ {config.SUB_TOPIC_TEAM_SIZE['max']} 人之间
3. 每个成员的 user_name 必须**完全匹配**上面列表中的姓名（不能修改或编造）
4. selection_reason 要详细（50-100字），说明：
   - 该成员的职位和 Rank
   - 该成员的核心技能及熟练度
   - 为什么这些技能适合这个项目
   - （如果是 Rank 1/2）该成员的领导力和资源调动能力
5. team_summary 中的 key_skills_covered 要列出团队覆盖的关键技能
6. 只返回 JSON 数据，不要包含任何其他说明文字

请根据项目需求，从 {len(all_employees)} 名员工中选择合适的团队成员。
"""
    return prompt


def get_subtask_generation_and_sequencing_prompt_new(sub_topic: Dict, team_members: List[Dict]) -> str:
    """
    Stage 4: 生成并排序 Subtask

    输入：
    - sub_topic: 小 topic 信息
    - team_members: 团队成员列表（已选定）

    要求：
    1. 拆解项目为独立的 subtask
    2. 按照时间线排序（Strategy → Design → Development → Testing → Deployment）
    3. 每个 subtask 包含 required_skills

    返回格式：
    {
      "subtasks": [
        {
          "subtask": "进行设备监控需求调研",
          "phase": "Strategy & Planning",
          "required_skills": ["需求分析", "行业研究"],
          "reasoning": "..."
        },
        ...
      ]
    }
    """
    import config

    sub_topic_id = sub_topic.get('sub_topic_id', 'SUB_XXX_XXX')
    topic = sub_topic.get('topic', '未命名项目')
    description = sub_topic.get('description', '')

    # 格式化团队成员信息
    team_info = []
    for i, member in enumerate(team_members, 1):
        skills_str = ", ".join([f"{s['skill']}({s['proficiency']})" for s in member.get('hard_skills', [])])
        team_info.append(f"{i}. {member['user_name']} - {member['title']} (Rank {member['rank']})")
        team_info.append(f"   技能: {skills_str}")

    team_list = "\n".join(team_info)

    # 计算最小任务数（每人至少5个任务）
    min_total_tasks = len(team_members) * config.MIN_SUBTASKS_PER_MEMBER
    recommended_min_tasks = len(team_members) * 8  # 推荐最少每人8个任务
    recommended_max_tasks = len(team_members) * 12  # 推荐最多每人12个任务

    prompt = f"""你是一位资深的项目拆解和任务规划专家。现在需要将一个项目拆解为**非常细粒度**的子任务（subtasks），并按照时间线排序。

## 项目信息

**项目ID**: {sub_topic_id}
**项目名称**: {topic}
**项目描述**: {description}

## 团队成员（共{len(team_members)}人）

{team_list}

## ⚠️ 核心要求：任务必须拆得足够细！

这是**最重要**的要求：任务必须拆分到足够细的粒度，确保每个成员都能分配到充足的任务。

### 什么是"足够细"的拆分？

**示例1：需求调研阶段**
❌ **太粗**（只有1个任务）：
- "进行需求调研"

✅ **足够细**（拆分为8个具体任务）：
- "调研目标用户群体画像"
- "收集竞品功能清单"
- "访谈内部业务部门需求"
- "整理现有系统痛点列表"
- "编写需求调研问卷"
- "组织用户焦点小组讨论"
- "分析调研数据并输出报告"
- "制定需求优先级矩阵"

**示例2：系统设计阶段**
❌ **太粗**（只有2个任务）：
- "设计系统架构"
- "设计数据库"

✅ **足够细**（拆分为12个具体任务）：
- "设计系统总体架构图"
- "设计前后端分离方案"
- "设计微服务拆分策略"
- "设计API网关架构"
- "设计缓存架构方案"
- "设计消息队列架构"
- "设计数据库主从架构"
- "设计用户表结构"
- "设计订单表结构"
- "设计权限表结构"
- "设计索引优化方案"
- "编写数据库设计文档"

**示例3：开发实现阶段**
❌ **太粗**（只有3个任务）：
- "开发后端API"
- "开发前端页面"
- "开发数据库"

✅ **足够细**（拆分为20+个具体任务）：
- "实现用户注册接口"
- "实现用户登录接口"
- "实现密码重置接口"
- "实现用户信息查询接口"
- "实现用户信息更新接口"
- "实现订单创建接口"
- "实现订单查询接口"
- "实现订单状态更新接口"
- "实现支付回调接口"
- "开发用户注册页面"
- "开发用户登录页面"
- "开发用户中心页面"
- "开发订单列表页面"
- "开发订单详情页面"
- "开发支付页面"
- "实现前端表单验证"
- "实现前端状态管理"
- "实现前端路由配置"
- "对接后端API"
- "编写前端单元测试"
- ...（还可以继续细分）

## 核心任务

请完成以下两个步骤：

### 步骤1：拆解项目为 Subtasks（必须足够细粒度！）

**任务数量要求**：
- **最少**：{min_total_tasks} 个任务（{len(team_members)}人 × {config.MIN_SUBTASKS_PER_MEMBER}任务/人）
- **推荐范围**：{recommended_min_tasks} ~ {recommended_max_tasks} 个任务（每人 8-12 个任务）
- **目标**：尽可能多地拆分，确保每个成员都有充足的任务

**任务拆解原则**：
1. **细粒度**：将每个工作拆分到最小的可执行单元
2. **独立性**：每个 subtask 必须是独立的、可并行的
3. **具体性**：每个 subtask 要清晰、具体、可执行
4. **完整性**：列出项目的所有工作项，不要遗漏任何环节
5. **互斥性**：不能有父子关系或重复

**如何做到足够细？**
- 将"设计"拆分为多个具体设计项（架构、数据库、接口、UI等）
- 将"开发"拆分为每个具体的功能模块或接口
- 将"测试"拆分为每个功能的测试项
- 将"文档"拆分为每份具体的文档
- 将"部署"拆分为每个具体的部署步骤

❌ **禁止的拆分方式**（太粗、有父子关系）：
- "开发系统" 和 "开发系统的登录模块"（父子关系）
- "设计UI"（太粗，应拆分为具体的每个页面）
- "编写文档"（太粗，应拆分为具体的每份文档）
- "开发后端"（太粗，应拆分为具体的每个接口或模块）

✅ **正确的拆分方式**（足够细、独立并行）：
- "设计用户注册页面UI"、"设计用户登录页面UI"、"设计用户中心页面UI"
- "实现用户注册接口"、"实现用户登录接口"、"实现用户信息查询接口"
- "编写API接口文档"、"编写部署运维文档"、"编写用户使用手册"

### 步骤2：按时间线排序
将所有 subtasks 按照项目的典型时间线排序，分为以下5个阶段：

**Phase 1: Strategy & Planning（战略与规划）**
- 需求调研、市场分析
- 项目规划、可行性分析
- 商业模式设计

**Phase 2: Design & Architecture（设计与架构）**
- 系统架构设计
- 数据库设计
- UI/UX设计
- 技术选型

**Phase 3: Development & Implementation（开发与实现）**
- 功能模块开发
- API开发
- 前端/后端实现
- 集成开发

**Phase 4: Testing & Optimization（测试与优化）**
- 功能测试
- 性能优化
- 安全测试
- Bug修复

**Phase 5: Deployment & Launch（部署与上线）**
- 环境部署
- 数据迁移
- 用户培训
- 上线发布

**排序要求**：
- 为每个 subtask 标注所属的 phase
- 按照 phase 的先后顺序组织任务（Strategy & Planning → Design & Architecture → Development & Implementation → Testing & Optimization → Deployment & Launch）
- 同一 phase 内的任务可以并行，但 phase 之间有先后关系

## 输出格式

请严格按照以下 JSON 格式输出（以下展示细粒度拆分示例）：

```json
{{
  "subtasks": [
    {{
      "subtask": "调研目标用户群体画像",
      "phase": "Strategy & Planning",
      "required_skills": ["需求分析", "用户研究"],
      "reasoning": "明确目标用户是谁，他们的特征、需求和痛点，为产品定位提供基础。"
    }},
    {{
      "subtask": "收集竞品功能清单",
      "phase": "Strategy & Planning",
      "required_skills": ["行业研究", "竞品分析"],
      "reasoning": "了解市场上同类产品的功能和特点，为功能规划提供参考。"
    }},
    {{
      "subtask": "访谈内部业务部门需求",
      "phase": "Strategy & Planning",
      "required_skills": ["需求分析", "沟通能力"],
      "reasoning": "收集内部业务部门的实际需求和期望，确保产品符合业务目标。"
    }},
    {{
      "subtask": "编写需求调研问卷",
      "phase": "Strategy & Planning",
      "required_skills": ["需求分析", "问卷设计"],
      "reasoning": "设计调研问卷，系统化地收集用户需求和反馈。"
    }},
    {{
      "subtask": "组织用户焦点小组讨论",
      "phase": "Strategy & Planning",
      "required_skills": ["用户研究", "沟通能力"],
      "reasoning": "通过焦点小组深入了解用户真实需求和痛点。"
    }},
    {{
      "subtask": "设计系统总体架构图",
      "phase": "Design & Architecture",
      "required_skills": ["系统架构", "架构设计"],
      "reasoning": "绘制系统的整体架构图，明确各模块之间的关系和数据流。"
    }},
    {{
      "subtask": "设计前后端分离方案",
      "phase": "Design & Architecture",
      "required_skills": ["系统架构", "技术选型"],
      "reasoning": "确定前后端分离的技术栈和通信方式，提高开发效率和可维护性。"
    }},
    {{
      "subtask": "设计用户表结构",
      "phase": "Design & Architecture",
      "required_skills": ["数据库设计", "数据建模"],
      "reasoning": "设计用户相关的数据表结构，包括字段、类型、索引等。"
    }},
    {{
      "subtask": "设计订单表结构",
      "phase": "Design & Architecture",
      "required_skills": ["数据库设计", "数据建模"],
      "reasoning": "设计订单相关的数据表结构，支持订单的创建、查询和状态管理。"
    }},
    {{
      "subtask": "设计权限表结构",
      "phase": "Design & Architecture",
      "required_skills": ["数据库设计", "权限设计"],
      "reasoning": "设计RBAC权限模型的数据表，支持灵活的权限管理。"
    }},
    {{
      "subtask": "设计用户注册页面UI",
      "phase": "Design & Architecture",
      "required_skills": ["UI设计", "用户体验"],
      "reasoning": "设计用户注册页面的界面布局、交互流程和视觉效果。"
    }},
    {{
      "subtask": "设计用户登录页面UI",
      "phase": "Design & Architecture",
      "required_skills": ["UI设计", "用户体验"],
      "reasoning": "设计用户登录页面的界面布局和交互流程。"
    }},
    {{
      "subtask": "实现用户注册接口",
      "phase": "Development & Implementation",
      "required_skills": ["Java", "Spring Boot", "API开发"],
      "reasoning": "开发用户注册的后端接口，包括参数验证、密码加密、数据存储。"
    }},
    {{
      "subtask": "实现用户登录接口",
      "phase": "Development & Implementation",
      "required_skills": ["Java", "Spring Boot", "JWT"],
      "reasoning": "开发用户登录接口，包括身份验证、Token生成和返回。"
    }},
    {{
      "subtask": "实现用户信息查询接口",
      "phase": "Development & Implementation",
      "required_skills": ["Java", "Spring Boot", "MySQL"],
      "reasoning": "开发用户信息查询接口，支持根据用户ID获取用户详细信息。"
    }},
    {{
      "subtask": "实现用户信息更新接口",
      "phase": "Development & Implementation",
      "required_skills": ["Java", "Spring Boot", "MySQL"],
      "reasoning": "开发用户信息更新接口，支持用户修改个人信息。"
    }},
    {{
      "subtask": "实现密码重置接口",
      "phase": "Development & Implementation",
      "required_skills": ["Java", "Spring Boot", "邮件服务"],
      "reasoning": "开发密码重置功能，包括邮件验证和密码更新。"
    }},
    {{
      "subtask": "开发用户注册页面",
      "phase": "Development & Implementation",
      "required_skills": ["React", "JavaScript", "前端开发"],
      "reasoning": "实现用户注册页面的前端代码，包括表单、验证和提交逻辑。"
    }},
    {{
      "subtask": "开发用户登录页面",
      "phase": "Development & Implementation",
      "required_skills": ["React", "JavaScript", "前端开发"],
      "reasoning": "实现用户登录页面的前端代码，包括表单、状态管理和Token存储。"
    }},
    {{
      "subtask": "开发用户中心页面",
      "phase": "Development & Implementation",
      "required_skills": ["React", "JavaScript", "前端开发"],
      "reasoning": "实现用户中心页面，展示用户信息和提供信息修改功能。"
    }}
  ],
  "summary": {{
    "total_subtasks": {recommended_min_tasks},
    "phase_distribution": {{
      "Strategy & Planning": {int(recommended_min_tasks * 0.15)},
      "Design & Architecture": {int(recommended_min_tasks * 0.20)},
      "Development & Implementation": {int(recommended_min_tasks * 0.40)},
      "Testing & Optimization": {int(recommended_min_tasks * 0.15)},
      "Deployment & Launch": {int(recommended_min_tasks * 0.10)}
    }}
  }}
}}
```

**注意**：上述示例仅展示部分任务，实际需要继续列出所有任务直到达到 {recommended_min_tasks}~{recommended_max_tasks} 个。

## ⚠️ 重要提醒（必读！）

1. **任务数量要求**：
   - **最少**：{min_total_tasks} 个任务（每人至少{config.MIN_SUBTASKS_PER_MEMBER}个）
   - **推荐**：{recommended_min_tasks} ~ {recommended_max_tasks} 个任务（每人 8-12 个）
   - **目标**：尽可能多地拆分，不要遗漏任何工作项

2. **细粒度要求**（最关键！）：
   - 将每个"设计"拆分为具体的设计项（每个页面、每个模块、每个表）
   - 将每个"开发"拆分为具体的功能（每个接口、每个页面、每个组件）
   - 将每个"测试"拆分为具体的测试项（每个功能、每个场景）
   - 将每个"文档"拆分为具体的文档（API文档、用户手册、部署文档等）

3. **格式要求**：
   - subtask 名称要清晰具体（6-15个字），**直接描述要做的事情**
   - phase 必须是 5 个阶段之一（Strategy & Planning, Design & Architecture, Development & Implementation, Testing & Optimization, Deployment & Launch）
   - 任务按照 phase 顺序排列（不需要编号，系统会自动生成）

4. **质量要求**：
   - required_skills 要准确列出所需技能（参考团队成员的技能列表）
   - reasoning 要简明扼要（30-80字）
   - 任务之间必须独立、互不重复、无父子关系
   - **严格要求**：只返回纯 JSON 数据，不要包含任何注释（不要使用 // 或 /* */）
   - 不要包含任何其他说明文字

请开始拆解项目 "{topic}" 并按时间线排序任务。记住：
1. 任务要拆得足够细，数量要达到 {recommended_min_tasks}~{recommended_max_tasks} 个
2. 输出纯 JSON，不要添加任何注释或说明文字
"""
    return prompt


def get_subtask_assignment_prompt_new(sequenced_subtasks: List[Dict], team_members: List[Dict]) -> str:
    """
    Stage 5: 分配 Subtask 到成员

    输入：
    - sequenced_subtasks: 已按时间线排序的 subtask 列表（按 phase 顺序）
    - team_members: 团队成员列表（带 hard_skills）

    要求：
    1. 根据成员的 hard_skills 分配 subtask
    2. 确保每个成员至少 MIN_SUBTASKS_PER_MEMBER 个任务
    3. 为每个分配提供详细的 CoT 推理原因

    返回格式：
    {
      "task_assignments": [
        {
          "user_name": "张伟华",
          "rank": 1,
          "assigned_subtasks": [
            {
              "subtask": "进行设备监控需求调研",
              "phase": "Strategy & Planning",
              "required_skills": ["需求分析", "行业研究"],
              "assignment_reason": "张伟华作为CEO..."
            },
            ...
          ],
          "total_assigned": 8
        },
        ...
      ]
    }
    """
    import config

    # 格式化团队成员信息
    team_info = []
    for i, member in enumerate(team_members, 1):
        skills_str = ", ".join([f"{s['skill']}({s['proficiency']})" for s in member.get('hard_skills', [])])
        team_info.append(f"{i}. {member['user_name']} - {member['title']} (Rank {member['rank']})")
        team_info.append(f"   技能: {skills_str}")

    team_list = "\n".join(team_info)

    # 格式化 subtask 列表
    subtask_info = []
    for i, subtask in enumerate(sequenced_subtasks, 1):
        required_skills_str = ", ".join(subtask.get('required_skills', []))
        subtask_info.append(
            f"{i}. {subtask.get('subtask', '未命名任务')} "
            f"({subtask.get('phase', 'N/A')})"
        )
        # subtask_id 在分配后才会生成，这里不显示
        subtask_info.append(f"   需要技能: {required_skills_str}")

    subtask_list = "\n".join(subtask_info)

    prompt = f"""你是一位资深的任务分配专家。现在需要将已经排序好的任务分配给团队成员，确保每个人都能充分发挥自己的技能。

## 团队成员（共{len(team_members)}人）

{team_list}

## 待分配任务（共{len(sequenced_subtasks)}个，已按时间线排序）

{subtask_list}

## 分配原则

### 1. 技能匹配
- **优先匹配技能**：任务的 required_skills 要与成员的 hard_skills 匹配
- **技能熟练度**：优先分配给该技能 proficiency 为 strong 的成员
- **如果多人都有该技能**：选择熟练度更高的，或者工作量更轻的成员

### 2. 工作量平衡
- **最低要求**：每个成员至少分配 **{config.MIN_SUBTASKS_PER_MEMBER}** 个任务
- **平衡原则**：尽量让每个成员的任务数量相近
- **推荐范围**：每人 {config.MIN_SUBTASKS_PER_MEMBER} ~ {config.MIN_SUBTASKS_PER_MEMBER + 3} 个任务

### 3. Rank 级别考虑
- **Rank 1（高层领导）**：
  - 优先分配 "Strategy & Planning" 阶段的任务
  - 适合：战略规划、需求调研、商业模式设计
  - 任务数量可以略少（{config.MIN_SUBTASKS_PER_MEMBER}个左右）

- **Rank 2（部门总监）**：
  - 优先分配 "Design & Architecture" 和管理类任务
  - 适合：系统架构、技术选型、团队管理
  - 任务数量适中（{config.MIN_SUBTASKS_PER_MEMBER}-{config.MIN_SUBTASKS_PER_MEMBER + 2}个）

- **Rank 3（普通员工）**：
  - 主要分配 "Development & Implementation" 和 "Testing & Optimization" 任务
  - 适合：功能开发、测试、文档编写
  - 任务数量可以略多（{config.MIN_SUBTASKS_PER_MEMBER}-{config.MIN_SUBTASKS_PER_MEMBER + 3}个）

### 4. 阶段覆盖
- 确保每个阶段都有足够的人员覆盖
- 同一阶段的任务可以分配给多个人（并行执行）

## 输出格式

请严格按照以下 JSON 格式输出：

```json
{{
  "task_assignments": [
    {{
      "user_name": "张伟华",
      "rank": 1,
      "assigned_subtasks": [
        {{
          "subtask": "进行设备监控需求调研",
          "phase": "Strategy & Planning",
          "required_skills": ["需求分析", "行业研究"],
          "assignment_reason": "张伟华作为CEO（Rank 1），具备商业模式画布(strong)、战略分析(strong)等技能，非常适合主导项目的需求调研工作。作为高层领导，他能够从战略高度理解业务需求，为后续设计提供准确的方向指引。"
        }},
        {{
          "subtask": "制定项目整体规划",
          "phase": "Strategy & Planning",
          "required_skills": ["项目管理", "战略规划"],
          "assignment_reason": "张伟华具备项目管理和战略规划能力，能够基于需求调研结果制定清晰的项目规划，包括里程碑、资源分配和风险管理。"
        }},
        ...
      ],
      "total_assigned": 6
    }},
    {{
      "user_name": "李明",
      "rank": 2,
      "assigned_subtasks": [
        {{
          "subtask": "设计系统总体架构",
          "phase": "Design & Architecture",
          "required_skills": ["系统架构", "技术选型"],
          "assignment_reason": "李明作为技术总监（Rank 2），拥有系统架构(strong)和云计算(strong)技能，是设计系统架构的最佳人选。他能够设计可扩展、高可用的技术架构。"
        }},
        ...
      ],
      "total_assigned": 7
    }},
    ...（所有{len(team_members)}个成员）
  ],
  "validation": {{
    "all_members_assigned": true,
    "min_tasks_per_member_met": true,
    "all_subtasks_assigned": true,
    "unassigned_subtasks": [],
    "members_below_minimum": []
  }}
}}
```

## 重要提醒

1. **必须**为所有 {len(team_members)} 个成员都分配任务
2. **必须**分配所有 {len(sequenced_subtasks)} 个任务（一个不能少）
3. 每个成员的 assigned_subtasks 数量 >= {config.MIN_SUBTASKS_PER_MEMBER}
4. assignment_reason 要详细（60-120字），必须包含：
   - 成员的职位和 Rank
   - 成员具备的相关技能及熟练度
   - 为什么这些技能适合这个任务
   - （可选）任务在项目中的重要性
5. 保留每个 subtask 的所有字段（subtask, phase, required_skills）
   - 注意：subtask_id 会由系统自动生成，不需要包含在输出中
6. validation 部分要如实反映分配情况
7. 只返回 JSON 数据，不要包含任何其他说明文字
8. **严格要求**：assignment_reason 必须是**单行文本**，不要使用换行符、制表符或其他控制字符

请开始为 {len(team_members)} 名成员分配 {len(sequenced_subtasks)} 个任务。记住：所有文本字段必须是单行，不要包含换行符或控制字符。
"""
    return prompt
