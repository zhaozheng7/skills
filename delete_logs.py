#!/usr/bin/env python3
"""
删除指定日期之前的旧日志文件。
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime


def parse_date_from_filename(filename):
    """从文件名中解析日期。"""
    pattern = r'\((\d{4})-(\d{2})-(\d{2})\s+(\d{2})_(\d{2})_(\d{2})\)'
    match = re.search(pattern, filename)
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        try:
            return datetime(year, month, day, hour, minute, second)
        except ValueError:
            return None
    return None


def delete_logs(folder_path, before_date, dry_run=False):
    """
    删除指定日期之前的日志文件。

    参数:
        folder_path: 文件夹路径
        before_date: 日期字符串 (YYYY-MM-DD)，该日期之前的文件将被删除
        dry_run: 预演模式，不实际删除文件

    返回: 操作结果字典
    """
    folder = Path(folder_path)

    if not folder.exists():
        return {"error": f"文件夹不存在: {folder_path}"}

    # 解析截止日期
    try:
        cutoff = datetime.fromisoformat(before_date)
    except ValueError:
        return {"error": f"无效的日期格式: {before_date}，请使用 YYYY-MM-DD 格式"}

    results = {
        "folder": str(folder.absolute()),
        "before_date": cutoff.isoformat(),
        "dry_run": dry_run,
        "total_files": 0,
        "deleted": 0,
        "skipped": 0,
        "failed": 0,
        "freed_bytes": 0,
        "files": []
    }

    # 扫描并删除文件
    for file_path in folder.glob("*.txt"):
        results["total_files"] += 1

        file_date = parse_date_from_filename(file_path.name)

        if file_date is None:
            results["skipped"] += 1
            results["files"].append({
                "name": file_path.name,
                "status": "skipped",
                "reason": "无法解析日期"
            })
            continue

        # 检查是否需要删除
        if file_date >= cutoff:
            results["skipped"] += 1
            results["files"].append({
                "name": file_path.name,
                "status": "skipped",
                "reason": "在截止日期之后",
                "date": file_date.isoformat()
            })
            continue

        # 需要删除
        file_size = file_path.stat().st_size

        try:
            if not dry_run:
                file_path.unlink()

            results["deleted"] += 1
            results["freed_bytes"] += file_size
            results["files"].append({
                "name": file_path.name,
                "status": "deleted",
                "size": file_size,
                "date": file_date.isoformat()
            })
        except Exception as e:
            results["failed"] += 1
            results["files"].append({
                "name": file_path.name,
                "status": "failed",
                "error": str(e)
            })

    # 转换字节为可读格式
    results["freed_human"] = _human_readable_size(results["freed_bytes"])

    return results


def _human_readable_size(size_bytes):
    """将字节数转换为人类可读格式。"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="删除旧日志文件")
    parser.add_argument("folder", help="文件夹路径")
    parser.add_argument("--before-date", required=True, help="截止日期 (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="预演模式，不实际删除文件")

    args = parser.parse_args()

    result = delete_logs(
        args.folder,
        args.before_date,
        dry_run=args.dry_run
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
