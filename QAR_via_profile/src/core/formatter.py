"""
选择题格式化器
"""

import random
import uuid
from typing import List, Dict, Any, Optional
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from quality_control import QualityController


class QARFormatter:
    """QAR选择题格式化器"""
    
    def __init__(self, quality_controller: Optional[QualityController] = None):
        """
        初始化格式化器
        
        Args:
            quality_controller: 质量控制器实例
        """
        self.quality_controller = quality_controller
    
    def format_single_qa(self, qa_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        格式化单个QAR条目为选择题格式
        
        Args:
            qa_entry: QAR条目字典，包含:
                - Question: 问题
                - Correct_Answer: 正确答案
                - Incorrect_Answers: 错误选项列表
                - Type: QAR类型
                - Topic: 话题
                - Reference: 参考信息
                
        Returns:
            dict: 格式化后的选择题字典
        """
        if not qa_entry or 'Question' not in qa_entry:
            return None
        
        # 提取基本信息
        question = qa_entry['Question']
        correct_answer = qa_entry['Correct_Answer']
        incorrect_answers = qa_entry.get('Incorrect_Answers', [])
        
        # 确保有足够的错误选项
        if len(incorrect_answers) < 3:
            # 如果错误选项不足，补充一些通用选项
            generic_options = [
                "I don't have enough information to provide a specific recommendation.",
                "Based on general preferences, I would suggest exploring different options.",
                "Let me provide some general advice that might be helpful."
            ]
            while len(incorrect_answers) < 3:
                incorrect_answers.append(generic_options[len(incorrect_answers) % len(generic_options)])
        
        # 随机选择3个错误选项
        selected_incorrect = random.sample(incorrect_answers, min(3, len(incorrect_answers)))
        
        # 组合所有选项并打乱
        options = [correct_answer] + selected_incorrect
        random.shuffle(options)
        
        # 应用质量控制：选项长度平衡
        if self.quality_controller:
            options = self.quality_controller.ensure_option_length_balance(options)
        
        # 找到正确答案的位置
        correct_index = options.index(correct_answer)
        correct_letter = chr(97 + correct_index)  # 转换为字母 (a, b, c, d)
        
        # 生成格式化的问题
        formatted_question = f"Question: {question}\nAnswer:\n"
        for i, option in enumerate(options):
            formatted_question += f"({chr(97 + i)}) {option}\n"
        formatted_question += "\n.Respond with the correct option, including both the letter (a), (b), (c), or (d). Do not include other information."
        
        # 生成所有选项的列表
        all_options = [f"({chr(97 + i)}) {option}" for i, option in enumerate(options)]
        
        # 创建格式化后的条目
        formatted_entry = {
            "question_id": str(uuid.uuid4()),
            "question": question,
            "correct_answer": f"({correct_letter})",
            "correct_answer_text": correct_answer,
            "all_options": all_options,
            "formatted_question": formatted_question,
            "question_type": qa_entry.get('Type', 'unknown'),
            "topic": qa_entry.get('Topic', 'unknown'),
            "reference": qa_entry.get('Reference', {}),
            "options": options,
            "correct_index": correct_index
        }
        
        return formatted_entry
    
    def format_multiple_qa(self, qa_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量格式化多个QAR条目
        
        Args:
            qa_entries: QAR条目列表
            
        Returns:
            list: 格式化后的选择题列表
        """
        formatted_entries = []
        
        for qa_entry in qa_entries:
            formatted_entry = self.format_single_qa(qa_entry)
            if formatted_entry:
                formatted_entries.append(formatted_entry)
        
        return formatted_entries
    
    def create_question_loader(self, qa_entries: List[Dict[str, Any]]):
        """
        创建问题加载器生成器
        
        Args:
            qa_entries: QAR条目列表
            
        Yields:
            dict: 格式化后的选择题条目
        """
        for qa_entry in qa_entries:
            formatted_entry = self.format_single_qa(qa_entry)
            if formatted_entry:
                yield formatted_entry
    
    def validate_qa_entry(self, qa_entry: Dict[str, Any]) -> bool:
        """
        验证QAR条目的有效性
        
        Args:
            qa_entry: QAR条目
            
        Returns:
            bool: 是否有效
        """
        required_fields = ['Question', 'Correct_Answer']
        
        for field in required_fields:
            if field not in qa_entry or not qa_entry[field]:
                return False
        
        # 检查是否有足够的错误选项
        incorrect_answers = qa_entry.get('Incorrect_Answers', [])
        if len(incorrect_answers) < 1:
            return False
        
        return True
    
    def filter_valid_qa(self, qa_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤出有效的QAR条目
        
        Args:
            qa_entries: QAR条目列表
            
        Returns:
            list: 有效的QAR条目列表
        """
        valid_entries = []
        
        for qa_entry in qa_entries:
            if self.validate_qa_entry(qa_entry):
                valid_entries.append(qa_entry)
        
        return valid_entries
    
    def export_to_json(self, formatted_entries: List[Dict[str, Any]], output_path: str):
        """
        导出格式化后的选择题到JSON文件
        
        Args:
            formatted_entries: 格式化后的选择题列表
            output_path: 输出文件路径
        """
        import json
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_entries, f, ensure_ascii=False, indent=2)
    
    def export_to_csv(self, formatted_entries: List[Dict[str, Any]], output_path: str):
        """
        导出格式化后的选择题到CSV文件
        
        Args:
            formatted_entries: 格式化后的选择题列表
            output_path: 输出文件路径
        """
        import csv
        
        if not formatted_entries:
            return
        
        # 获取所有字段名
        fieldnames = list(formatted_entries[0].keys())
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(formatted_entries)
    
    def get_statistics(self, formatted_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取格式化后的选择题统计信息
        
        Args:
            formatted_entries: 格式化后的选择题列表
            
        Returns:
            dict: 统计信息
        """
        if not formatted_entries:
            return {}
        
        # 统计各类型问题数量
        type_counts = {}
        topic_counts = {}
        
        for entry in formatted_entries:
            qa_type = entry.get('question_type', 'unknown')
            topic = entry.get('topic', 'unknown')
            
            type_counts[qa_type] = type_counts.get(qa_type, 0) + 1
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return {
            'total_questions': len(formatted_entries),
            'type_distribution': type_counts,
            'topic_distribution': topic_counts,
            'average_options_per_question': sum(len(entry.get('options', [])) for entry in formatted_entries) / len(formatted_entries)
        }
