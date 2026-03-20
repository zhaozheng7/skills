#!/usr/bin/env python3
"""
扫描日志文件夹并解析文件名中的日期信息。
支持的格式：环境名称(YYYY-MM-DD HH_MM_SS).txt
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime


def parse_date_from_filename(filename):
    """
    从文件名中解析日期。
    支持格式：环境名称(YYYY-MM-DD HH_MM_SS).txt

    返回：datetime 对象或 None
    """
    # 匹配 (YYYY-MM-DD HH_MM_SS) 格式
    pattern = r'\((\d{4})-(\d{2})-(\d{2})\s+(\d{2})_(\d{2})_(\d{2})\)'
    match = re.search(pattern, filename)

    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        try:
            return datetime(year, month, day, hour, minute, second)
        except ValueError:
            return None
    return None


def scan_folder(folder_path):
    """
    扫描文件夹，解析所有日志文件的日期信息。

    返回包含扫描结果的字典
    """
    folder = Path(folder_path)

    if not folder.exists():
        return {"error": f"文件夹不存在: {folder_path}"}

    if not folder.is_dir():
        return {"error": f"路径不是文件夹: {folder_path}"}

    results = {
        "folder": str(folder.absolute()),
        "total_files": 0,
        "parsed_files": 0,
        "unparsed_files": 0,
        "files": [],
        "unparsed": [],
        "date_range": None
    }

    dates = []

    # 扫描所有 .txt 文件
    for file_path in folder.glob("*.txt"):
        results["total_files"] += 1

        date = parse_date_from_filename(file_path.name)

        if date:
            results["parsed_files"] += 1
            results["files"].append({
                "name": file_path.name,
                "path": str(file_path),
                "date": date.isoformat(),
                "size": file_path.stat().st_size
            })
            dates.append(date)
        else:
            results["unparsed_files"] += 1
            results["unparsed"].append(file_path.name)

    # 计算日期范围
    if dates:
        dates.sort()
        results["date_range"] = {
            "earliest": dates[0].isoformat(),
            "latest": dates[-1].isoformat()
        }

    # 按日期排序文件列表
    results["files"].sort(key=lambda x: x["date"])

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="扫描日志文件夹并解析日期")
    parser.add_argument("folder", help="要扫描的文件夹路径")

    args = parser.parse_args()

    result = scan_folder(args.folder)

    # JSON 格式输出
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
