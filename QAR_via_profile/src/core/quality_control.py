"""
质量控制模块 - 重构为四个清晰的子模块
"""

import random
import re
from typing import List, Dict, Any, Tuple
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from llm_interface import LLMInterface


class LeakageDetector:
    """泄漏检测模块 - 专门处理问题答案泄漏检测，基于LLM语义理解"""
    
    def __init__(self, llm_interface: LLMInterface):
        """
        初始化泄漏检测器
        
        Args:
            llm_interface: LLM接口实例
        """
        self.llm = llm_interface
        self.checked_questions = {}
        self.n_calls = 6  # 统计检测的调用次数
        self.threshold = 4  # 判定阈值（6中4）
    
    def filter_leaked_questions(self, qa_entries: List[Dict[str, Any]], 
                              max_attempts: int = 3) -> List[Dict[str, Any]]:
        """
        过滤掉可能泄露答案的问题
        
        Args:
            qa_entries: QAR条目列表
            max_attempts: 最大尝试次数
            
        Returns:
            list: 过滤后的QAR条目列表
        """
        filtered_entries = []
        
        for qa_entry in qa_entries:
            question = qa_entry.get('Question', '')
            qa_type = qa_entry.get('Type', '')
            
            # 跳过某些类型的检查
            if qa_type == "tracking_the_full_sequence_of_preference_updates" or question.startswith('User:'):
                filtered_entries.append(qa_entry)
                continue
            
            # 检查问题是否已经检查过
            if question in self.checked_questions:
                if self.checked_questions[question]:
                    filtered_entries.append(qa_entry)
                continue
            
            # 测试问题是否可以在没有上下文的情况下回答
            is_leaked = self.test_question_leakage(qa_entry, max_attempts)
            self.checked_questions[question] = not is_leaked
            
            if not is_leaked:
                filtered_entries.append(qa_entry)
        
        return filtered_entries
    
    def test_question_leakage(self, qa_entry: Dict[str, Any], max_attempts: int = 5) -> bool:
        """
        测试问题是否泄露答案
        
        Args:
            qa_entry: QAR条目
            max_attempts: 最大尝试次数
            
        Returns:
            bool: 是否泄露答案
        """
        question = qa_entry['Question']
        correct_answer = qa_entry['Correct_Answer']
        incorrect_answers = qa_entry.get('Incorrect_Answers', [])
        
        # 确保有足够的错误选项
        if len(incorrect_answers) < 2:
            return False  # 选项不足，无法进行有效测试
        
        # 组合选项
        selected_incorrect = random.sample(incorrect_answers, min(3, len(incorrect_answers)))
        options = [correct_answer] + selected_incorrect
        random.shuffle(options)
        
        correct_index = options.index(correct_answer)
        correct_letter = f"({chr(97 + correct_index)})"
        all_options = [f"({chr(97 + i)}) {option}" for i, option in enumerate(options)]
        
        # 统计测试结果
        correct_count = 0
        total_attempts = 0
        
        # 多次测试
        for _ in range(max_attempts):
            try:
                # 构建纯净的测试数据（只包含问题和选项，无上下文）
                test_data = {
                    'question': question,
                    'options': all_options
                }
                
                # 在没有上下文的情况下测试问题
                model_response = self.llm.query_llm(test_data, 'test_question_leakage', verbose=False)
                score, predicted_answer = self._extract_answer(model_response, correct_letter)
                
                total_attempts += 1
                if score:
                    correct_count += 1
                    
            except Exception:
                continue
        
        # 如果测试次数不足，返回False（保守策略）
        if total_attempts < 3:
            return False
        
        # 计算准确率
        accuracy = correct_count / total_attempts
        
        # 随机猜测的期望准确率（4个选项）
        random_accuracy = 0.25
        
        # 如果准确率显著高于随机猜测，认为有泄漏
        # 使用更严格的阈值：准确率 > 50% 且至少答对2次
        leakage_threshold = 0.5
        
        return accuracy > leakage_threshold and correct_count >= 2
    
    def run_statistical_check(self, qa_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于"6中4"统计规则的问题泄漏检测
        
        Args:
            qa_entry: QAR条目
            
        Returns:
            dict: 包含检测结果的详细信息
        """
        question = qa_entry['Question']
        correct_answer = qa_entry['Correct_Answer']
        incorrect_answers = qa_entry.get('Incorrect_Answers', [])
        
        result = {
            'is_leaked': False,
            'has_strawman': False,
            'most_reasonable_votes': {},
            'most_unreasonable_votes': {},
            'total_calls': 0,
            'successful_calls': 0,
            'test_details': [],
            'statistical_confidence': 0.0
        }
        
        # 确保有足够的错误选项
        if len(incorrect_answers) < 2:
            result['error'] = "Insufficient incorrect answers for testing"
            return result
        
        # 组合选项
        selected_incorrect = random.sample(incorrect_answers, min(3, len(incorrect_answers)))
        options = [correct_answer] + selected_incorrect
        random.shuffle(options)
        
        # 记录正确答案的位置
        correct_index = options.index(correct_answer)
        correct_letter = f"({chr(97 + correct_index)})"
        all_options = [f"({chr(97 + i)}) {option}" for i, option in enumerate(options)]
        
        # 初始化投票统计
        most_reasonable_votes = {}
        most_unreasonable_votes = {}
        
        # 执行6次调用
        for call_num in range(self.n_calls):
            try:
                # 构建双输出测试数据
                test_data = {
                    'question': question,
                    'options': all_options,
                    'correct_answer': correct_answer,
                    'incorrect_answers': selected_incorrect
                }
                
                # 调用LLM进行双输出检测
                model_response = self.llm.query_llm(test_data, 'dual_output_leakage_test', verbose=False)
                most_reasonable, most_unreasonable = self._extract_dual_output(model_response)
                
                result['total_calls'] += 1
                result['successful_calls'] += 1
                
                # 统计最合理选项的投票
                if most_reasonable:
                    most_reasonable_votes[most_reasonable] = most_reasonable_votes.get(most_reasonable, 0) + 1
                
                # 统计最不合理选项的投票
                if most_unreasonable:
                    most_unreasonable_votes[most_unreasonable] = most_unreasonable_votes.get(most_unreasonable, 0) + 1
                
                # 记录每次调用的详情
                result['test_details'].append({
                    'call': call_num + 1,
                    'response': model_response[:150] + "..." if len(model_response) > 150 else model_response,
                    'most_reasonable': most_reasonable,
                    'most_unreasonable': most_unreasonable
                })
                    
            except Exception as e:
                result['test_details'].append({
                    'call': call_num + 1,
                    'error': str(e),
                    'most_reasonable': None,
                    'most_unreasonable': None
                })
                continue
        
        # 更新结果
        result['most_reasonable_votes'] = most_reasonable_votes
        result['most_unreasonable_votes'] = most_unreasonable_votes
        
        # 如果成功调用次数不足，返回保守结果
        if result['successful_calls'] < 4:
            result['error'] = f"Insufficient successful calls: {result['successful_calls']}"
            return result
        
        # 实现"6中4"判定逻辑
        # 1. 泄漏检测：正确答案在most_reasonable_votes中获得≥4票
        correct_reasonable_votes = most_reasonable_votes.get(correct_letter, 0)
        result['is_leaked'] = correct_reasonable_votes >= self.threshold
        
        # 2. 稻草人检测：任意错误答案在most_unreasonable_votes中获得≥4票
        for option_letter in [f"({chr(97 + i)})" for i in range(len(options))]:
            if option_letter != correct_letter:  # 只检查错误选项
                unreasonable_votes = most_unreasonable_votes.get(option_letter, 0)
                if unreasonable_votes >= self.threshold:
                    result['has_strawman'] = True
                    break
        
        # 计算统计置信度（基于成功调用次数）
        result['statistical_confidence'] = result['successful_calls'] / self.n_calls
        
        return result
    
    def test_question_leakage_detailed(self, qa_entry: Dict[str, Any], max_attempts: int = 5) -> Dict[str, Any]:
        """
        详细测试问题是否泄露答案，返回统计信息（保持向后兼容）
        
        Args:
            qa_entry: QAR条目
            max_attempts: 最大尝试次数（已弃用，使用固定6次）
            
        Returns:
            dict: 包含检测结果的详细信息
        """
        # 调用新的统计检测方法
        result = self.run_statistical_check(qa_entry)
        
        # 转换为旧格式以保持兼容性
        # 计算正确答案被选中的次数
        # 从run_statistical_check的结果中获取正确答案的字母标识
        correct_letter = None
        most_reasonable_votes = result.get('most_reasonable_votes', {})
        
        # 找到得票最多的选项作为正确答案
        if most_reasonable_votes:
            correct_letter = max(most_reasonable_votes.items(), key=lambda x: x[1])[0]
        
        # 计算正确答案被选中的次数
        correct_count = 0
        if correct_letter:
            correct_count = most_reasonable_votes.get(correct_letter, 0)
        
        legacy_result = {
            'is_leaked': result.get('is_leaked', False),
            'accuracy': result.get('statistical_confidence', 0.0),
            'correct_count': correct_count,
            'total_attempts': result.get('successful_calls', 0),
            'random_accuracy': 0.25,
            'leakage_threshold': 0.5,
            'test_details': result.get('test_details', []),
            'has_strawman': result.get('has_strawman', False),
            'most_reasonable_votes': most_reasonable_votes,
            'most_unreasonable_votes': result.get('most_unreasonable_votes', {})
        }
        
        return legacy_result
    
    def batch_test_leakage(self, qa_entries: List[Dict[str, Any]], 
                          max_attempts: int = 5) -> Dict[str, Any]:
        """
        批量测试问题泄漏，生成统计报告
        
        Args:
            qa_entries: QAR条目列表
            max_attempts: 每个问题的最大尝试次数
            
        Returns:
            dict: 包含批量测试结果的统计报告
        """
        results = {
            'total_questions': len(qa_entries),
            'leaked_questions': 0,
            'clean_questions': 0,
            'failed_tests': 0,
            'leakage_rate': 0.0,
            'avg_accuracy': 0.0,
            'question_details': [],
            'summary_stats': {}
        }
        
        total_accuracy = 0.0
        valid_tests = 0
        
        for i, qa_entry in enumerate(qa_entries):
            print(f"Testing question {i+1}/{len(qa_entries)}: {qa_entry.get('Question', '')[:50]}...")
            
            # 执行详细测试
            test_result = self.test_question_leakage_detailed(qa_entry, max_attempts)
            
            # 记录结果
            question_result = {
                'index': i,
                'question': qa_entry.get('Question', ''),
                'type': qa_entry.get('Type', ''),
                'is_leaked': test_result.get('is_leaked', False),
                'accuracy': test_result.get('accuracy', 0.0),
                'correct_count': test_result.get('correct_count', 0),
                'total_attempts': test_result.get('total_attempts', 0),
                'error': test_result.get('error', None)
            }
            
            results['question_details'].append(question_result)
            
            # 更新统计
            if test_result.get('error'):
                results['failed_tests'] += 1
            elif test_result.get('is_leaked', False):
                results['leaked_questions'] += 1
            else:
                results['clean_questions'] += 1
            
            # 计算平均准确率
            if test_result.get('total_attempts', 0) > 0:
                total_accuracy += test_result.get('accuracy', 0.0)
                valid_tests += 1
        
        # 计算最终统计
        if valid_tests > 0:
            results['avg_accuracy'] = total_accuracy / valid_tests
        
        if results['total_questions'] > 0:
            results['leakage_rate'] = results['leaked_questions'] / results['total_questions']
        
        # 生成摘要统计
        results['summary_stats'] = {
            'leakage_rate_percentage': round(results['leakage_rate'] * 100, 2),
            'avg_accuracy_percentage': round(results['avg_accuracy'] * 100, 2),
            'clean_rate_percentage': round((results['clean_questions'] / results['total_questions']) * 100, 2) if results['total_questions'] > 0 else 0,
            'failure_rate_percentage': round((results['failed_tests'] / results['total_questions']) * 100, 2) if results['total_questions'] > 0 else 0
        }
        
        return results
    
    def _extract_answer(self, response: str, correct_answer: str) -> Tuple[bool, str]:
        """
        从模型响应中提取答案并评分
        
        Args:
            response: 模型响应
            correct_answer: 正确答案
            
        Returns:
            tuple: (是否正确, 预测答案)
        """
        # 清理响应文本
        response = response.strip().lower()
        
        # 多种答案格式的正则表达式
        patterns = [
            r'\(([a-d])\)',  # (a), (b), (c), (d)
            r'\b([a-d])\b',  # 单独的字母 a, b, c, d
            r'选项\s*([a-d])',  # 选项a, 选项b等
            r'答案\s*([a-d])',  # 答案a, 答案b等
            r'选择\s*([a-d])',  # 选择a, 选择b等
        ]
        
        predicted_answer = None
        for pattern in patterns:
            matches = re.findall(pattern, response)
            if matches:
                predicted_answer = f"({matches[0]})"
                break
        
        # 如果没找到标准格式，尝试从文本中提取最后一个字母
        if not predicted_answer:
            # 查找所有可能的字母
            letter_matches = re.findall(r'[a-d]', response)
            if letter_matches:
                predicted_answer = f"({letter_matches[-1]})"  # 取最后一个字母
        
        if predicted_answer:
            score = (predicted_answer == correct_answer)
            return score, predicted_answer
        
        return False, None
    
    def _extract_dual_output(self, response: str) -> Tuple[str, str]:
        """
        从模型响应中提取双输出结果（最合理和最不合理选项）
        
        Args:
            response: 模型响应
            
        Returns:
            tuple: (最合理选项, 最不合理选项)
        """
        # 清理响应文本
        response = response.strip().lower()
        
        most_reasonable = None
        most_unreasonable = None
        
        # 查找"最合理"选项
        reasonable_patterns = [
            r'最合理[：:]\s*\(([a-d])\)',
            r'最合理[：:]\s*([a-d])',
            r'reasonable[：:]\s*\(([a-d])\)',
            r'reasonable[：:]\s*([a-d])'
        ]
        
        for pattern in reasonable_patterns:
            matches = re.findall(pattern, response)
            if matches:
                most_reasonable = f"({matches[0]})"
                break
        
        # 查找"最不合理"选项
        unreasonable_patterns = [
            r'最不合理[：:]\s*\(([a-d])\)',
            r'最不合理[：:]\s*([a-d])',
            r'unreasonable[：:]\s*\(([a-d])\)',
            r'unreasonable[：:]\s*([a-d])'
        ]
        
        for pattern in unreasonable_patterns:
            matches = re.findall(pattern, response)
            if matches:
                most_unreasonable = f"({matches[0]})"
                break
        
        # 如果没找到标准格式，尝试从文本中提取
        if not most_reasonable or not most_unreasonable:
            # 查找所有可能的字母
            letter_matches = re.findall(r'[a-d]', response)
            if len(letter_matches) >= 2:
                if not most_reasonable:
                    most_reasonable = f"({letter_matches[0]})"
                if not most_unreasonable:
                    most_unreasonable = f"({letter_matches[1]})"
        
        return most_reasonable, most_unreasonable


class OptionBalancer:
    """选项平衡模块 - 基于LLM语义理解实现选项平衡"""
    
    def __init__(self, llm_interface: LLMInterface):
        """
        初始化选项平衡器
        
        Args:
            llm_interface: LLM接口实例
        """
        self.llm = llm_interface
    
    def balance_options_semantically(self, qa_entry: Dict[str, Any], strategy: str = 'single') -> Dict[str, Any]:
        """
        基于LLM语义理解实现选项平衡，重写选项以保持信息密度和结构复杂度一致
        
        Args:
            qa_entry: QAR条目
            strategy: 改写策略 ('single' 或 'multiple')
                - 'single': 一次改写一个选项，更精确但成本更高
                - 'multiple': 一次改写多个选项，更高效但可能不够精确
            
        Returns:
            dict: 平衡后的QAR条目
        """
        if not qa_entry.get('Correct_Answer') or not qa_entry.get('Incorrect_Answers'):
            return qa_entry
        
        correct_answer = qa_entry['Correct_Answer']
        incorrect_answers = qa_entry['Incorrect_Answers']
        question = qa_entry.get('Question', '')
        
        # 识别目标选项（正确答案）
        target_option = correct_answer
        
        # 构建所有选项列表（用于上下文）
        all_options = [f"({chr(97 + i)}) {option}" for i, option in enumerate([correct_answer] + incorrect_answers)]
        
        if strategy == 'single':
            # 策略1：一次改写一个选项
            balanced_incorrect_answers = self._rewrite_options_individually(
                question, all_options, target_option, incorrect_answers
            )
        elif strategy == 'multiple':
            # 策略2：一次改写多个选项
            balanced_incorrect_answers = self._rewrite_options_batch(
                question, all_options, target_option, incorrect_answers
            )
        else:
            raise ValueError(f"Invalid strategy: {strategy}. Must be 'single' or 'multiple'")
        
        # 更新QAR条目
        qa_entry['Incorrect_Answers'] = balanced_incorrect_answers
        
        return qa_entry
    
    def _rewrite_options_individually(self, question: str, all_options: List[str], 
                                    target_option: str, incorrect_answers: List[str]) -> List[str]:
        """
        策略1：一次改写一个选项，更精确但成本更高
        
        Args:
            question: 问题文本
            all_options: 所有选项列表
            target_option: 目标选项（参考选项）
            incorrect_answers: 错误选项列表
            
        Returns:
            list: 改写后的错误选项列表
        """
        balanced_incorrect_answers = []
        
        for i, incorrect_option in enumerate(incorrect_answers):
            try:
                rewritten_option = self._rewrite_single_option_with_llm(
                    question, all_options, target_option, incorrect_option, i
                )
                balanced_incorrect_answers.append(rewritten_option)
            except Exception as e:
                # 如果重写失败，使用原始选项
                print(f"Warning: Failed to rewrite option {i+1}: {e}")
                balanced_incorrect_answers.append(incorrect_option)
        
        return balanced_incorrect_answers
    
    def _rewrite_options_batch(self, question: str, all_options: List[str], 
                             target_option: str, incorrect_answers: List[str]) -> List[str]:
        """
        策略2：一次改写多个选项，更高效但可能不够精确
        
        Args:
            question: 问题文本
            all_options: 所有选项列表
            target_option: 目标选项（参考选项）
            incorrect_answers: 错误选项列表
            
        Returns:
            list: 改写后的错误选项列表
        """
        try:
            # 构建批量改写请求数据
            batch_rewrite_data = {
                'question': question,
                'all_options': all_options,
                'target_option': target_option,
                'options_to_rewrite': incorrect_answers
            }
            
            # 调用LLM进行批量改写
            batch_response = self.llm.query_llm(batch_rewrite_data, 'rewrite_multiple_options_for_balance', verbose=False)
            
            # 提取批量改写结果
            rewritten_options = self._extract_multiple_rewritten_options(batch_response, incorrect_answers)
            
            return rewritten_options
            
        except Exception as e:
            print(f"Warning: Batch rewrite failed: {e}, falling back to individual rewrite")
            # 如果批量改写失败，回退到单个改写
            return self._rewrite_options_individually(question, all_options, target_option, incorrect_answers)
    
    def _rewrite_single_option_with_llm(self, question: str, all_options: List[str], 
                                       target_option: str, option_to_rewrite: str, option_index: int) -> str:
        """
        使用LLM重写单个选项，使其在风格、长度和复杂度上与目标选项保持一致
        
        Args:
            question: 问题文本
            all_options: 所有选项列表
            target_option: 目标选项（参考选项）
            option_to_rewrite: 待重写的选项
            option_index: 选项索引
            
        Returns:
            str: 重写后的选项
        """
        # 构建重写请求数据
        rewrite_data = {
            'question': question,
            'all_options': all_options,
            'target_option': target_option,
            'option_to_rewrite': option_to_rewrite
        }
        
        # 调用LLM进行重写
        rewritten_response = self.llm.query_llm(rewrite_data, 'rewrite_option_for_balance', verbose=False)
        
        # 提取重写后的选项
        rewritten_option = self._extract_rewritten_option(rewritten_response, option_to_rewrite)
        
        return rewritten_option
    
    def _extract_multiple_rewritten_options(self, response: str, original_options: List[str]) -> List[str]:
        """
        从LLM批量响应中提取多个重写后的选项
        
        Args:
            response: LLM响应
            original_options: 原始选项列表
            
        Returns:
            list: 重写后的选项列表
        """
        # 清理响应文本
        response = response.strip()
        
        rewritten_options = []
        
        # 查找编号格式的选项 (1. 内容, 2. 内容, ...)
        numbered_pattern = r'(\d+)\.\s*(.+?)(?=\n\d+\.|\n*$)'
        matches = re.findall(numbered_pattern, response, re.MULTILINE | re.DOTALL)
        
        if matches:
            # 按编号排序
            matches.sort(key=lambda x: int(x[0]))
            for _, content in matches:
                content = content.strip()
                if content and len(content) > 10:
                    rewritten_options.append(content)
        
        # 如果编号格式解析失败，尝试其他格式
        if len(rewritten_options) != len(original_options):
            # 尝试按行分割
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            for line in lines:
                # 移除可能的编号前缀
                cleaned_line = re.sub(r'^\d+\.\s*', '', line)
                if cleaned_line and len(cleaned_line) > 10:
                    rewritten_options.append(cleaned_line)
        
        # 确保返回的选项数量与原始选项数量一致
        if len(rewritten_options) < len(original_options):
            # 如果重写选项不足，用原始选项补充
            for i in range(len(rewritten_options), len(original_options)):
                rewritten_options.append(original_options[i])
        elif len(rewritten_options) > len(original_options):
            # 如果重写选项过多，只取前N个
            rewritten_options = rewritten_options[:len(original_options)]
        
        return rewritten_options
    
    def _extract_rewritten_option(self, response: str, original_option: str) -> str:
        """
        从LLM响应中提取重写后的选项
        
        Args:
            response: LLM响应
            original_option: 原始选项
            
        Returns:
            str: 重写后的选项
        """
        # 清理响应文本
        response = response.strip()
        
        # 查找重写后的选项模式
        patterns = [
            r'改写后的选项[：:]\s*(.+)',
            r'rewritten option[：:]\s*(.+)',
            r'\([a-d]\)\s*(.+)',  # 选项格式 (a) 内容
            r'^(.+)$'  # 如果只有一行，直接使用
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.MULTILINE | re.DOTALL)
            if matches:
                rewritten = matches[0].strip()
                # 确保重写后的选项不为空且与原始选项不同
                if rewritten and len(rewritten) > 10:
                    return rewritten
        
        # 如果无法提取，返回原始选项
        return original_option
    
    def ensure_option_length_balance(self, options: List[str], 
                                   max_variance: float = 0.3) -> List[str]:
        """
        确保所有选项长度相似，防止模型通过长度判断答案（保持向后兼容）
        
        Args:
            options: 选项列表
            max_variance: 最大长度方差比例
            
        Returns:
            list: 平衡后的选项列表
        """
        if not options:
            return options
        
        # 计算平均长度
        lengths = [len(option) for option in options]
        avg_length = sum(lengths) / len(lengths)
        
        # 计算方差
        variance = sum((length - avg_length) ** 2 for length in lengths) / len(lengths)
        variance_ratio = variance / (avg_length ** 2) if avg_length > 0 else 0
        
        # 如果方差过大，进行调整
        if variance_ratio > max_variance:
            balanced_options = []
            for option in options:
                if len(option) < avg_length * 0.7:  # 太短
                    option += " This option provides additional context and details."
                elif len(option) > avg_length * 1.3:  # 太长
                    option = option[:int(avg_length * 1.2)] + "..."
                balanced_options.append(option)
            return balanced_options
        
        return options
    
    def ensure_diverse_incorrect_options(self, correct_answer: str, 
                                      incorrect_answers: List[str], 
                                      qa_type: str) -> List[str]:
        """
        确保错误选项的多样性，避免过于相似的选项
        
        Args:
            correct_answer: 正确答案
            incorrect_answers: 错误选项列表
            qa_type: QAR类型
            
        Returns:
            list: 多样化的错误选项列表
        """
        if len(incorrect_answers) >= 3:
            return incorrect_answers[:3]
        
        # 生成不同类型的错误选项
        error_types = [
            "完全遗忘型",  # 模型完全忘记了用户信息
            "错误记忆型",  # 模型记错了用户偏好
            "刻板印象型"   # 基于用户身份的刻板印象
        ]
        
        diverse_options = incorrect_answers.copy()
        for i in range(len(incorrect_answers), 3):
            error_type = error_types[i % len(error_types)]
            generic_error = f"Generic response based on {error_type} assumption"
            diverse_options.append(generic_error)
        
        return diverse_options[:3]


class QualityValidator:
    """质量验证模块 - 专门处理QAR条目质量验证"""
    
    def validate_qa_entry(self, qa_entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证QAR条目的质量
        
        Args:
            qa_entry: QAR条目
            
        Returns:
            tuple: (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查必需字段
        required_fields = ['Question', 'Correct_Answer']
        for field in required_fields:
            if field not in qa_entry or not qa_entry[field]:
                errors.append(f"Missing required field: {field}")
        
        # 检查错误选项
        incorrect_answers = qa_entry.get('Incorrect_Answers', [])
        if len(incorrect_answers) < 1:
            errors.append("Insufficient incorrect answers")
        
        # 检查问题长度
        question = qa_entry.get('Question', '')
        if len(question) < 10:
            errors.append("Question too short")
        elif len(question) > 500:
            errors.append("Question too long")
        
        # 检查选项长度平衡
        options = [qa_entry.get('Correct_Answer', '')] + incorrect_answers
        lengths = [len(opt) for opt in options]
        if lengths:
            max_length = max(lengths)
            min_length = min(lengths)
            if max_length > min_length * 3:  # 长度差异过大
                errors.append("Option lengths too imbalanced")
        
        # 特殊检查：Profile-adaptive QAR
        if qa_entry.get('Type') == 'profile_adaptive_qa':
            # 检查是否同时包含Profile和Reference信息
            if not qa_entry.get('Profile'):
                errors.append("Profile-adaptive QAR missing Profile data")
            if not qa_entry.get('Reference'):
                errors.append("Profile-adaptive QAR missing Reference data")
            
            # 检查错误选项数量（Profile-adaptive需要3个错误选项）
            if len(incorrect_answers) < 3:
                errors.append(f"Profile-adaptive QAR requires exactly 3 incorrect answers, got {len(incorrect_answers)}")
            
            # 检查选项长度一致性（Profile-adaptive要求更严格）
            if lengths:
                max_length = max(lengths)
                min_length = min(lengths)
                if max_length > min_length * 2:  # Profile-adaptive要求更严格的长度平衡
                    errors.append("Profile-adaptive QAR option lengths too varied")
        
        return len(errors) == 0, errors
    
    def calculate_context_distance(self, qa_entry: Dict[str, Any], 
                                 context_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算问题到相关信息的距离（块数、token数等）
        
        Args:
            qa_entry: QAR条目
            context_info: 上下文信息
            
        Returns:
            dict: 距离信息
        """
        distance_info = {
            'distance_blocks': qa_entry.get('distance_blocks', 0),
            'distance_tokens': qa_entry.get('distance_tokens', 0),
            'context_length_in_tokens': context_info.get('context_length_in_tokens', 0),
            'context_length_in_letters': context_info.get('context_length_in_letters', 0),
            'num_irrelevant_tokens': context_info.get('num_irrelevant_tokens', 0)
        }
        
        return distance_info


class StatsGenerator:
    """统计生成模块 - 专门处理质量控制统计信息生成"""
    
    def generate_quality_stats(self, qa_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成质量控制统计信息
        
        Args:
            qa_entries: QAR条目列表
            
        Returns:
            dict: 质量统计信息
        """
        if not qa_entries:
            return {}
        
        stats = {
            'total_questions': len(qa_entries),
            'avg_option_length': 0,
            'length_variance': 0,
            'balanced_questions': 0,
            'type_distribution': {},
            'topic_distribution': {}
        }
        
        all_lengths = []
        balanced_count = 0
        
        for entry in qa_entries:
            # 统计选项长度
            options = [entry.get('Correct_Answer', '')] + entry.get('Incorrect_Answers', [])
            lengths = [len(opt) for opt in options]
            all_lengths.extend(lengths)
            
            # 检查是否平衡
            if len(set(lengths)) <= 2:  # 长度变化不大
                balanced_count += 1
            
            # 统计类型分布
            qa_type = entry.get('Type', 'unknown')
            stats['type_distribution'][qa_type] = stats['type_distribution'].get(qa_type, 0) + 1
            
            # 统计话题分布
            topic = entry.get('Topic', 'unknown')
            stats['topic_distribution'][topic] = stats['topic_distribution'].get(topic, 0) + 1
        
        if all_lengths:
            stats['avg_option_length'] = sum(all_lengths) / len(all_lengths)
            avg_length = stats['avg_option_length']
            stats['length_variance'] = sum((x - avg_length) ** 2 for x in all_lengths) / len(all_lengths)
        
        stats['balanced_questions'] = balanced_count
        
        return stats


class QualityController:
    """QAR质量控制器 - 整合所有质量控制模块"""
    
    def __init__(self, llm_interface: LLMInterface):
        """
        初始化质量控制器
        
        Args:
            llm_interface: LLM接口实例
        """
        self.llm = llm_interface
        self.leakage_detector = LeakageDetector(llm_interface)
        self.option_balancer = OptionBalancer(llm_interface)
        self.quality_validator = QualityValidator()
        self.stats_generator = StatsGenerator()
        self.length_threshold = 0.2  # ±20% 长度差异阈值
    
    # 泄漏检测相关方法
    def filter_leaked_questions(self, qa_entries: List[Dict[str, Any]], 
                              max_attempts: int = 3) -> List[Dict[str, Any]]:
        """过滤掉可能泄露答案的问题"""
        return self.leakage_detector.filter_leaked_questions(qa_entries, max_attempts)
    
    def test_question_leakage(self, qa_entry: Dict[str, Any], max_attempts: int = 5) -> bool:
        """测试问题是否泄露答案"""
        return self.leakage_detector.test_question_leakage(qa_entry, max_attempts)
    
    def test_question_leakage_detailed(self, qa_entry: Dict[str, Any], max_attempts: int = 5) -> Dict[str, Any]:
        """详细测试问题是否泄露答案，返回统计信息"""
        return self.leakage_detector.test_question_leakage_detailed(qa_entry, max_attempts)
    
    def batch_test_leakage(self, qa_entries: List[Dict[str, Any]], 
                          max_attempts: int = 5) -> Dict[str, Any]:
        """批量测试问题泄漏，生成统计报告"""
        return self.leakage_detector.batch_test_leakage(qa_entries, max_attempts)
    
    def run_statistical_check(self, qa_entry: Dict[str, Any]) -> Dict[str, Any]:
        """基于6中4统计规则的问题泄漏检测"""
        return self.leakage_detector.run_statistical_check(qa_entry)
    
    # 选项平衡相关方法
    def ensure_option_length_balance(self, options: List[str], 
                                   max_variance: float = 0.3) -> List[str]:
        """确保所有选项长度相似，防止模型通过长度判断答案"""
        return self.option_balancer.ensure_option_length_balance(options, max_variance)
    
    def ensure_diverse_incorrect_options(self, correct_answer: str, 
                                      incorrect_answers: List[str], 
                                      qa_type: str) -> List[str]:
        """确保错误选项的多样性，避免过于相似的选项"""
        return self.option_balancer.ensure_diverse_incorrect_options(correct_answer, incorrect_answers, qa_type)
    
    def balance_options_semantically(self, qa_entry: Dict[str, Any], strategy: str = 'single') -> Dict[str, Any]:
        """基于LLM语义理解实现选项平衡"""
        return self.option_balancer.balance_options_semantically(qa_entry, strategy)
    
    # 质量验证相关方法
    def validate_qa_entry(self, qa_entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证QAR条目的质量"""
        return self.quality_validator.validate_qa_entry(qa_entry)
    
    def calculate_context_distance(self, qa_entry: Dict[str, Any], 
                                 context_info: Dict[str, Any]) -> Dict[str, Any]:
        """计算问题到相关信息的距离（块数、token数等）"""
        return self.quality_validator.calculate_context_distance(qa_entry, context_info)
    
    # 统计生成相关方法
    def generate_quality_stats(self, qa_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成质量控制统计信息"""
        return self.stats_generator.generate_quality_stats(qa_entries)
    
    # 核心自检流程
    def comprehensive_quality_check(self, qa_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        综合质量控制自检流程
        
        流程：
        1. 检查长度差异（±20%阈值）
        2. 如果有严重差异，改写单个过长/过短选项
        3. 进行泄漏测试
        4. 如果泄漏测试失败，根据泄漏类型进行全选项改写
        
        Args:
            qa_entry: QAR条目
            
        Returns:
            dict: 质量控制结果
        """
        result = {
            'original_qa': qa_entry.copy(),
            'final_qa': qa_entry.copy(),
            'quality_passed': False,
            'steps_taken': [],
            'leakage_info': {},
            'length_analysis': {},
            'rewrite_history': []
        }
        
        # 步骤1：长度差异分析
        length_analysis = self._analyze_length_differences(qa_entry)
        result['length_analysis'] = length_analysis
        
        if length_analysis['has_severe_differences']:
            result['steps_taken'].append('length_balance')
            # 步骤2：改写单个过长/过短选项
            balanced_qa = self._balance_individual_options(qa_entry.copy(), length_analysis)
            result['rewrite_history'].append({
                'step': 'individual_balance',
                'reason': 'length_differences',
                'options_changed': length_analysis['problematic_options']
            })
            qa_entry = balanced_qa
        
        # 步骤3：泄漏测试
        leakage_result = self.run_statistical_check(qa_entry)
        result['leakage_info'] = leakage_result
        
        if leakage_result.get('is_leaked', False) or leakage_result.get('has_strawman', False):
            result['steps_taken'].append('leakage_correction')
            # 步骤4：根据泄漏类型进行全选项改写
            corrected_qa = self._correct_leakage_issues(qa_entry.copy(), leakage_result)
            result['rewrite_history'].append({
                'step': 'leakage_correction',
                'reason': 'leakage_detected',
                'leakage_type': 'answer_leakage' if leakage_result.get('is_leaked') else 'strawman_detected'
            })
            qa_entry = corrected_qa
        
        # 最终验证
        final_leakage_check = self.run_statistical_check(qa_entry)
        result['final_leakage_check'] = final_leakage_check
        
        # 判断质量是否通过
        result['quality_passed'] = not (final_leakage_check.get('is_leaked', False) or 
                                       final_leakage_check.get('has_strawman', False))
        
        result['final_qa'] = qa_entry
        
        return result
    
    def _analyze_length_differences(self, qa_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析选项长度差异
        
        Args:
            qa_entry: QAR条目
            
        Returns:
            dict: 长度分析结果
        """
        correct_answer = qa_entry.get('Correct_Answer', '')
        incorrect_answers = qa_entry.get('Incorrect_Answers', [])
        
        if not correct_answer or not incorrect_answers:
            return {'has_severe_differences': False}
        
        all_options = [correct_answer] + incorrect_answers
        lengths = [len(option) for option in all_options]
        
        # 计算长度统计
        avg_length = sum(lengths) / len(lengths)
        max_length = max(lengths)
        min_length = min(lengths)
        
        # 检查是否有严重差异（±20%）
        problematic_options = []
        for i, length in enumerate(lengths):
            length_ratio = length / avg_length
            if length_ratio < (1 - self.length_threshold) or length_ratio > (1 + self.length_threshold):
                problematic_options.append({
                    'index': i,
                    'option': all_options[i],
                    'length': length,
                    'ratio': length_ratio,
                    'type': 'too_short' if length_ratio < (1 - self.length_threshold) else 'too_long'
                })
        
        return {
            'has_severe_differences': len(problematic_options) > 0,
            'avg_length': avg_length,
            'max_length': max_length,
            'min_length': min_length,
            'length_variance': max_length / min_length if min_length > 0 else 1,
            'problematic_options': problematic_options,
            'all_lengths': lengths
        }
    
    def _balance_individual_options(self, qa_entry: Dict[str, Any], length_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        改写单个过长/过短选项
        
        Args:
            qa_entry: QAR条目
            length_analysis: 长度分析结果
            
        Returns:
            dict: 平衡后的QAR条目
        """
        correct_answer = qa_entry['Correct_Answer']
        incorrect_answers = qa_entry['Incorrect_Answers']
        question = qa_entry.get('Question', '')
        
        # 构建所有选项列表
        all_options = [f"({chr(97 + i)}) {option}" for i, option in enumerate([correct_answer] + incorrect_answers)]
        
        # 只改写有问题的错误选项
        for problem_option in length_analysis['problematic_options']:
            option_index = problem_option['index']
            if option_index > 0:  # 只处理错误选项（索引>0）
                incorrect_index = option_index - 1  # 转换为错误选项索引
                try:
                    rewritten_option = self.option_balancer._rewrite_single_option_with_llm(
                        question, all_options, correct_answer, incorrect_answers[incorrect_index], incorrect_index
                    )
                    incorrect_answers[incorrect_index] = rewritten_option
                except Exception as e:
                    print(f"Warning: Failed to rewrite problematic option {incorrect_index}: {e}")
        
        qa_entry['Incorrect_Answers'] = incorrect_answers
        return qa_entry
    
    def _correct_leakage_issues(self, qa_entry: Dict[str, Any], leakage_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据泄漏类型进行全选项改写
        
        Args:
            qa_entry: QAR条目
            leakage_result: 泄漏检测结果
            
        Returns:
            dict: 修正后的QAR条目
        """
        # 确定泄漏类型和提示信息
        if leakage_result.get('is_leaked', False):
            leakage_type = "answer_leakage"
            leakage_description = "正确答案信息泄漏"
            correction_instruction = "正确答案的信息过于明显，需要让所有选项在信息密度和表达方式上更加平衡"
        elif leakage_result.get('has_strawman', False):
            leakage_type = "strawman_detected"
            leakage_description = "稻草人选项过于明显"
            correction_instruction = "某些错误选项过于明显（稻草人），需要让所有选项看起来都更加合理和专业"
        else:
            return qa_entry
        
        # 使用批量改写策略，并告知泄漏信息
        try:
            corrected_qa = self._rewrite_with_leakage_feedback(qa_entry, leakage_type, correction_instruction)
            return corrected_qa
        except Exception as e:
            print(f"Warning: Failed to correct leakage issues: {e}")
            return qa_entry
    
    def _rewrite_with_leakage_feedback(self, qa_entry: Dict[str, Any], leakage_type: str, correction_instruction: str) -> Dict[str, Any]:
        """
        基于泄漏反馈进行全选项改写
        
        Args:
            qa_entry: QAR条目
            leakage_type: 泄漏类型
            correction_instruction: 修正指令
            
        Returns:
            dict: 修正后的QAR条目
        """
        correct_answer = qa_entry['Correct_Answer']
        incorrect_answers = qa_entry['Incorrect_Answers']
        question = qa_entry.get('Question', '')
        
        # 构建所有选项列表
        all_options = [f"({chr(97 + i)}) {option}" for i, option in enumerate([correct_answer] + incorrect_answers)]
        
        # 构建带泄漏反馈的改写请求
        leakage_feedback_data = {
            'question': question,
            'all_options': all_options,
            'target_option': correct_answer,
            'options_to_rewrite': incorrect_answers,
            'leakage_type': leakage_type,
            'correction_instruction': correction_instruction
        }
        
        # 调用LLM进行带反馈的批量改写
        batch_response = self.llm.query_llm(leakage_feedback_data, 'rewrite_with_leakage_feedback', verbose=False)
        
        # 提取改写结果
        rewritten_options = self.option_balancer._extract_multiple_rewritten_options(batch_response, incorrect_answers)
        
        qa_entry['Incorrect_Answers'] = rewritten_options
        return qa_entry