"""
数据加载工具
处理各种格式的输入数据
"""

import json
import os
from typing import List, Dict, Any, Optional


class DataLoader:
    """数据加载器"""
    
    @staticmethod
    def load_key_info(file_path: str) -> List[Dict[str, Any]]:
        """
        加载关键信息文件
        
        Args:
            file_path: 关键信息文件路径
            
        Returns:
            list: 关键信息列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file {file_path} does not exist")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    return json.load(f)
                else:
                    # 假设是JSONL格式
                    data = []
                    for line in f:
                        if line.strip():
                            data.append(json.loads(line.strip()))
                    return data
        except Exception as e:
            raise ValueError(f"Error loading key info file: {e}")
    
    @staticmethod
    def validate_key_info(key_info: Dict[str, Any], qa_type: str) -> bool:
        """
        验证关键信息是否包含所需字段
        
        Args:
            key_info: 关键信息字典
            qa_type: QAR类型
            
        Returns:
            bool: 是否有效
        """
        required_fields = {
            'profile_adaptive': ['complex_question', 'ground_truth_answer', 'supporting_evidence', 'profile_data'],
            'constraint_qa': ['complex_question', 'ground_truth_answer', 'supporting_evidence'],
            'progress_continuation_qa': ['complex_question', 'ground_truth_answer', 'supporting_evidence'],
            'conflict_resolution_qa': ['complex_question', 'ground_truth_answer', 'supporting_evidence'],
            'active_reminder_qa': ['complex_question', 'ground_truth_answer', 'supporting_evidence']
        }
        
        if qa_type not in required_fields:
            return False
        
        for field in required_fields[qa_type]:
            if field not in key_info or not key_info[field]:
                return False
        
        return True
    
    @staticmethod
    def load_reference_data(file_path: str) -> List[Dict[str, Any]]:
        """
        加载Reference数据文件
        
        Args:
            file_path: Reference数据文件路径
            
        Returns:
            list: Reference数据列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Reference file {file_path} does not exist")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                    # 如果是单个对象，转换为列表
                    if isinstance(data, dict):
                        return [data]
                    elif isinstance(data, list):
                        return data
                    else:
                        raise ValueError(f"Unexpected data format in {file_path}")
                else:
                    # 假设是JSONL格式
                    data = []
                    for line in f:
                        if line.strip():
                            data.append(json.loads(line.strip()))
                    return data
        except Exception as e:
            raise ValueError(f"Error loading reference file: {e}")
    
    @staticmethod
    def load_profile_data(file_path: str) -> Dict[str, Any]:
        """
        加载Profile数据文件
        
        Args:
            file_path: Profile数据文件路径
            
        Returns:
            dict: Profile数据字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Profile file {file_path} does not exist")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading profile file: {e}")
    
    @staticmethod
    def match_character_to_profile(character_name: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据角色名称匹配对应的Profile
        
        Args:
            character_name: 角色名称
            profile_data: Profile数据
            
        Returns:
            dict: 匹配的Profile信息
        """
        if 'profiles' not in profile_data:
            return {}
        
        for profile in profile_data['profiles']:
            if profile.get('identity_layer', {}).get('name') == character_name:
                return profile
        
        return {}
    
    @staticmethod
    def combine_reference_profile(reference_data: List[Dict], profile_data: Dict) -> List[Dict]:
        """
        组合Reference和Profile数据
        
        Args:
            reference_data: Reference数据列表
            profile_data: Profile数据字典
            
        Returns:
            list: 组合后的数据列表
        """
        combined_data = []
        
        for ref_item in reference_data:
            # 从supporting_evidence中提取角色名称
            character_names = []
            if 'content' in ref_item and 'supporting_evidence' in ref_item['content']:
                for evidence in ref_item['content']['supporting_evidence']:
                    if 'character_name' in evidence:
                        character_names.append(evidence['character_name'])
            
            # 为每个角色匹配Profile
            matched_profiles = {}
            for char_name in character_names:
                profile = DataLoader.match_character_to_profile(char_name, profile_data)
                if profile:
                    matched_profiles[char_name] = profile
            
            # 组合数据
            combined_item = {
                'reference_data': ref_item,
                'profile_data': matched_profiles,
                'character_names': character_names
            }
            combined_data.append(combined_item)
        
        return combined_data
    
    @staticmethod
    def random_select_character_and_generate_qa(reference_data: List[Dict], profile_data: Dict) -> List[Dict]:
        """
        随机选择角色并生成Profile-adaptive QAR数据
        
        Args:
            reference_data: Reference数据列表
            profile_data: Profile数据字典
            
        Returns:
            list: 生成的QAR数据列表
        """
        import random
        
        qar_data_list = []
        
        for ref_item in reference_data:
            # 从supporting_evidence中提取所有角色名称
            character_names = []
            if 'content' in ref_item and 'supporting_evidence' in ref_item['content']:
                for evidence in ref_item['content']['supporting_evidence']:
                    if 'character_name' in evidence:
                        character_names.append(evidence['character_name'])
            
            # 随机选择一个角色
            if character_names:
                selected_character = random.choice(character_names)
                selected_profile = DataLoader.match_character_to_profile(selected_character, profile_data)
                
                if selected_profile:
                    # 结构化Reference数据
                    structured_ref = DataLoader._structure_reference_data(ref_item)
                    
                    # 结构化Profile数据
                    structured_profile = DataLoader._structure_profile_data(selected_character, selected_profile)
                    
                    # 组合生成QAR数据，符合profile_adaptive类型的要求
                    qar_data = {
                        'complex_question': ref_item['content']['complex_question'],
                        'ground_truth_answer': ref_item['content']['ground_truth_answer'],
                        'supporting_evidence': ref_item['content']['supporting_evidence'],
                        'profile_data': structured_profile
                    }
                    
                    qar_data_list.append(qar_data)
        
        return qar_data_list
    
    @staticmethod
    def _structure_reference_data(reference_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        结构化Reference数据
        
        Args:
            reference_item: Reference数据项
            
        Returns:
            dict: 结构化的Reference数据
        """
        content = reference_item.get('content', {})
        
        # 提取事件类型
        reference_type = reference_item.get('type', 'unknown')
        
        # 提取事件描述
        event_description = content.get('reasoning', '')
        
        # 提取关键信息
        key_information = content.get('ground_truth_answer', '')
        
        # 提取对话内容
        dialogue_content = []
        if 'supporting_evidence' in content:
            for evidence in content['supporting_evidence']:
                if 'content' in evidence and 'dialogue' in evidence['content']:
                    dialogue_content.append({
                        'character': evidence.get('character_name', ''),
                        'dialogue': evidence['content']['dialogue']
                    })
        
        return {
            'reference_type': reference_type,
            'event_description': event_description,
            'key_information': key_information,
            'dialogue_content': dialogue_content
        }
    
    @staticmethod
    def _structure_profile_data(character_name: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        结构化Profile数据
        
        Args:
            character_name: 角色名称
            profile: Profile数据
            
        Returns:
            dict: 结构化的Profile数据
        """
        identity = profile.get('identity_layer', {})
        behavioral = profile.get('behavioral_patterns', {})
        knowledge = profile.get('knowledge_and_beliefs', {})
        
        # 格式化沟通风格
        comm_style = behavioral.get('communication_style', {})
        communication_style = f"正式程度: {comm_style.get('formality', '未知')}, " \
                             f"话多程度: {comm_style.get('verbosity', '未知')}, " \
                             f"幽默感: {comm_style.get('humor', '未知')}, " \
                             f"专业术语使用: {comm_style.get('jargon_usage', '未知')}, " \
                             f"口语使用: {comm_style.get('casual_language_usage', '未知')}"
        
        return {
            'character_name': character_name,
            'character_occupation': identity.get('occupation', '未知'),
            'communication_style': communication_style,
            'domain_knowledge': ', '.join(knowledge.get('domain_knowledge', []))
        }
    
    @staticmethod
    def filter_valid_key_info(key_info_list: List[Dict[str, Any]], 
                            qa_types: List[str]) -> List[Dict[str, Any]]:
        """
        过滤出有效的关键信息
        
        Args:
            key_info_list: 关键信息列表
            qa_types: QAR类型列表
            
        Returns:
            list: 有效的关键信息列表
        """
        valid_entries = []
        
        for key_info in key_info_list:
            for qa_type in qa_types:
                if DataLoader.validate_key_info(key_info, qa_type):
                    valid_entries.append(key_info)
                    break  # 只要满足一种类型就足够了
        
        return valid_entries
    
    @staticmethod
    def load_qar_subjective_data(file_path: str) -> List[Dict[str, Any]]:
        """
        加载QAR主观题数据文件（group3格式）
        
        Args:
            file_path: QAR主观题数据文件路径
            
        Returns:
            list: 处理后的QAR数据列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"QAR subjective file {file_path} does not exist")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果数据是单个对象，转换为列表
            if isinstance(data, dict):
                data = [data]
            
            # 处理每个QAR条目，提取content中的信息
            processed_data = []
            for item in data:
                if 'content' in item:
                    content = item['content']
                    processed_item = {
                        'reasoning': content.get('reasoning', ''),
                        'complex_question': content.get('complex_question', ''),
                        'ground_truth_answer': content.get('ground_truth_answer', ''),
                        'supporting_evidence': content.get('supporting_evidence', []),
                        'evaluation_type': content.get('evaluation_type', ''),
                        'original_data': item  # 保留原始数据用于reference
                    }
                    processed_data.append(processed_item)
                else:
                    # 如果数据直接包含QAR字段，直接使用
                    processed_data.append(item)
            
            return processed_data
        except Exception as e:
            raise ValueError(f"Error loading QAR subjective data: {e}")
    
    @staticmethod
    def load_qar_subjective_batch(file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        批量加载多个QAR主观题数据文件
        
        Args:
            file_paths: QAR主观题数据文件路径列表
            
        Returns:
            list: 合并后的QAR数据列表
        """
        all_data = []
        for file_path in file_paths:
            try:
                data = DataLoader.load_qar_subjective_data(file_path)
                all_data.extend(data)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")
                continue
        return all_data