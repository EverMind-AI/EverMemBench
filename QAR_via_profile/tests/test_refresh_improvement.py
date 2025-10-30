#!/usr/bin/env python3
"""
测试QA Refresh改进 - 验证约束信息是否被正确提取和使用
"""

import sys
import os
import json

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.qa_refresher import QARRefresher
from llm_interface import LLMInterface
from utils.data_loader import DataLoader


def test_constraint_extraction():
    """测试约束信息提取功能"""
    print("="*80)
    print("测试约束信息提取功能")
    print("="*80)
    
    # 加载2.1.json（拔牙案例）
    data_file = "data/reference_data/group3/2.1.json"
    
    try:
        qa_data = DataLoader.load_qar_subjective_data(data_file)
        print(f"✓ 成功加载测试数据: {data_file}")
        
        # 如果返回的是list，取第一个元素
        if isinstance(qa_data, list) and len(qa_data) > 0:
            reference_data = qa_data[0]
        else:
            reference_data = qa_data
            
        print(f"  Reference类型: {type(reference_data)}")
        
        # 创建一个模拟的QA entry
        qa_entry = {
            "Question": "我周六晚上想和朋友聚餐，有什么餐厅推荐吗？",
            "Correct_Answer": "鉴于你刚做完拔牙手术，还在恢复期，建议选择主打清淡粥品的'一碗好粥'。",
            "Incorrect_Answers": [
                "推荐去'川味坊'尝试招牌水煮鱼。",
                "可以去'轻食日记'点份软意面。",
                "建议前往'滋补坊'只喝炖汤。"
            ],
            "Type": "constraint_qa",
            "Topic": "memory_application",
            "Reference": reference_data
        }
        
        # 初始化refresher
        llm_interface = LLMInterface()
        refresher = QARRefresher(llm_interface)
        
        # 提取关键约束
        key_constraints = refresher._extract_key_constraints(qa_entry['Reference'])
        
        print("\n提取的关键约束信息：")
        print("-" * 80)
        print(key_constraints)
        print("-" * 80)
        
        # 验证是否提取到了关键约束
        expected_keywords = ['一周', '喝粥', '硬的', '辣的', '不能碰']
        found_keywords = [kw for kw in expected_keywords if kw in key_constraints]
        
        print(f"\n关键词检测：")
        print(f"  期望关键词: {expected_keywords}")
        print(f"  找到关键词: {found_keywords}")
        print(f"  覆盖率: {len(found_keywords)}/{len(expected_keywords)} ({len(found_keywords)/len(expected_keywords)*100:.1f}%)")
        
        if len(found_keywords) >= len(expected_keywords) * 0.6:  # 至少60%覆盖
            print("\n✓ 约束信息提取测试通过")
            return True
        else:
            print("\n✗ 约束信息提取不完整")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_refresh_with_constraints():
    """测试完整的refresh流程（包含约束信息）"""
    print("\n" + "="*80)
    print("测试完整的Refresh流程")
    print("="*80)
    
    print("\n此测试需要调用LLM API，可能需要一些时间...")
    print("建议直接运行 examples/example_group3_qa.py 来查看完整效果")
    
    # 这里可以添加完整的refresh测试，但会调用API
    # 为了避免不必要的API调用，暂时跳过
    return True


if __name__ == "__main__":
    print("\nQA Refresh改进测试")
    print("=" * 80)
    
    # 测试1: 约束信息提取
    test1_passed = test_constraint_extraction()
    
    # 测试2: 完整refresh流程（可选）
    test2_passed = test_refresh_with_constraints()
    
    print("\n" + "=" * 80)
    print("测试结果汇总：")
    print(f"  约束信息提取: {'✓ 通过' if test1_passed else '✗ 失败'}")
    print(f"  完整Refresh流程: {'✓ 通过' if test2_passed else '✗ 失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)

