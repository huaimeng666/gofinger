import json
from pathlib import Path
import logging
from collections import defaultdict
import argparse
import datetime
import re

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'deduplicate_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def load_json(file_path):
    """读取 JSON 文件并返回内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"读取文件 {file_path} 失败: {e}")
        return None

def save_json(data, output_file):
    """将数据保存为 JSON 文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"数据已保存到 {output_file}")
    except IOError as e:
        logging.error(f"保存文件 {output_file} 失败: {e}")

def is_chinese_cms(cms):
    """判断 CMS 是否包含中文字符"""
    return bool(cms and any(0x4E00 <= ord(c) <= 0x9FFF for c in cms))

def generate_fingerprint_key(fingerprint):
    """生成指纹的唯一键，基于 method、location 和 keyword"""
    try:
        key_parts = [
            fingerprint.get('method', ''),
            fingerprint.get('location', ''),
            tuple(sorted(fingerprint.get('keyword', []) or []))
        ]
        return tuple(key_parts)
    except (AttributeError, TypeError) as e:
        logging.warning(f"无效指纹结构，跳过: {fingerprint}, 错误: {e}")
        return None

def deduplicate_fingerprints(input_file, output_file):
    """去重指纹文件，基于 method、location、keyword，优先保留中文 CMS"""
    # 读取输入文件
    data = load_json(input_file)
    if data is None:
        return

    fingerprints = data.get('fingerprint', [])
    if not fingerprints:
        logging.error("文件不包含 fingerprint 数组")
        return

    unique_fingerprints = []
    seen_fingerprints = {}  # key: (method, location, keyword), value: {is_chinese: fingerprint}
    cms_counts = defaultdict(int)
    removed_fingerprints = []

    for index, fingerprint in enumerate(fingerprints):
        fingerprint_key = generate_fingerprint_key(fingerprint)
        if fingerprint_key is None:
            continue

        cms = fingerprint.get('cms', '')
        is_chinese = is_chinese_cms(cms)

        if fingerprint_key in seen_fingerprints:
            existing_fingerprint = seen_fingerprints[fingerprint_key]
            existing_is_chinese = is_chinese_cms(existing_fingerprint.get('cms', ''))

            # 如果已有指纹是中文，且当前不是中文，跳过当前指纹
            if existing_is_chinese and not is_chinese:
                removed_fingerprints.append({"index": index, "fingerprint": fingerprint})
                continue
            # 如果当前是中文，替换现有指纹（无论现有是否中文）
            elif is_chinese:
                removed_fingerprints.append({
                    "index": unique_fingerprints.index(existing_fingerprint),
                    "fingerprint": existing_fingerprint
                })
                unique_fingerprints[unique_fingerprints.index(existing_fingerprint)] = fingerprint
                seen_fingerprints[fingerprint_key] = fingerprint
                cms_counts[existing_fingerprint.get('cms', '未知')] -= 1
                cms_counts[cms] += 1
            # 如果两者都不是中文，且 CMS 不同，记录为重复
            else:
                removed_fingerprints.append({"index": index, "fingerprint": fingerprint})
                continue
        else:
            # 新指纹，直接保留
            seen_fingerprints[fingerprint_key] = fingerprint
            unique_fingerprints.append(fingerprint)
            cms_counts[cms] += 1

    # 创建新 JSON 结构
    new_data = {'fingerprint': unique_fingerprints}

    # 保存去重后的文件
    save_json(new_data, output_file)

    # 输出去重报告
    num_removed = len(fingerprints) - len(unique_fingerprints)
    logging.info(f"共处理 {len(fingerprints)} 个指纹，移除 {num_removed} 个重复指纹")
    logging.info(f"去重后剩余 {len(unique_fingerprints)} 个唯一指纹")
    
    # 按 CMS 统计
    logging.info("\n=== 去重后 CMS 分布 ===")
    for cms, count in sorted(cms_counts.items()):
        logging.info(f"  {cms}: {count} 个指纹")

    # 输出移除的重复指纹
    if removed_fingerprints:
        logging.info("\n=== 移除的重复指纹 ===")
        for removed in removed_fingerprints:
            logging.info(f"  索引 {removed['index']}: {json.dumps(removed['fingerprint'], ensure_ascii=False, indent=2)}")

    # 保存去重报告
    report = {
        "metadata": {
            "input_file": str(input_file),
            "output_file": str(output_file),
            "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_fingerprints": len(fingerprints),
            "unique_fingerprints": len(unique_fingerprints),
            "removed_fingerprints": num_removed
        },
        "cms_distribution": dict(cms_counts),
        "removed_fingerprints": removed_fingerprints
    }
    report_file = output_file.with_name(f"{output_file.stem}_report.json")
    save_json(report, report_file)

if __name__ == "__main__":
    # 使用命令行参数支持灵活输入
    parser = argparse.ArgumentParser(description="去重 JSON 文件中的指纹，基于 method、location、keyword，优先保留中文 CMS")
    script_dir = Path(__file__).parent
    parser.add_argument('--input', default=script_dir / "finger.json", help="输入 JSON 文件路径")
    parser.add_argument('--output', default=script_dir / "finger_unique.json", help="输出去重后的 JSON 文件路径")
    args = parser.parse_args()

    deduplicate_fingerprints(Path(args.input), Path(args.output))