"""
QAR生成器核心类
"""

import json
import random
from typing import List, Dict, Any, Optional
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from llm_interface import LLMInterface
from .quality_control import QualityController


class QARGenerator:
    """QAR选择题生成器核心类"""
    
    def __init__(self, model: str = None):
        """
        初始化QAR生成器
        
        Args:
            model: 使用的模型名称（可选，默认使用配置中的模型）
        """
        self.llm = LLMInterface(model)
        self.quality_controller = QualityController(self.llm)
    
    
    
    
    def generate_multiple_qa(self, key_info_list: List[Dict[str, Any]], 
                           qa_types: List[str] = None, 
                           verbose: bool = False,
                           apply_quality_control: bool = True) -> List[Dict[str, Any]]:
        """
        批量生成多个QAR
        
        Args:
            key_info_list: 关键信息列表
            qa_types: QAR类型列表，如果为None则使用所有类型
            verbose: 是否打印详细信息
            apply_quality_control: 是否应用质量控制
            
        Returns:
            list: QAR条目列表
        """
        if qa_types is None:
            qa_types = ['profile_adaptive', 'constraint_qa', 'progress_continuation_qa', 'conflict_resolution_qa', 'active_reminder_qa']
        
        all_qa_entries = []
        
        for key_info in key_info_list:
            for qa_type in qa_types:
                try:
                    qa_entry = self.generate_qa_by_type(key_info, qa_type, verbose, apply_quality_control)
                    if qa_entry:
                        all_qa_entries.append(qa_entry)
                except Exception as e:
                    if verbose:
                        print(f"Error generating {qa_type} QAR: {e}")
                    continue
        
        # 应用质量控制
        if apply_quality_control and all_qa_entries:
            if verbose:
                print("Applying quality control...")
            all_qa_entries = self.quality_controller.filter_leaked_questions(all_qa_entries)
            
            # 生成质量统计
            quality_stats = self.quality_controller.generate_quality_stats(all_qa_entries)
            if verbose:
                print(f"Quality stats: {quality_stats}")
        
        return all_qa_entries
    
    def generate_profile_adaptive_qa(self, combined_data: Dict[str, Any], verbose: bool = False, apply_quality_control: bool = True) -> Optional[Dict[str, Any]]:
        """
        基于Reference和Profile数据生成自适应QAR
        
        Args:
            combined_data: 组合数据字典，包含:
                - complex_question: 复杂问题
                - ground_truth_answer: 正确答案
                - supporting_evidence: 支持证据
                - profile_data: Profile数据
            verbose: 是否打印详细信息
            
        Returns:
            dict: QAR条目
        """
        # 构建符合prompt期望的数据结构
        profile_data = combined_data.get('profile_data', {})
        
        # 从supporting_evidence中提取对话内容
        dialogue_content = []
        if 'supporting_evidence' in combined_data:
            for evidence in combined_data['supporting_evidence']:
                if 'content' in evidence and 'dialogue' in evidence['content']:
                    dialogue_content.append({
                        'character_name': evidence.get('character_name', ''),
                        'dialogue': evidence['content']['dialogue']
                    })
        
        data = {
            'reference_type': 'evaluation_checkpoint',
            'event_description': combined_data.get('complex_question', ''),
            'key_information': combined_data.get('ground_truth_answer', ''),
            'dialogue_content': dialogue_content,
            'character_name': profile_data.get('character_name', ''),
            'character_occupation': profile_data.get('character_occupation', ''),
            'communication_style': profile_data.get('communication_style', ''),
            'domain_knowledge': profile_data.get('domain_knowledge', [])
        }
        
        # 生成Profile自适应QAR条目
        qa_pair = self.llm.generate_qa_pair(data, 'profile_adaptive_qa', verbose)
        question = qa_pair.get("Question", "")
        correct_answer = qa_pair.get("Correct_Answer", "")
        incorrect_answers = qa_pair.get("Incorrect_Answers", [])
        
        if not question or not correct_answer or len(incorrect_answers) < 3:
            return None
        
        qa_entry = {
            "Question": question,
            "Correct_Answer": correct_answer,
            "Incorrect_Answers": incorrect_answers,
            "Type": "profile_adaptive_qa",
            "Topic": "profile_adaptive",
            "Reference": {
                'complex_question': combined_data.get('complex_question', ''),
                'ground_truth_answer': combined_data.get('ground_truth_answer', ''),
                'supporting_evidence': combined_data.get('supporting_evidence', [])
            },
            "Profile": combined_data.get('profile_data', {})
        }
        
        # 质量验证
        if apply_quality_control:
            is_valid, errors = self.quality_controller.validate_qa_entry(qa_entry)
            if not is_valid and verbose:
                print(f"Quality issues in profile-adaptive QAR: {errors}")
            return qa_entry if is_valid else None
        else:
            return qa_entry
    
    def generate_memory_application_qa(self, data: Dict[str, Any], qa_type: str, verbose: bool = False, apply_quality_control: bool = True) -> Optional[Dict[str, Any]]:
        """
        生成记忆应用型QAR（约束型、进度延续、矛盾推理、主动提醒）
        
        Args:
            data: 输入数据（已通过DataLoader.load_qar_subjective_data处理）
            qa_type: QAR类型
            verbose: 是否打印详细信息
            apply_quality_control: 是否应用质量控制
            
        Returns:
            dict: QAR条目
        """
        # 数据已经通过DataLoader处理，直接使用
        qa_pair = self.llm.generate_qa_pair(data, qa_type, verbose)
        question = qa_pair.get("Question", "")
        correct_answer = qa_pair.get("Correct_Answer", "")
        incorrect_answers = qa_pair.get("Incorrect_Answers", [])
        
        if not question or not correct_answer or len(incorrect_answers) < 3:
            return None
        
        qa_entry = {
            "Question": question,
            "Correct_Answer": correct_answer,
            "Incorrect_Answers": incorrect_answers,
            "Type": qa_type,
            "Topic": "memory_application",
            "Reference": data.get('original_data', data)  # 使用原始数据作为reference
        }
        
        # 质量验证
        if apply_quality_control:
            is_valid, errors = self.quality_controller.validate_qa_entry(qa_entry)
            if not is_valid and verbose:
                print(f"Quality issues in {qa_type} QAR: {errors}")
            return qa_entry if is_valid else None
        else:
            return qa_entry
    
    def generate_qa_by_type(self, data: Dict[str, Any], qa_type: str, verbose: bool = False, apply_quality_control: bool = True) -> Optional[Dict[str, Any]]:
        """
        根据类型生成QAR
        
        Args:
            data: 输入数据
            qa_type: QAR类型
            verbose: 是否打印详细信息
            apply_quality_control: 是否应用质量控制
            
        Returns:
            dict: QAR条目
        """
        if qa_type == 'profile_adaptive':
            return self.generate_profile_adaptive_qa(data, verbose, apply_quality_control)
        elif qa_type in ['constraint_qa', 'progress_continuation_qa', 'conflict_resolution_qa', 'active_reminder_qa']:
            return self.generate_memory_application_qa(data, qa_type, verbose, apply_quality_control)
        else:
            raise ValueError(f"Unsupported QAR type: {qa_type}")
