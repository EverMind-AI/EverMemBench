"""
LLM查询接口
使用OpenRouter API
"""

import json
import re
import requests
import os
from typing import Dict, Any, List, Optional
from json_repair import repair_json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import OPENROUTER_CONFIG


class LLMInterface:
    """OpenRouter API查询接口"""
    
    def __init__(self, model: str = None):
        """
        初始化LLM接口
        
        Args:
            model: 使用的模型名称（可选，默认使用配置中的模型）
        """
        # 优先使用环境变量，否则使用配置文件中的密钥
        self.api_key = os.getenv("OPENROUTER_API_KEY", OPENROUTER_CONFIG['api_key'])
        self.base_url = OPENROUTER_CONFIG['base_url']
        self.model = model or OPENROUTER_CONFIG['model']
        self.max_tokens = OPENROUTER_CONFIG['max_tokens']
        self.app_name = OPENROUTER_CONFIG['app_name']
        
        # 设置请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": OPENROUTER_CONFIG['base_url'],
            "X-Title": self.app_name,
        }
    
    def query_llm(self, data: Dict[str, Any], action: str, verbose: bool = False) -> str:
        """
        查询LLM生成QAR相关内容
        
        Args:
            data: 输入数据字典
            action: 操作类型
            verbose: 是否打印详细信息
            
        Returns:
            str: LLM的响应文本
        """
        from prompts import get_qa_prompts
        
        # 获取对应的prompt
        prompt = get_qa_prompts(data, action)
        
        if verbose:
            print(f"Action: {action}")
            print(f"Prompt: {prompt[:200]}...")
        
        try:
            return self._query_openrouter(prompt, verbose)
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return ""
    
    def _query_openrouter(self, prompt: str, verbose: bool = False) -> str:
        """使用OpenRouter API查询"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that generates high-quality QAR (Question-Answer-Reasoning) content for evaluating LLM personalization capabilities."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
    
    def process_json_response(self, response: str) -> Dict[str, Any]:
        """
        处理LLM返回的JSON响应
        
        Args:
            response: LLM的原始响应
            
        Returns:
            dict: 解析后的JSON数据
        """
        try:
            # 尝试直接解析JSON
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                # 使用json_repair修复JSON
                repaired_json = repair_json(response)
                return json.loads(repaired_json)
            except Exception as e:
                print(f"Error processing JSON response: {e}")
                return {}
    
    def extract_python_list(self, response: str) -> List[str]:
        """
        从LLM响应中提取Python列表
        
        Args:
            response: LLM的原始响应
            
        Returns:
            list: 提取的Python列表
        """
        try:
            # 查找代码块
            match = re.search(r"```python\n(.*?)\n```", response, re.DOTALL)
            if match:
                code_block = match.group(1)
            else:
                code_block = response.strip("```").strip()
            
            # 清理代码块
            code_block = code_block.replace('\n', '').strip()
            
            # 尝试解析为JSON
            try:
                return json.loads(code_block)
            except:
                # 如果JSON解析失败，尝试使用ast.literal_eval
                import ast
                return ast.literal_eval(code_block)
                
        except Exception as e:
            print(f"Error extracting Python list: {e}")
            return []
    
    def generate_qa_pair(self, data: Dict[str, Any], action: str, verbose: bool = False) -> Dict[str, Any]:
        """
        生成问答对
        
        Args:
            data: 输入数据
            action: 操作类型
            verbose: 是否打印详细信息
            
        Returns:
            dict: 包含问题和答案的字典
        """
        response = self.query_llm(data, action, verbose)
        return self.process_json_response(response)
    
    def generate_incorrect_options(self, data: Dict[str, Any], action: str, verbose: bool = False) -> List[str]:
        """
        生成错误选项
        
        Args:
            data: 输入数据
            action: 操作类型
            verbose: 是否打印详细信息
            
        Returns:
            list: 错误选项列表
        """
        response = self.query_llm(data, action, verbose)
        return self.extract_python_list(response)
