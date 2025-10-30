"""
QAR刷新模块 - 基于LLM自我评估的质量控制和改写
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from llm_interface import LLMInterface


class QARRefresher:
    """QAR刷新器 - 使用LLM自我评估和改写来确保质量"""
    
    def __init__(self, llm_interface: LLMInterface):
        """
        初始化QAR刷新器
        
        Args:
            llm_interface: LLM接口实例
        """
        self.llm = llm_interface
        self.max_refresh_attempts = 1  # 最多改写一次
    
    def evaluate_and_refresh(self, qa_entry: Dict[str, Any], qa_type: str, 
                            original_prompt: str, verbose: bool = False, 
                            reference: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        评估QAR质量并在需要时进行刷新
        
        Args:
            qa_entry: QAR条目
            qa_type: QAR类型
            original_prompt: 原始生成prompt
            verbose: 是否输出详细信息
            
        Returns:
            dict: 处理后的QAR条目，包含is_leaked和refresh_count字段
        """
        # 初始化字段
        qa_entry['is_leaked'] = False
        qa_entry['refresh_count'] = qa_entry.get('refresh_count', 0)
        qa_entry['evaluation_history'] = qa_entry.get('evaluation_history', [])
        
        # 如果没有传入reference，从qa_entry中获取
        if reference is None:
            reference = qa_entry.get('Reference', {})
        
        # 第一步：自我评估
        evaluation_result = self.self_evaluate(qa_entry, qa_type, original_prompt, reference, verbose)
        
        if evaluation_result is None:
            # 评估失败，保守标记为需要人工审核
            qa_entry['needs_manual_review'] = True
            return qa_entry
        
        # 记录评估历史
        qa_entry['evaluation_history'].append({
            'attempt': qa_entry['refresh_count'],
            'evaluation': evaluation_result
        })
        
        # 检查是否需要刷新
        needs_refresh = evaluation_result.get('needs_refresh', False)
        
        if not needs_refresh:
            # 质量合格，直接返回
            if verbose:
                print(f"✓ QAR质量评估通过，无需刷新")
            return qa_entry
        
        # 第二步：检查是否已达到最大刷新次数
        if qa_entry['refresh_count'] >= self.max_refresh_attempts:
            # 已达到最大刷新次数，标记为泄漏
            qa_entry['is_leaked'] = True
            if verbose:
                print(f"✗ QAR已达到最大刷新次数({self.max_refresh_attempts})，标记为泄漏")
            return qa_entry
        
        # 第三步：执行刷新
        if verbose:
            print(f"→ QAR需要刷新，正在执行改写...")
        
        refreshed_qa = self.refresh_qa(qa_entry, qa_type, evaluation_result, original_prompt, reference, verbose)
        
        if refreshed_qa is None:
            # 刷新失败，标记为泄漏
            qa_entry['is_leaked'] = True
            if verbose:
                print(f"✗ QAR刷新失败，标记为泄漏")
            return qa_entry
        
        # 更新刷新计数
        refreshed_qa['refresh_count'] = qa_entry['refresh_count'] + 1
        refreshed_qa['evaluation_history'] = qa_entry['evaluation_history']
        
        if verbose:
            print(f"✓ QAR刷新完成 (第{refreshed_qa['refresh_count']}次)")
        
        return refreshed_qa
    
    def self_evaluate(self, qa_entry: Dict[str, Any], qa_type: str, original_prompt: str,
                     reference: Dict[str, Any], verbose: bool = False) -> Optional[Dict[str, Any]]:
        """
        使用LLM对QAR进行自我评估
        
        Args:
            qa_entry: QAR条目
            original_prompt: 原始生成prompt
            verbose: 是否输出详细信息
            
        Returns:
            dict: 评估结果，如果评估失败返回None
        """
        try:
            # 提取关键约束
            key_constraints = self._extract_key_constraints(reference)
            
            # 准备评估数据
            evaluation_data = {
                'question': qa_entry.get('Question', ''),
                'correct_answer': qa_entry.get('Correct_Answer', ''),
                'incorrect_answers': qa_entry.get('Incorrect_Answers', []),
                'original_prompt': original_prompt,
                'qa_type': qa_type,
                'key_constraints': key_constraints
            }
            
            # 调用LLM进行评估
            response = self.llm.query_llm(evaluation_data, 'qa_self_evaluation', verbose=verbose)
            
            # 解析评估结果
            evaluation_result = self._parse_evaluation_result(response)
            
            if evaluation_result is None:
                if verbose:
                    print(f"Warning: Failed to parse evaluation result")
                return None
            
            if verbose:
                self._print_evaluation_summary(evaluation_result)
            
            return evaluation_result
            
        except Exception as e:
            print(f"Error during self-evaluation: {e}")
            return None
    
    def refresh_qa(self, qa_entry: Dict[str, Any], qa_type: str, evaluation_result: Dict[str, Any],
                   original_prompt: str, reference: Dict[str, Any], verbose: bool = False) -> Optional[Dict[str, Any]]:
        """
        基于评估结果刷新QAR
        
        Args:
            qa_entry: 原始QAR条目
            evaluation_result: 评估结果
            original_prompt: 原始生成prompt
            verbose: 是否输出详细信息
            
        Returns:
            dict: 刷新后的QAR条目，如果刷新失败返回None
        """
        try:
            # 提取Reference中的关键约束信息
            key_constraints = self._extract_key_constraints(reference)
            
            # 准备刷新数据
            refresh_data = {
                'question': qa_entry.get('Question', ''),
                'correct_answer': qa_entry.get('Correct_Answer', ''),
                'incorrect_answers': qa_entry.get('Incorrect_Answers', []),
                'original_prompt': original_prompt,
                'evaluation_result': evaluation_result,
                'refresh_instruction': evaluation_result.get('refresh_instruction', ''),
                'reference': reference,
                'key_constraints': key_constraints,
                'qa_type': qa_type
            }
            
            # 调用LLM进行刷新
            response = self.llm.query_llm(refresh_data, 'qa_refresh', verbose=verbose)
            
            # 解析刷新结果
            refreshed_qa = self._parse_refresh_result(response, qa_entry)
            
            if refreshed_qa is None:
                if verbose:
                    print(f"Warning: Failed to parse refresh result")
                return None
            
            if verbose:
                print(f"✓ QAR刷新成功")
                if 'refresh_notes' in refreshed_qa:
                    print(f"  改写说明: {refreshed_qa['refresh_notes']}")
            
            return refreshed_qa
            
        except Exception as e:
            print(f"Error during QAR refresh: {e}")
            return None
    
    def _parse_evaluation_result(self, response: str) -> Optional[Dict[str, Any]]:
        """
        解析评估结果
        
        Args:
            response: LLM响应
            
        Returns:
            dict: 解析后的评估结果
        """
        try:
            # 清理响应文本
            response = response.strip()
            
            # 尝试提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                evaluation_result = json.loads(json_str)
                
                # 验证必需字段
                if 'needs_refresh' in evaluation_result:
                    return evaluation_result
            
            # 如果JSON解析失败，尝试按字段提取
            return self._extract_evaluation_fields(response)
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return self._extract_evaluation_fields(response)
        except Exception as e:
            print(f"Error parsing evaluation result: {e}")
            return None
    
    def _extract_evaluation_fields(self, response: str) -> Optional[Dict[str, Any]]:
        """
        从文本中提取评估字段（备用方法）
        
        Args:
            response: LLM响应
            
        Returns:
            dict: 提取的评估结果
        """
        try:
            # 提取overall_quality
            quality_match = re.search(r'overall_quality["\s:]+([a-z_]+)', response, re.IGNORECASE)
            overall_quality = quality_match.group(1) if quality_match else 'needs_improvement'
            
            # 提取needs_refresh
            refresh_match = re.search(r'needs_refresh["\s:]+(\w+)', response, re.IGNORECASE)
            needs_refresh_str = refresh_match.group(1) if refresh_match else 'true'
            needs_refresh = needs_refresh_str.lower() in ['true', 'yes', '1']
            
            # 提取refresh_instruction
            instruction_match = re.search(r'refresh_instruction["\s:]+["\'](.+?)["\']', response, re.DOTALL)
            refresh_instruction = instruction_match.group(1) if instruction_match else ''
            
            return {
                'overall_quality': overall_quality,
                'needs_refresh': needs_refresh,
                'refresh_instruction': refresh_instruction,
                'evaluation_details': {}
            }
            
        except Exception as e:
            print(f"Error extracting evaluation fields: {e}")
            return None
    
    def _parse_refresh_result(self, response: str, original_qa: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        解析刷新结果
        
        Args:
            response: LLM响应
            original_qa: 原始QAR条目
            
        Returns:
            dict: 解析后的刷新结果
        """
        try:
            # 清理响应文本
            response = response.strip()
            
            # 尝试提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                refreshed_qa = json.loads(json_str)
                
                # 验证必需字段
                if self._validate_refreshed_qa(refreshed_qa):
                    # 保留原始字段
                    refreshed_qa['Type'] = original_qa.get('Type', '')
                    refreshed_qa['Topic'] = original_qa.get('Topic', '')
                    refreshed_qa['Reference'] = original_qa.get('Reference', {})
                    return refreshed_qa
            
            # 如果JSON解析失败，尝试按字段提取
            return self._extract_refresh_fields(response, original_qa)
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return self._extract_refresh_fields(response, original_qa)
        except Exception as e:
            print(f"Error parsing refresh result: {e}")
            return None
    
    def _validate_refreshed_qa(self, qa_dict: Dict[str, Any]) -> bool:
        """
        验证刷新后的QAR是否有效
        
        Args:
            qa_dict: QAR字典
            
        Returns:
            bool: 是否有效
        """
        required_fields = ['Question', 'Correct_Answer', 'Incorrect_Answers']
        for field in required_fields:
            if field not in qa_dict or not qa_dict[field]:
                return False
        
        # 检查错误选项数量
        incorrect_answers = qa_dict.get('Incorrect_Answers', [])
        if len(incorrect_answers) < 3:
            return False
        
        return True
    
    def _extract_refresh_fields(self, response: str, original_qa: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从文本中提取刷新字段（备用方法）
        
        Args:
            response: LLM响应
            original_qa: 原始QAR条目
            
        Returns:
            dict: 提取的刷新结果
        """
        try:
            # 提取问题
            question_patterns = [
                r'Question["\s:]+["\'](.+?)["\']',
                r'问题["\s:]+["\'](.+?)["\']',
            ]
            
            question = None
            for pattern in question_patterns:
                matches = re.findall(pattern, response, re.DOTALL)
                if matches:
                    question = matches[0].strip()
                    break
            
            # 提取正确答案
            correct_patterns = [
                r'Correct_Answer["\s:]+["\'](.+?)["\']',
                r'正确答案["\s:]+["\'](.+?)["\']',
            ]
            
            correct_answer = None
            for pattern in correct_patterns:
                matches = re.findall(pattern, response, re.DOTALL)
                if matches:
                    correct_answer = matches[0].strip()
                    break
            
            # 提取错误选项
            incorrect_answers = []
            incorrect_section = re.search(r'Incorrect_Answers["\s:]+\[(.*?)\]', response, re.DOTALL)
            if incorrect_section:
                options_text = incorrect_section.group(1)
                # 提取所有引号内的内容
                options = re.findall(r'["\'](.+?)["\']', options_text, re.DOTALL)
                incorrect_answers = [opt.strip() for opt in options if opt.strip()]
            
            # 验证提取结果
            if question and correct_answer and len(incorrect_answers) >= 3:
                return {
                    'Question': question,
                    'Correct_Answer': correct_answer,
                    'Incorrect_Answers': incorrect_answers[:3],
                    'Type': original_qa.get('Type', ''),
                    'Topic': original_qa.get('Topic', ''),
                    'Reference': original_qa.get('Reference', {})
                }
            
            return None
            
        except Exception as e:
            print(f"Error extracting refresh fields: {e}")
            return None
    
    def _print_evaluation_summary(self, evaluation_result: Dict[str, Any]):
        """
        打印评估摘要
        
        Args:
            evaluation_result: 评估结果
        """
        print("\n" + "="*60)
        print("QAR质量评估结果")
        print("="*60)
        
        overall_quality = evaluation_result.get('overall_quality', 'unknown')
        needs_refresh = evaluation_result.get('needs_refresh', False)
        
        print(f"总体质量: {overall_quality}")
        print(f"需要刷新: {'是' if needs_refresh else '否'}")
        
        evaluation_details = evaluation_result.get('evaluation_details', {})
        if evaluation_details:
            print("\n详细评估:")
            for dimension, details in evaluation_details.items():
                if isinstance(details, dict):
                    score = details.get('score', 'unknown')
                    issue = details.get('issue', '')
                    print(f"  - {dimension}: {score}")
                    if issue:
                        print(f"    问题: {issue}")
        
        refresh_instruction = evaluation_result.get('refresh_instruction', '')
        if refresh_instruction:
            print(f"\n改写指导: {refresh_instruction}")
        
        print("="*60 + "\n")
    
    def batch_evaluate_and_refresh(self, qa_entries: list, qa_type: str,
                                   original_prompt: str, verbose: bool = False) -> Tuple[list, Dict[str, Any]]:
        """
        批量评估和刷新QAR
        
        Args:
            qa_entries: QAR条目列表
            qa_type: QAR类型
            original_prompt: 原始生成prompt
            verbose: 是否输出详细信息
            
        Returns:
            tuple: (处理后的QAR列表, 统计信息)
        """
        processed_entries = []
        stats = {
            'total': len(qa_entries),
            'passed_first_time': 0,
            'refreshed_and_passed': 0,
            'leaked': 0,
            'needs_manual_review': 0
        }
        
        for i, qa_entry in enumerate(qa_entries):
            if verbose:
                print(f"\n处理QAR {i+1}/{len(qa_entries)}...")
            
            processed_qa = self.evaluate_and_refresh(qa_entry, qa_type, original_prompt, verbose)
            processed_entries.append(processed_qa)
            
            # 更新统计
            if processed_qa.get('is_leaked', False):
                stats['leaked'] += 1
            elif processed_qa.get('needs_manual_review', False):
                stats['needs_manual_review'] += 1
            elif processed_qa.get('refresh_count', 0) == 0:
                stats['passed_first_time'] += 1
            else:
                stats['refreshed_and_passed'] += 1
        
        if verbose:
            self._print_batch_summary(stats)
        
        return processed_entries, stats
    
    def _extract_key_constraints(self, reference: Dict[str, Any]) -> str:
        """
        从Reference中提取关键约束信息
        
        Args:
            reference: Reference数据（支持两种格式：原始格式和DataLoader处理后的格式）
            
        Returns:
            str: 关键约束信息的文本描述
        """
        constraints = []
        
        # 兼容两种数据格式：
        # 1. 原始格式：{type, timestamp, content: {reasoning, ...}}
        # 2. DataLoader格式：{reasoning, supporting_evidence, ..., original_data}
        
        # 尝试从两种格式中提取数据
        if 'content' in reference:
            # 原始格式
            content = reference['content']
        else:
            # DataLoader格式（直接使用reference本身）
            content = reference
        
        # 1. 提取reasoning中的关键约束（优先级最高）
        reasoning = content.get('reasoning', '')
        if reasoning:
            # 提取包含约束信息的部分
            constraint_keywords = ['关键约束', '约束', '必须', '不能', '只能', '要求', '规定', '不应', '应该', '避免', '禁止']
            if any(keyword in reasoning for keyword in constraint_keywords):
                constraints.append(f"**推理说明（包含核心约束）：**\n{reasoning}")
                
                # 特别提取硬约束（如"只能喝粥"、"不能吃辣"）
                hard_constraints = []
                if '只能' in reasoning:
                    import re
                    matches = re.findall(r'只能[^，。；！]*', reasoning)
                    hard_constraints.extend(matches)
                if '不能' in reasoning:
                    import re
                    matches = re.findall(r'不能[^，。；！]*', reasoning)
                    hard_constraints.extend(matches)
                if '必须' in reasoning:
                    import re
                    matches = re.findall(r'必须[^，。；！]*', reasoning)
                    hard_constraints.extend(matches)
                
                if hard_constraints:
                    constraints.append(f"**⚠️ 硬性约束（必须严格遵守）：**\n" + "\n".join([f"- {c}" for c in hard_constraints]))
        
        # 2. 特别提取AI知识库规则（用于active_reminder_qa）
        if 'AI知识库' in reasoning or 'R_Policy' in reasoning:
            import re
            # 提取SOP规则
            sop_pattern = r'(SOP\s*[\d\.]+[^：。]*[：:][^。]+)'
            sop_matches = re.findall(sop_pattern, reasoning)
            if sop_matches:
                constraints.append(f"**AI知识库已知规则：**\n" + "\n".join([f"- {s}" for s in sop_matches]))
        
        # 3. 提取supporting_evidence中的关键对话
        supporting_evidence = content.get('supporting_evidence', [])
        if supporting_evidence:
            key_dialogues = []
            for evidence in supporting_evidence:
                if 'content' in evidence and 'dialogue' in evidence['content']:
                    dialogue = evidence['content']['dialogue']
                    character = evidence.get('character_name', '未知')
                    # 提取包含约束、要求、规定等关键词的对话
                    dialogue_keywords = [
                        '医生说', '必须', '不能', '只能', '要求', '规定', 
                        'SOP', '制度', '应该', '不应', '避免', '禁止',
                        '一周', '流食', '软食', '硬的', '辣的', '粥',
                        '提前', '批准', '审批', '流程'
                    ]
                    if any(keyword in dialogue for keyword in dialogue_keywords):
                        key_dialogues.append(f"- {character}: {dialogue}")
            
            if key_dialogues:
                constraints.append("**关键对话（包含约束信息）：**\n" + "\n".join(key_dialogues))
        
        # 4. 提取ground_truth_answer作为参考
        ground_truth = content.get('ground_truth_answer', '')
        if ground_truth:
            constraints.append(f"**参考答案：**\n{ground_truth}")
        
        # 如果没有提取到任何约束，返回全部reasoning作为兜底
        if not constraints and reasoning:
            constraints.append(f"**完整推理过程：**\n{reasoning}")
        
        return "\n\n".join(constraints) if constraints else "无明确约束"
    
    def _print_batch_summary(self, stats: Dict[str, Any]):
        """
        打印批量处理摘要
        
        Args:
            stats: 统计信息
        """
        print("\n" + "="*60)
        print("批量处理摘要")
        print("="*60)
        print(f"总计: {stats['total']}")
        print(f"首次通过: {stats['passed_first_time']} ({stats['passed_first_time']/stats['total']*100:.1f}%)")
        print(f"刷新后通过: {stats['refreshed_and_passed']} ({stats['refreshed_and_passed']/stats['total']*100:.1f}%)")
        print(f"标记为泄漏: {stats['leaked']} ({stats['leaked']/stats['total']*100:.1f}%)")
        print(f"需要人工审核: {stats['needs_manual_review']} ({stats['needs_manual_review']/stats['total']*100:.1f}%)")
        print("="*60 + "\n")

