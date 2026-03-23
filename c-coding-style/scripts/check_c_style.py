#!/usr/bin/env python3
"""
C代码风格检查脚本
检查C代码是否符合华为编码规范
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class StyleIssue:
    """风格问题"""
    line: int
    column: int
    severity: str  # error, warning
    rule: str
    message: str


@dataclass
class FileResult:
    """文件检查结果"""
    path: str
    issues: List[StyleIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


class CStyleChecker:
    """C代码风格检查器"""

    def __init__(self):
        self.issues: List[StyleIssue] = []
        self.current_file = ""

        # 函数匹配模式（常见C函数定义模式）
        self.function_patterns = [
            # 返回类型 + 函数名 + 参数
            r'^\s*(?:static\s+)?(?:inline\s+)?(?:const\s+)?(?:unsigned\s+)?(?:signed\s+)?'
            r'(?:struct\s+)?(?:enum\s+)?(?:\w+\s+\*?\s*)+(\w+)\s*\([^*]*\)',
            # 函数名直接开始（构造函数风格）
            r'^\s*(\w+)\s*\([^)]*\)\s*$',
        ]

        # 函数调用模式
        self.function_call_pattern = r'(\w+)\s*\('

    def check_file(self, filepath: Path) -> FileResult:
        """检查单个文件"""
        self.issues = []
        self.current_file = str(filepath)

        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
        except Exception as e:
            return FileResult(path=str(filepath), issues=[
                StyleIssue(0, 0, "error", "file_read", f"无法读取文件: {e}")
            ])

        # 检查文件头版权声明
        self._check_file_header(lines)

        # 逐行检查
        for i, line in enumerate(lines, 1):
            self._check_line(i, line, lines)

        # 检查函数大括号
        self._check_function_braces(lines)

        # 检查命名规范
        self._check_naming(lines)

        return FileResult(path=str(filepath), issues=self.issues)

    def _check_file_header(self, lines: List[str]) -> None:
        """检查文件头版权声明"""
        if len(lines) < 5:
            return

        header = '\n'.join(lines[:10])
        if 'Copyright (c) Huawei Technologies Co., Ltd. 2026' not in header:
            self.issues.append(StyleIssue(
                1, 0, "warning", "file_header",
                "文件头缺少版权声明: Copyright (c) Huawei Technologies Co., Ltd. 2026. All rights reserved."
            ))

    def _check_line(self, num: int, line: str, all_lines: List[str]) -> None:
        """检查单行代码"""
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # 1. 检查行宽
        if len(line) > 80:
            self.issues.append(StyleIssue(
                num, 81, "warning", "line_width",
                f"行宽超过80字符 (当前: {len(line)})"
            ))

        # 2. 检查行末空格
        if line != line.rstrip():
            self.issues.append(StyleIssue(
                num, len(line.rstrip()) + 1, "warning", "trailing_spaces",
                "行末有空格"
            ))

        # 3. 检查缩进（应使用Tab）
        if indent > 0 and line[:indent].count(' ') == indent:
            # 使用空格缩进，检查是否应该是Tab
            # 排除预处理指令（通常在行首）
            if not stripped.startswith('#'):
                self.issues.append(StyleIssue(
                    num, 1, "warning", "indentation",
                    "应使用Tab缩进，而非空格"
                ))

        # 4. 检查注释格式
        if '//' in line:
            self.issues.append(StyleIssue(
                num, line.index('//') + 1, "warning", "comment_style",
                "应使用 /* */ 注释风格，而非 //"
            ))

        # 检查注释符后是否有空格
        if '/*' in line and '*/' in line:
            comment_match = re.search(r'/\*\S', line)
            if comment_match:
                self.issues.append(StyleIssue(
                    num, comment_match.start() + 1, "warning", "comment_spacing",
                    "注释符 /* 后应有空格"
                ))
            # 检查 */ 前是否有空格
            end_match = re.search(r'\S\*/', line)
            if end_match:
                self.issues.append(StyleIssue(
                    num, end_match.start() + 1, "warning", "comment_spacing",
                    "*/ 前应有空格"
                ))

        # 5. 检查大括号位置
        # 函数左大括号应另起一行
        # 匹配函数定义行，且行末有{
        if (re.search(r'\w+\s*\([^)]*\)\s*(?:const\s*)?\{', stripped) and
                not stripped.startswith('typedef')):
            self.issues.append(StyleIssue(
                num, line.rfind('{') + 1, "error", "brace_style",
                "函数左大括号应另起一行，放在行首"
            ))

        # 6. 检查关键字后的空格
        keywords_after_space = ['if', 'while', 'for', 'switch', 'return', 'sizeof']
        for kw in keywords_after_space:
            # 匹配关键字后直接跟(或没有空格的情况
            pattern = rf'\b{kw}\s*\('
            match = re.search(pattern, line)
            if match and match.group(0).strip() != match.group(0):
                # 有空格，检查是否正确
                if re.search(rf'\b{kw}\s*\(', line):
                    pass  # 正确
            else:
                # 检查是否直接跟(
                if re.search(rf'\b{kw}\(', line):
                    self.issues.append(StyleIssue(
                        num, match.start() + 1, "warning", "keyword_spacing",
                        f"关键字 '{kw}' 后应加空格"
                    ))

        # 7. 检查小括号内部不应有空格
        # 赋值、函数调用、if/while条件中的括号
        paren_pairs = re.finditer(r'\([^)]+\)', line)
        for match in paren_pairs:
            inner = match.group()[1:-1]
            if inner.startswith(' ') or inner.endswith(' '):
                # 排除某些合法情况（如字符串字面量）
                if '"' not in inner or inner.count('"') % 2 == 0:
                    self.issues.append(StyleIssue(
                        num, match.start() + 1, "info", "paren_spacing",
                        "小括号内部两侧不应加空格"
                    ))

    def _check_function_braces(self, lines: List[str]) -> None:
        """检查函数大括号风格"""
        in_function_def = False
        brace_line = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # 检测函数定义（简化版）
            if re.match(r'^[\w\s\*]+(\w+)\s*\([^)]*\)\s*$', stripped):
                in_function_def = True
                brace_line = i + 1
                continue

            if in_function_def:
                if stripped == '{':
                    # 正确：函数左大括号另起一行
                    if not line.startswith('\t') and not line.startswith(' '):
                        pass  # 正确
                elif stripped.startswith('{'):
                    # 错误：左大括号不应跟随在同一行（对于函数）
                    self.issues.append(StyleIssue(
                        i, 1, "error", "function_brace",
                        "函数左大括号应另起一行，位于行首"
                    ))
                in_function_def = False

    def _check_naming(self, lines: List[str]) -> None:
        """检查命名规范"""
        # 收集所有标识符及其上下文
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # 跳过注释和预处理
            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                continue
            if stripped.startswith('#'):
                continue

            # 检查全局变量声明（在文件/作用域顶层）
            # 简化判断：行首是类型名 + 变量名
            global_var_pattern = r'^\s*(?:static\s+)?(?:const\s+)?(?:unsigned\s+)?(?:signed\s+)?(?:struct\s+)?(?:\w+\s+)+(\*?\s*)(\w+)\s*[;=]'
            match = re.match(global_var_pattern, line)
            if match:
                var_name = match.group(2)
                # 排除函数定义（有括号）
                if '(' not in line:
                    if not var_name.startswith('g'):
                        self.issues.append(StyleIssue(
                            i, 1, "error", "global_var_naming",
                            f"全局变量 '{var_name}' 应使用 'g' 前缀的小驼峰命名 (如: g{var_name[0].upper()}{var_name[1:]})"
                        ))
                    elif not self._is_camel_case(var_name[1:]):  # 去掉g前缀检查
                        self.issues.append(StyleIssue(
                            i, 1, "error", "global_var_naming",
                            f"全局变量 '{var_name}' 应使用小驼峰命名 (去掉g前缀后)"
                        ))

            # 检查宏定义
            define_pattern = r'^#define\s+(\w+)\s+'
            match = re.match(define_pattern, stripped)
            if match:
                macro_name = match.group(1)
                if '(' in macro_name:
                    # 函数式宏，去掉括号部分
                    macro_base = macro_name.split('(')[0]
                    # 检查是否全大写或大驼峰
                    if not (macro_base.isupper() or self._is_pascal_case(macro_base)):
                        self.issues.append(StyleIssue(
                            i, 1, "warning", "macro_naming",
                            f"函数式宏 '{macro_base}' 应使用全大写下划线或大驼峰命名"
                        ))
                else:
                    # 普通宏，应全大写
                    if not macro_name.isupper():
                        self.issues.append(StyleIssue(
                            i, 1, "error", "macro_naming",
                            f"宏 '{macro_name}' 应使用全大写下划线命名"
                        ))

            # 检查枚举值
            if 'enum' in stripped:
                # 检查后续几行的枚举值
                for j in range(i, min(i + 20, len(lines))):
                    enum_line = lines[j].strip()
                    if enum_line == '}' or enum_line.startswith(';'):
                        break
                    enum_match = re.match(r'^(\w+)\s*[,\=]', enum_line)
                    if enum_match:
                        enum_val = enum_match.group(1)
                        if not enum_val.isupper():
                            self.issues.append(StyleIssue(
                                j + 1, 1, "error", "enum_value_naming",
                                f"枚举值 '{enum_val}' 应使用全大写下划线命名"
                            ))

            # 检查 goto 标签
            label_pattern = r'^\s*(\w+)\s*:\s*(?!:)'
            match = re.match(label_pattern, stripped)
            if match and not match.group(1).startswith('case') and not match.group(1) == 'default':
                label = match.group(1)
                if not label.isupper():
                    self.issues.append(StyleIssue(
                        i, 1, "error", "label_naming",
                        f"goto标签 '{label}' 应使用全大写下划线命名"
                    ))

            # 检查结构体定义
            struct_pattern = r'^\s*struct\s+(\w+)\s*\{'
            match = re.match(struct_pattern, line)
            if match:
                struct_name = match.group(1)
                if struct_name and not self._is_pascal_case(struct_name):
                    self.issues.append(StyleIssue(
                        i, 1, "error", "struct_naming",
                        f"结构体类型 '{struct_name}' 应使用大驼峰命名"
                    ))

            # 检查结构体字段（简化版）
            if 'struct' in self._get_context(lines, i, 5):
                field_pattern = r'^\s*(?:const\s+)?(?:unsigned\s+)?(?:signed\s+)?(\w+(?:\s*\*+)?)\s+(\w+)\s*[;=]'
                match = re.match(field_pattern, stripped)
                if match and stripped.endswith(';'):
                    field_name = match.group(2)
                    if field_name and not field_name.startswith('g'):
                        if not self._is_camel_case(field_name):
                            self.issues.append(StyleIssue(
                                i, 1, "info", "struct_field_naming",
                                f"结构体字段 '{field_name}' 建议使用小驼峰命名"
                            ))

    def _get_context(self, lines: List[str], current: int, lookback: int) -> str:
        """获取前几行的上下文"""
        start = max(0, current - lookback)
        return '\n'.join(lines[start:current])

    def _is_camel_case(self, name: str) -> bool:
        """判断是否为小驼峰命名"""
        if not name:
            return False
        return name[0].islower() and '_' not in name

    def _is_pascal_case(self, name: str) -> bool:
        """判断是否为大驼峰命名"""
        if not name:
            return False
        return name[0].isupper() and '_' not in name


def print_result(result: FileResult, show_info: bool = False) -> None:
    """打印检查结果"""
    rel_path = Path(result.path).relative_to(Path.cwd()) if Path(result.path).is_absolute() else result.path
    print(f"\n{'='*60}")
    print(f"文件: {rel_path}")
    print(f"  错误: {result.error_count}, 警告: {result.warning_count}")
    print('='*60)

    for issue in result.issues:
        if issue.severity == "info" and not show_info:
            continue
        severity_symbol = {
            "error": "✗",
            "warning": "⚠",
            "info": "ℹ"
        }.get(issue.severity, "?")

        print(f"  {severity_symbol} 第{issue.line}行: {issue.message}")
        print(f"     规则: {issue.rule}")

    if not result.issues:
        print("  ✓ 未发现风格问题")


def main():
    parser = argparse.ArgumentParser(description='C代码风格检查工具')
    parser.add_argument('paths', nargs='+', help='要检查的文件或目录路径')
    parser.add_argument('--info', action='store_true', help='显示信息级别的提示')
    parser.add_argument('--summary', action='store_true', help='仅显示摘要')

    args = parser.parse_args()

    checker = CStyleChecker()
    all_results = []
    total_errors = 0
    total_warnings = 0

    for path_str in args.paths:
        path = Path(path_str)

        if path.is_file():
            results = [checker.check_file(path)]
        elif path.is_dir():
            results = []
            for ext in ['.c', '.h']:
                for file_path in path.rglob(f'*{ext}'):
                    results.append(checker.check_file(file_path))
        else:
            print(f"错误: 路径不存在: {path_str}", file=sys.stderr)
            continue

        for result in results:
            all_results.append(result)
            total_errors += result.error_count
            total_warnings += result.warning_count

            if not args.summary:
                print_result(result, args.info)

    # 打印汇总
    print(f"\n{'='*60}")
    print(f"汇总:")
    print(f"  检查文件数: {len(all_results)}")
    print(f"  总错误数: {total_errors}")
    print(f"  总警告数: {total_warnings}")
    print('='*60)

    # 返回退出码
    sys.exit(0 if total_errors == 0 else 1)


if __name__ == '__main__':
    main()
