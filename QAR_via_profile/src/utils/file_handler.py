"""
文件处理工具
处理输入输出文件操作
"""

import json
import csv
import os
from typing import List, Dict, Any


class FileHandler:
    """文件处理器"""
    
    @staticmethod
    def save_results(formatted_entries: List[Dict[str, Any]], 
                    output_dir: str, 
                    base_name: str = "qar_results") -> Dict[str, str]:
        """
        保存结果到文件
        
        Args:
            formatted_entries: 格式化后的选择题列表
            output_dir: 输出目录
            base_name: 基础文件名
            
        Returns:
            dict: 保存的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存JSON格式
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_entries, f, ensure_ascii=False, indent=2)
        
        # 保存CSV格式
        csv_path = os.path.join(output_dir, f"{base_name}.csv")
        FileHandler._save_to_csv(formatted_entries, csv_path)
        
        return {
            'json_path': json_path,
            'csv_path': csv_path
        }
    
    @staticmethod
    def _save_to_csv(formatted_entries: List[Dict[str, Any]], csv_path: str):
        """
        保存到CSV文件
        
        Args:
            formatted_entries: 格式化后的选择题列表
            csv_path: CSV文件路径
        """
        if not formatted_entries:
            return
        
        # 获取所有字段名
        fieldnames = list(formatted_entries[0].keys())
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(formatted_entries)
    
    @staticmethod
    def create_output_directory(output_dir: str) -> str:
        """
        创建输出目录
        
        Args:
            output_dir: 输出目录路径
            
        Returns:
            str: 创建的目录路径
        """
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    @staticmethod
    def backup_existing_file(file_path: str) -> str:
        """
        备份现有文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 备份文件路径
        """
        if not os.path.exists(file_path):
            return file_path
        
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        
        return backup_path
