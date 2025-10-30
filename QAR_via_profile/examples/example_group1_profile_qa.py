#!/usr/bin/env python3
"""
示例脚本二：读取group1的multi_hop.json和profile数据生成第三类选择题并使用QAR Refresh进行质量控制
演示profile_adaptive QAR的完整处理流程
"""

import sys
import os
import json
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.qa_generator import QARGenerator
from core.qa_refresher import QARRefresher
from llm_interface import LLMInterface
from utils.data_loader import DataLoader
from prompts import get_qa_prompts


def load_group1_profile_data():
    """加载group1的reference和profile数据"""
    print("加载group1数据...")
    
    # 加载reference数据
    reference_file = "../data/reference_data/group1/multi_hop.json"
    if not os.path.exists(reference_file):
        print(f"✗ Reference文件不存在: {reference_file}")
        return None, None
    
    try:
        with open(reference_file, 'r', encoding='utf-8') as f:
            reference_data = json.load(f)
        print(f"✓ 成功加载reference数据: {os.path.basename(reference_file)}")
    except Exception as e:
        print(f"✗ 加载reference数据失败: {e}")
        return None, None
    
    # 加载profile数据
    profile_file = "../data/profile_data/group1.json"
    if not os.path.exists(profile_file):
        print(f"✗ Profile文件不存在: {profile_file}")
        return None, None
    
    try:
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        print(f"✓ 成功加载profile数据: {os.path.basename(profile_file)}")
    except Exception as e:
        print(f"✗ 加载profile数据失败: {e}")
        return None, None
    
    return reference_data, profile_data


def run_group1_profile_qa_pipeline():
    """运行group1的profile_adaptive QAR生成和QA Refresh完整流程"""
    print("="*80)
    print("Group1 Profile Adaptive QAR选择题生成与QA Refresh示例")
    print("="*80)
    
    # 1. 加载group1数据
    print("\n1. 加载group1数据...")
    reference_data, profile_data = load_group1_profile_data()
    
    if not reference_data or not profile_data:
        print("✗ 数据加载失败")
        return False
    
    # 2. 初始化处理组件
    print("\n2. 初始化处理组件...")
    try:
        llm_interface = LLMInterface()
        generator = QARGenerator()  # QARGenerator会自己创建LLM接口
        refresher = QARRefresher(llm_interface)
        print("✓ 组件初始化成功")
    except Exception as e:
        print(f"✗ 组件初始化失败: {e}")
        return False
    
    # 3. 生成profile_adaptive QAR选择题并进行Refresh
    print("\n3. 生成profile_adaptive QAR选择题并进行质量评估和刷新...")
    refresh_stats = {
        'total_generated': 0,
        'passed_first_time': 0,
        'refreshed_and_passed': 0,
        'leaked': 0,
        'generation_failed': 0
    }
    
    all_qa_entries = []
    
    try:
        # 步骤1: 生成QAR条目（不进行旧的质量检测）
        print(f"  步骤1: 生成profile_adaptive QAR选择题...")
        
        # 使用DataLoader随机选择角色并生成QAR数据
        reference_list = [reference_data] if isinstance(reference_data, dict) else reference_data
        qar_data_list = DataLoader.random_select_character_and_generate_qa(reference_list, profile_data)
        
        if not qar_data_list:
            print(f"  ✗ 生成数据失败")
            refresh_stats['generation_failed'] += 1
            return False
        
        # 使用第一个生成的数据
        qa_data = qar_data_list[0]
        
        qa_entry = generator.generate_profile_adaptive_qa(
            qa_data, 
            verbose=False,
            apply_quality_control=False  # 关键：不使用旧的质量检测
        )
        
        if not qa_entry:
            print(f"  ✗ 生成失败")
            refresh_stats['generation_failed'] += 1
            return False
        
        print(f"  ✓ 生成成功")
        print(f"    问题: {qa_entry.get('Question', 'N/A')[:60]}...")
        print(f"    角色: {qa_data['profile_data'].get('character_name', 'Unknown')}")
        refresh_stats['total_generated'] += 1
        
        # 步骤2: 获取原始prompt（用于评估和刷新）
        # 构建用于prompt的数据
        prompt_data = {
            'reference_type': reference_data.get('type', 'unknown'),
            'event_description': reference_data.get('content', {}).get('reasoning', ''),
            'key_information': reference_data.get('content', {}).get('ground_truth_answer', ''),
            'dialogue_content': [],
            'character_name': qa_data['profile_data'].get('character_name', ''),
            'character_occupation': qa_data['profile_data'].get('character_occupation', ''),
            'communication_style': qa_data['profile_data'].get('communication_style', ''),
            'domain_knowledge': qa_data['profile_data'].get('domain_knowledge', '')
        }
        
        # 提取对话内容
        supporting_evidence = reference_data.get('content', {}).get('supporting_evidence', [])
        for evidence in supporting_evidence:
            if 'content' in evidence and 'dialogue' in evidence['content']:
                prompt_data['dialogue_content'].append({
                    'character_name': evidence.get('character_name', ''),
                    'dialogue': evidence['content']['dialogue']
                })
        
        original_prompt = get_qa_prompts(prompt_data, 'profile_adaptive_qa')
        
        # 步骤3: 使用QAR Refresher进行评估和刷新
        print(f"  步骤2: 质量评估和刷新...")
        processed_qa = refresher.evaluate_and_refresh(
            qa_entry,
            'profile_adaptive_qa',
            original_prompt,
            verbose=True
        )
        
        # 更新统计
        if processed_qa.get('is_leaked', False):
            refresh_stats['leaked'] += 1
            print(f"  ✗ 标记为泄漏")
        elif processed_qa.get('refresh_count', 0) == 0:
            refresh_stats['passed_first_time'] += 1
            print(f"  ✓ 首次通过")
        else:
            refresh_stats['refreshed_and_passed'] += 1
            print(f"  ✓ 刷新后通过 (第{processed_qa['refresh_count']}次)")
        
        all_qa_entries.append(processed_qa)
        
    except Exception as e:
        print(f"  ✗ 处理错误: {e}")
        import traceback
        traceback.print_exc()
        refresh_stats['generation_failed'] += 1
        return False
    
    if not all_qa_entries:
        print("\n✗ 没有成功生成任何QAR条目")
        return False
    
    print(f"\n✓ 成功处理 {len(all_qa_entries)} 个QAR条目")
    
    # 4. 保存结果
    print(f"\n{'='*80}")
    print("4. 保存结果...")
    print(f"{'='*80}")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "../output/group1_profile_example_results"
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存QAR结果（只保存JSON）
        output_file = os.path.join(output_dir, f'group1_profile_qa_results_{timestamp}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_qa_entries, f, ensure_ascii=False, indent=2)
        print(f"✓ QAR结果已保存到: {output_file}")
        
        # 保存统计报告
        stats_report = {
            "processing_info": {
                "timestamp": timestamp,
                "input_files": ["multi_hop.json", "group1.json"],
                "qa_type": "profile_adaptive",
                "output_directory": output_dir
            },
            "refresh_stats": refresh_stats,
            "refresh_summary": {
                "total_attempted": 1,
                "total_generated": refresh_stats['total_generated'],
                "generation_failed": refresh_stats['generation_failed'],
                "passed_first_time": refresh_stats['passed_first_time'],
                "refreshed_and_passed": refresh_stats['refreshed_and_passed'],
                "leaked": refresh_stats['leaked'],
                "first_pass_rate": f"{refresh_stats['passed_first_time']/max(refresh_stats['total_generated'],1)*100:.1f}%",
                "refresh_success_rate": f"{refresh_stats['refreshed_and_passed']/max(refresh_stats['total_generated'],1)*100:.1f}%",
                "leakage_rate": f"{refresh_stats['leaked']/max(refresh_stats['total_generated'],1)*100:.1f}%"
            }
        }
        
        stats_file = os.path.join(output_dir, f'group1_profile_refresh_stats_{timestamp}.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_report, f, ensure_ascii=False, indent=2)
        print(f"✓ 统计报告已保存到: {stats_file}")
        
    except Exception as e:
        print(f"✗ 保存结果失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 显示最终统计
    print(f"\n{'='*80}")
    print("5. 最终统计")
    print(f"{'='*80}")
    print(f"总计尝试: 1")
    print(f"成功生成: {refresh_stats['total_generated']}")
    print(f"生成失败: {refresh_stats['generation_failed']}")
    print(f"首次通过: {refresh_stats['passed_first_time']} ({refresh_stats['passed_first_time']/max(refresh_stats['total_generated'],1)*100:.1f}%)")
    print(f"刷新后通过: {refresh_stats['refreshed_and_passed']} ({refresh_stats['refreshed_and_passed']/max(refresh_stats['total_generated'],1)*100:.1f}%)")
    print(f"标记为泄漏: {refresh_stats['leaked']} ({refresh_stats['leaked']/max(refresh_stats['total_generated'],1)*100:.1f}%)")
    
    print(f"\n{'='*80}")
    print("✓ Group1 Profile Adaptive QAR处理完成")
    print(f"{'='*80}")
    print(f"\n📁 输出文件:")
    print(f"  QAR结果: group1_profile_qa_results_{timestamp}.json")
    print(f"  统计报告: group1_profile_refresh_stats_{timestamp}.json")
    
    return True


if __name__ == "__main__":
    success = run_group1_profile_qa_pipeline()
    if success:
        print("\n🎉 Group1 Profile Adaptive QAR处理成功！")
    else:
        print("\n❌ Group1 Profile Adaptive QAR处理失败！")
        sys.exit(1)
