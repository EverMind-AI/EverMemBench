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
    def get_project_generation_prompt(team_members: List[Dict], project_number: int, previous_projects: Optional[List[Dict]] = None) -> str:
        """获取项目生成提示词（生成project topic和description）"""
        return get_project_generation_prompt_phase4(team_members, project_number, previous_projects)

    @staticmethod
    def get_member_adjustment_prompt(new_project_topic: str, new_project_description: str, current_team: List[Dict], all_employees: List[Dict], previous_projects: List[Dict]) -> str:
        """获取成员调整提示词（调整team members）"""
        return get_member_adjustment_prompt_phase4(new_project_topic, new_project_description, current_team, all_employees, previous_projects)

    @staticmethod
    def get_communication_style_adjustment_prompt(project_topic: str, project_description: str, team_members: List[Dict]) -> str:
        """获取沟通风格调整提示词（根据项目架构调整communication style）"""
        return get_communication_style_adjustment_prompt_phase4(project_topic, project_description, team_members)

    @staticmethod
    def get_task_breakdown_and_assignment_prompt(project_topic: str, project_description: str, team_members: List[Dict]) -> str:
        """获取任务拆解和分配提示词（拆解project为subtasks）"""
        return get_task_breakdown_and_assignment_prompt_phase4(project_topic, project_description, team_members)


# ==================== Phase 4: Task Generation Prompt Functions ====================

def get_project_generation_prompt_phase4(team_members: List[Dict], project_number: int, previous_projects: Optional[List[Dict]] = None) -> str:
    """
    Prompt 1: 生成项目主题和描述
    
    用于：
    - Project 1: 基于初始团队生成第一个项目
    - Project 2+: 生成与之前项目相关的新项目
    """
    
    # 格式化团队成员信息
    team_info = []
    for i, member in enumerate(team_members, 1):
        # 格式化hard_skills
        skills_str = ", ".join([f"{s['skill']}({s['proficiency']})" for s in member['hard_skills']])
        
        # 简要概括communication_style
        cs = member['communication_style']
        cs_summary = f"{cs.get('Formality', 'N/A')}, {cs.get('Directness', 'N/A')}, {cs.get('Warmth', 'N/A')}"
        
        team_info.append(f"""{i}. {member['user_name']} - {member['title']} - {member['team']}
   - Rank: {member['rank']}
   - 硬技能: {skills_str}
   - 沟通风格: {cs_summary}""")
    
    team_info_text = "\n\n".join(team_info)
    
    # Rank分布
    rank_counts = {}
    for member in team_members:
        rank = member['rank']
        rank_counts[rank] = rank_counts.get(rank, 0) + 1
    
    # 之前项目信息
    if previous_projects and len(previous_projects) > 0:
        prev_projects_text = "\n\n之前已经生成了以下项目，新项目需要与这些项目相关但不重复：\n\n"
        for i, proj in enumerate(previous_projects, 1):
            proj_info = proj.get('project_info', {})
            prev_projects_text += f"""项目{i}: {proj_info.get('project_topic', 'N/A')}
描述: {proj_info.get('project_description', 'N/A')}\n\n"""
    else:
        prev_projects_text = "\n\n这是第一个项目，可以自由选择方向。\n"
    
    prompt = f"""# 任务：生成项目主题和描述

## 项目编号
第{project_number}个项目

## 团队成员信息
你将为以下团队生成一个合适的项目：

{team_info_text}

## 团队构成分析
- Rank 1 (CEO/高管): {rank_counts.get(1, 0)}人
- Rank 2 (总监): {rank_counts.get(2, 0)}人
- Rank 3 (员工): {rank_counts.get(3, 0)}人
- 总人数: {len(team_members)}人

## 已有项目信息
{prev_projects_text}

## 要求

1. **项目相关性**（如果有之前项目）：
   - 新项目必须与之前的项目有业务或技术上的关联
   - 但不能是重复项目
   - 不能是父子任务关系（例如：已有"开发CRM系统"，不能生成"开发CRM系统的登录模块"）
   - 应该是相关但独立的项目（例如：已有"CRM系统"，可以生成"数据分析平台"、"移动端App"等）

2. **项目类型多样化** ⚠️ 重要：
   - 避免所有项目都是"智能xxx"类型
   - 项目类型应该多样化，可以包括但不限于：
     * 传统业务系统（如：ERP系统、CRM系统、OA系统）
     * 移动应用（如：电商App、社交App）
     * 数据平台（如：数据中台、BI平台）
     * 企业服务（如：协作平台、项目管理系统）
     * 营销工具（如：营销自动化平台、内容管理系统）
     * 基础设施（如：监控平台、日志系统）
   - 即使团队有AI/ML技能，也不必每个项目都用上这些技能
   - 项目名称要具体、实用，避免过度使用"智能"等流行词汇

3. **技能匹配**：
   - 项目必须充分利用团队成员的硬技能
   - 考虑团队的技术栈和专业领域
   - 确保每个成员都有可以贡献的地方
   - 但不必强制使用所有技能类型

4. **规模适配**：
   - 项目规模应该适合{len(team_members)}人团队
   - 考虑Rank分布，高管少意味着战略性项目，基层员工多意味着执行性项目

5. **沟通风格考虑**：
   - 考虑团队的整体沟通风格
   - 如果团队更formal，适合严谨的项目
   - 如果团队更casual，适合创新探索型项目

## 输出格式

请严格按照以下JSON格式输出（不要添加任何其他文字）：

```json
{{
  "project_topic": "项目主题（简短，10字以内）",
  "project_description": "项目描述（详细说明项目目标、主要功能模块、技术栈、预期成果等，100-200字）",
  "reasoning": "为什么选择这个项目（说明与团队技能和之前项目的关联性，50-100字）"
}}
```

## 重要提示

- project_topic应该简洁明确，便于创建文件夹
- project_description应该详细到足以指导后续的任务拆解
- 确保项目是high-level的，不要涉及具体的实现细节
- ⚠️ **避免项目名称都是"智能xxx"**，要有创意和多样性
- 项目类型示例：
  * ✅ 好的项目名称：企业协作平台、电商管理系统、移动端社交App、供应链管理平台、营销自动化工具
  * ❌ 避免过度使用：智能客服系统、智能推荐平台、智能数据分析、智能xxx...
- 只返回JSON数据，不要包含任何其他说明文字

现在请为这个团队生成项目主题和描述。"""
    
    return prompt


def get_member_adjustment_prompt_phase4(new_project_topic: str, new_project_description: str, current_team: List[Dict], all_employees: List[Dict], previous_projects: List[Dict]) -> str:
    """
    Prompt 2: 生成新项目主题并调整团队成员

    注意：这个prompt实际上包含两部分功能：
    1. 生成新项目的topic和description
    2. 基于新项目需求调整团队成员

    但根据实施计划，这两部分应该合并成一个GPT调用
    """
    import config

    # 格式化当前团队成员
    current_team_info = []
    for i, member in enumerate(current_team, 1):
        skills_str = ", ".join([f"{s['skill']}({s['proficiency']})" for s in member['hard_skills']])
        cs = member['communication_style']
        cs_summary = f"{cs.get('Formality', 'N/A')}, {cs.get('Directness', 'N/A')}"
        
        current_team_info.append(f"""{i}. {member['user_name']} - {member['title']} - {member['team']} (Rank {member['rank']})
   - 硬技能: {skills_str}
   - 沟通风格: {cs_summary}""")
    
    current_team_text = "\n\n".join(current_team_info)
    
    # 格式化所有员工（按Rank分组）
    all_emp_by_rank = {1: [], 2: [], 3: []}
    for emp in all_employees:
        rank = emp['rank']
        skills_str = ", ".join([s['skill'] for s in emp['hard_skills']])  # 显示所有技能
        all_emp_by_rank[rank].append(f"{emp['user_name']} ({emp['title']}, {emp['team']}) - {skills_str}")
    
    all_emp_text = f"""**Rank 1 (CEO/高管)**: {len(all_emp_by_rank[1])}人
{chr(10).join(all_emp_by_rank[1])}

**Rank 2 (总监)**: {len(all_emp_by_rank[2])}人
{chr(10).join(all_emp_by_rank[2])}

**Rank 3 (员工)**: {len(all_emp_by_rank[3])}人
{chr(10).join(all_emp_by_rank[3])}"""
    
    # 格式化之前的项目
    prev_projects_text = ""
    for i, proj in enumerate(previous_projects, 1):
        proj_info = proj.get('project_info', {})
        members = proj.get('members', [])
        member_names = [m['user_name'] for m in members]
        
        prev_projects_text += f"""项目{i}: {proj_info.get('project_topic', 'N/A')}
描述: {proj_info.get('project_description', 'N/A')}
团队成员({len(members)}人): {', '.join(member_names)}

"""
    
    # 找出当前团队中的Rank 1成员
    rank1_members = [m['user_name'] for m in current_team if m['rank'] == 1]
    
    prompt = f"""# 任务：为新项目调整团队成员

你刚刚生成了一个新项目：

**项目主题**: {new_project_topic}
**项目描述**: {new_project_description}

现在需要根据这个新项目的需求，决定团队成员的调整。

⚠️ **【重要约束】最终团队总人数必须在{config.SUBSEQUENT_TEAM_SIZE_RANGE['min']}-{config.SUBSEQUENT_TEAM_SIZE_RANGE['max']}人之间！这是硬性要求，必须严格遵守！**

## 当前团队成员
以下是上一个项目的团队成员：

{current_team_text}

## 所有可用员工
公司共有{len(all_employees)}名员工可供选择：

{all_emp_text}

## 之前的项目历史
{prev_projects_text}

## 调整规则

**必须遵守的约束**：
1. ⚠️ **Rank 1的员工绝对不能移除**: {', '.join(rank1_members)}
2. ⚠️ **Rank 2的员工至少保留1个**
3. ⚠️ **团队总人数必须严格在{config.SUBSEQUENT_TEAM_SIZE_RANGE['min']}-{config.SUBSEQUENT_TEAM_SIZE_RANGE['max']}人之间（包含边界值）**
   - 最少{config.SUBSEQUENT_TEAM_SIZE_RANGE['min']}人，最多{config.SUBSEQUENT_TEAM_SIZE_RANGE['max']}人
   - 这是硬性要求，不是建议！
   - 计算方法：len(keep_members) + len(add_members) 必须在此范围内
   - 如果当前团队人数已经符合要求，可以微调但不要超出范围

**调整原则**：
1. **先满足人数约束，再考虑技能匹配**：确保最终团队人数在{config.SUBSEQUENT_TEAM_SIZE_RANGE['min']}-{config.SUBSEQUENT_TEAM_SIZE_RANGE['max']}人范围内
2. **技能匹配**：在满足人数约束的前提下，选择技能最匹配的成员
3. **避免重复使用**：优先选择在之前项目中较少使用的员工（从all_employees中选择）
4. **团队平衡**：考虑不同部门、不同技能的平衡
5. **沟通兼容**：考虑成员间的沟通风格是否兼容

## 输出格式

请严格按照以下JSON格式输出（不要添加任何其他文字）：

**注意：示例中的total_members必须在{config.SUBSEQUENT_TEAM_SIZE_RANGE['min']}-{config.SUBSEQUENT_TEAM_SIZE_RANGE['max']}范围内！**

```json
{{
  "member_adjustments": {{
    "keep_members": [
      "顾行远",
      "张昱宸",
      "黄致远",
      "李明",
      "王芳",
      ... （根据实际情况列出所有保留的成员，确保总人数符合要求）
    ],
    "remove_members": [
      {{
        "user_name": "赵翎珊",
        "reason": "财务技能在此项目中不是核心需求"
      }},
      {{
        "user_name": "孙强",
        "reason": "市场技能与新项目关联度低"
      }}
    ],
    "add_members": [
      {{
        "user_name": "孟昭林",
        "from_team": "技术研发部",
        "from_title": "数据科学家",
        "rank": 3,
        "reason": "项目需要数据科学专业技能"
      }},
      {{
        "user_name": "陈静",
        "from_team": "技术研发部",
        "from_title": "后端工程师",
        "rank": 3,
        "reason": "需要更多后端开发资源"
      }},
      ... （添加足够的成员，确保 len(keep_members) + len(add_members) 在{config.SUBSEQUENT_TEAM_SIZE_RANGE['min']}-{config.SUBSEQUENT_TEAM_SIZE_RANGE['max']}范围内）
    ]
  }},
  "final_team_composition": {{
    "total_members": 18,  // 必须在{config.SUBSEQUENT_TEAM_SIZE_RANGE['min']}-{config.SUBSEQUENT_TEAM_SIZE_RANGE['max']}范围内，且等于keep_members + add_members的总数
    "rank_1": 1,
    "rank_2": 1,
    "rank_3": 16
  }},
  "team_analysis": "简要说明为什么这样调整团队，新团队的优势是什么（50-100字）"
}}
```

## 重要提示

- ⚠️ **CRITICAL**: 最终团队总人数（keep_members + add_members的总数）必须在{config.SUBSEQUENT_TEAM_SIZE_RANGE['min']}-{config.SUBSEQUENT_TEAM_SIZE_RANGE['max']}人之间
- ⚠️ **CRITICAL**: final_team_composition.total_members 必须等于 len(keep_members) + len(add_members)，且必须在{config.SUBSEQUENT_TEAM_SIZE_RANGE['min']}-{config.SUBSEQUENT_TEAM_SIZE_RANGE['max']}范围内
- ⚠️ 必须严格遵守Rank约束（Rank 1不能移除，Rank 2至少1个）
- remove_members和add_members中的user_name必须是实际存在的员工姓名
- keep_members列表应包含所有保留的员工姓名（包括Rank 1）
- 在调整成员时，先计算最终人数是否符合要求，再考虑技能匹配
- 只返回JSON数据，不要包含任何其他说明文字

现在请为这个新项目调整团队成员。"""
    
    return prompt


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
   - 小团队({config.SUBSEQUENT_TEAM_SIZE_RANGE['min']}-{config.SUBSEQUENT_TEAM_SIZE_RANGE['min'] + (config.SUBSEQUENT_TEAM_SIZE_RANGE['max'] - config.SUBSEQUENT_TEAM_SIZE_RANGE['min']) // 3}人)：更casual，更direct
   - 中团队({config.SUBSEQUENT_TEAM_SIZE_RANGE['min'] + (config.SUBSEQUENT_TEAM_SIZE_RANGE['max'] - config.SUBSEQUENT_TEAM_SIZE_RANGE['min']) // 3 + 1}-{config.SUBSEQUENT_TEAM_SIZE_RANGE['min'] + 2 * (config.SUBSEQUENT_TEAM_SIZE_RANGE['max'] - config.SUBSEQUENT_TEAM_SIZE_RANGE['min']) // 3}人)：balanced
   - 大团队({config.SUBSEQUENT_TEAM_SIZE_RANGE['min'] + 2 * (config.SUBSEQUENT_TEAM_SIZE_RANGE['max'] - config.SUBSEQUENT_TEAM_SIZE_RANGE['min']) // 3 + 1}+人)：更formal，更structured

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

- 不要大幅度改变所有维度，只调整受架构影响明显的维度
- 主要调整的维度：Formality, Directness, Warmth
- 次要调整的维度：Verbosity, Questioning_Style
- 较少调整的维度：Humor, Emoji_Usage, Jargon_Usage
- user_name必须是实际存在的员工姓名
- 所有维度的值必须严格使用上述定义的标签（区分大小写）
- 如果某个维度不需要调整，在adjustments_made中不要包含它
- 只返回JSON数据，不要包含任何其他说明文字

现在请根据项目架构调整团队成员的沟通风格。"""
    
    return prompt


def get_task_breakdown_and_assignment_prompt_phase4(project_topic: str, project_description: str, team_members: List[Dict]) -> str:
    """
    Prompt 4: 拆解项目任务并分配给团队成员
    """
    
    # 格式化团队成员信息
    members_info = []
    for i, member in enumerate(team_members, 1):
        # 格式化hard_skills
        skills_str = ", ".join([f"{s['skill']}({s['proficiency']})" for s in member['hard_skills']])
        
        # 格式化communication_style
        cs = member['communication_style']
        cs_details = "\n     ".join([f"* {k}: {v}" for k, v in cs.items()])
        
        members_info.append(f"""{i}. {member['user_name']} - {member['title']} - {member['team']} (Rank {member['rank']})
   - 硬技能: {skills_str}
   - 沟通风格:
     {cs_details}""")
    
    members_text = "\n\n".join(members_info)
    
    # 统计Rank分布
    rank_counts = {}
    for member in team_members:
        rank = member['rank']
        rank_counts[rank] = rank_counts.get(rank, 0) + 1
    
    prompt = f"""# 任务：拆解项目任务并分配给团队成员

## 项目信息
- 项目主题: {project_topic}
- 项目描述: {project_description}

## 团队成员信息

{members_text}

## 任务拆解和分配要求

**任务拆解原则**：
1. **细致程度**：任务应该足够细致，每个subtask都是可执行的具体工作
2. **技能匹配**：每个subtask应该匹配执行者的硬技能
3. **沟通考虑**：任务描述中应该说明需要的沟通方式
4. **负载平衡**：每个成员至少5个subtask，但要考虑任务复杂度

**⚠️ CRITICAL - 任务互斥性约束**：
- 同一个项目内的所有subtasks之间必须是**互斥的**、**不冲突的**、**非父子关系的**
- ❌ 错误示例1（父子关系）：不能同时有"开发用户管理模块"和"开发用户管理模块的登录功能"
- ❌ 错误示例2（重复）：不能同时有"设计数据库schema"和"设计数据库表结构"
- ❌ 错误示例3（冲突）：不能同时有"选择MySQL数据库"和"选择PostgreSQL数据库"
- ✅ 正确示例：每个subtask应该是独立的、并行的工作单元，如"开发用户认证模块"、"开发数据分析模块"、"开发API接口层"

**分配原则**：
1. **Rank 1（CEO/高管）**：
   - 战略规划、决策制定、跨部门协调
   - 数量：5-7个高复杂度任务

2. **Rank 2（总监）**：
   - 模块负责、团队协调、技术架构
   - 数量：5-8个任务

3. **Rank 3（员工）**：
   - 具体实现、开发、测试、文档
   - 数量：5-10个任务

**沟通需求标注**：
- 每个任务应该说明需要与谁沟通
- 说明沟通方式（formal meeting, casual discussion, written report等）
- 考虑成员的沟通风格

## 输出格式

请严格按照以下JSON格式输出（不要添加任何其他文字）：

```json
{{
  "project_topic": "{project_topic}",
  "total_subtasks": 60,
  "task_assignments": [
    {{
      "user_name": "顾行远",
      "rank": 1,
      "total_assigned": 6,
      "subtasks": [
        {{
          "subtask_id": 1,
          "subtask": "分析市场需求和竞争态势，制定项目的整体战略方向和核心目标，明确关键成功因素和里程碑，输出战略规划文档和项目目标OKR",
          "required_skills": ["商业模式画布", "SWOT分析", "OKR"],
          "communication_requirements": "需要与所有Rank 2总监进行formal meeting和书面战略文档沟通，每周进行战略review"
        }},
        {{
          "subtask_id": 2,
          "subtask": "审批项目预算和资源配置方案，确保各部门资源合理分配，监督预算执行情况，输出资源配置报告",
          "required_skills": ["KPI", "BSC平衡计分卡"],
          "communication_requirements": "与财务总监和各部门总监进行formal budget review meeting"
        }},
        {{
          "subtask_id": 3,
          "subtask": "..."
        }}
      ]
    }},
    {{
      "user_name": "张昱宸",
      "rank": 2,
      "total_assigned": 7,
      "subtasks": [
        {{
          "subtask_id": 7,
          "subtask": "设计系统整体技术架构，选择合适的技术栈和框架，制定技术规范和开发标准，输出技术架构文档",
          "required_skills": ["Java", "Kubernetes", "Spring Boot"],
          "communication_requirements": "与CEO进行formal架构review，与开发团队进行technical discussion"
        }},
        ...
      ]
    }}
  ]
}}
```

## 重要提示

- **⚠️ CRITICAL**: 必须为所有{len(team_members)}名成员分配任务，一个都不能漏
- user_name必须是上面列出的实际员工姓名
- subtask_id在整个项目中应该是唯一的（建议用1, 2, 3...连续编号）
- 每个成员至少5个subtasks
- required_skills应该是该成员实际拥有的硬技能名称（不包括proficiency）
- **⚠️ CRITICAL**: 所有subtasks之间必须互斥、不冲突、无父子关系
- "subtask"字段应该详细清晰地描述要做什么、如何做、输出什么，一个字段包含所有信息
- "communication_requirements"字段应该具体说明需要与谁沟通、沟通方式、频率等
- 任务分配要合理，不要让某个人的任务明显多于或少于其他人
- total_subtasks应该等于所有成员的subtasks数量之和
- total_assigned应该等于该成员的subtasks数量
- 只返回JSON数据，不要包含任何其他说明文字

现在请为这个项目拆解任务并分配给团队成员。"""

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
            all_tasks.append({
                'subtask_id': subtask['subtask_id'],
                'user_name': user_name,
                'rank': rank,
                'subtask': subtask['subtask'],
                'required_skills': subtask['required_skills']
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

## 1. 排序原则
- **依赖关系优先**:
  - 战略规划 → 需求分析 → 设计 → 开发 → 测试 → 部署
  - CEO/高层任务通常在前期（战略、预算、资源分配）
  - Rank 1（高层）任务在最前，Rank 2（总监）次之，Rank 3（员工）根据任务类型分布

- **任务类型顺序**:
  1. 战略规划与目标制定
  2. 预算与资源配置
  3. 需求分析与调研
  4. 系统设计（架构设计、UX设计、原型设计）
  5. 开发实施（前端、后端、算法、数据）
  6. 测试与优化
  7. 部署与上线
  8. 运营维护与迭代

- **合理性原则**:
  - 任务deadline应合理分布在365天内
  - 避免所有任务集中在某个时间段
  - 考虑任务复杂度：复杂任务给予更长的准备时间
  - 考虑团队负载：同一个人的多个任务不应deadline过于集中

## 2. 时间分配建议
- **项目前期（1-3月）**: 战略规划、需求分析、预算审批、架构设计
- **项目中期（4-8月）**: 系统开发、迭代测试、功能实现
- **项目后期（9-12月）**: 集成测试、性能优化、上线部署、文档完善

## 3. ⚠️ 硬性约束
- **所有deadline必须在 {start_date} 到 {end_date} 之间（包含边界）**
- **每个subtask必须分配一个deadline，不能遗漏**
- **deadline格式必须为 YYYY-MM-DD**
- **后续依赖任务的deadline不能早于前置任务**

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
1. `task_timeline` 数组必须包含所有{total_tasks}个subtask，一个都不能少
2. 每个任务必须有 `subtask_id`, `user_name`, `deadline`, `phase`, `reasoning` 五个字段
3. `deadline` 必须是 YYYY-MM-DD 格式的字符串
4. `phase` 必须是 "前期"、"中期" 或 "后期" 之一
5. `reasoning` 简要说明（10-30字）为什么这个任务安排在这个时间点

请开始分配任务时间线。
"""
    return prompt
