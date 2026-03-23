#!/usr/bin/env python3
"""
归档旧日志文件到指定文件夹（扁平化存放）。
"""

import os
import re
import json
import shutil
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


def archive_logs(source_folder, archive_folder, before_date, on_conflict="skip", dry_run=False):
    """
    归档指定日期之前的日志文件。

    参数:
        source_folder: 源文件夹路径
        archive_folder: 归档文件夹路径
        before_date: 日期字符串 (YYYY-MM-DD)，该日期之前的文件将被归档
        on_conflict: 冲突处理方式 - "skip"(跳过), "overwrite"(覆盖), "rename"(重命名)
        dry_run: 预演模式，不实际移动文件

    返回: 操作结果字典
    """
    source = Path(source_folder)
    archive = Path(archive_folder)

    if not source.exists():
        return {"error": f"源文件夹不存在: {source_folder}"}

    # 解析截止日期
    try:
        cutoff = datetime.fromisoformat(before_date)
    except ValueError:
        return {"error": f"无效的日期格式: {before_date}，请使用 YYYY-MM-DD 格式"}

    # 创建归档文件夹
    if not dry_run:
        archive.mkdir(parents=True, exist_ok=True)

    results = {
        "source": str(source.absolute()),
        "archive": str(archive.absolute()),
        "before_date": cutoff.isoformat(),
        "dry_run": dry_run,
        "total_files": 0,
        "archived": 0,
        "skipped": 0,
        "failed": 0,
        "files": [],
        "conflicts": []
    }

    # 扫描并归档文件
    for file_path in source.glob("*.txt"):
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

        # 检查是否需要归档
        if file_date >= cutoff:
            results["skipped"] += 1
            results["files"].append({
                "name": file_path.name,
                "status": "skipped",
                "reason": "在截止日期之后"
            })
            continue

        # 需要归档
        dest_path = archive / file_path.name

        # 检查冲突
        if dest_path.exists():
            if on_conflict == "skip":
                results["skipped"] += 1
                results["conflicts"].append(file_path.name)
                results["files"].append({
                    "name": file_path.name,
                    "status": "skipped",
                    "reason": "目标文件已存在"
                })
                continue
            elif on_conflict == "rename":
                # 添加后缀
                base = dest_path.stem
                ext = dest_path.suffix
                counter = 1
                while dest_path.exists():
                    dest_path = archive / f"{base}_{counter}{ext}"
                    counter += 1
            # overwrite 不需要特殊处理

        # 执行移动
        try:
            if not dry_run:
                shutil.move(str(file_path), str(dest_path))
            else:
                dest_path = f"[DRY RUN] {dest_path}"

            results["archived"] += 1
            results["files"].append({
                "name": file_path.name,
                "status": "archived",
                "destination": str(dest_path),
                "date": file_date.isoformat()
            })
        except Exception as e:
            results["failed"] += 1
            results["files"].append({
                "name": file_path.name,
                "status": "failed",
                "error": str(e)
            })

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="归档旧日志文件")
    parser.add_argument("source", help="源文件夹路径")
    parser.add_argument("archive", help="归档文件夹路径")
    parser.add_argument("--before-date", required=True, help="截止日期 (YYYY-MM-DD)")
    parser.add_argument("--on-conflict", default="skip",
                        choices=["skip", "overwrite", "rename"],
                        help="当目标文件已存在时的处理方式")
    parser.add_argument("--dry-run", action="store_true", help="预演模式，不实际移动文件")

    args = parser.parse_args()

    result = archive_logs(
        args.source,
        args.archive,
        args.before_date,
        on_conflict=args.on_conflict,
        dry_run=args.dry_run
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
