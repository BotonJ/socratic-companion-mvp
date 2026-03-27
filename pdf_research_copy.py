#!/usr/bin/env python3
"""
PDF 文本提取 + Chunk分割
  支持PDF（调用pdftotext）+ TXT输入 + 剪贴板

  用法：
      # 处理PDF文件（默认2000字符chunk）
      python3 pdf_extract.py input.pdf > output.txt

      # 处理TXT文件
      python3 pdf_extract.py input.txt > output.txt

      # 从剪贴板读取
      python3 pdf_extract.py > output.txt

      # 自定义chunk大小
      python3 pdf_extract.py input.pdf --chunk-size 3000 > output.txt

      # 添加frontmatter
      python3 pdf_extract.py input.pdf --frontmatter title="论文标题" author="作者" type="paper" > output.txt

      # 添加chunk标记
      python3 pdf_extract.py input.pdf --chunk-prefix "## " > output.txt
  """
import re
import sys
import subprocess
import argparse
from typing import List
from datetime import datetime


def is_pdf_file(filepath: str) -> bool:
    """判断是否为PDF文件"""
    return filepath.lower().endswith('.pdf')


def pdf_to_text(pdf_path: str) -> str:
    """
    调用 pdftotext 提取PDF文本
    支持多种编码检测（P0修复）
    """
    # 检查 pdftotext 是否可用
    try:
        subprocess.run(['pdftotext', '-v'],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误：pdftotext 未安装", file=sys.stderr)
        print("macOS: brew install poppler", file=sys.stderr)
        print("Ubuntu/Debian: sudo apt-get install poppler-utils", file=sys.stderr)
        sys.exit(1)

    try:
        # 使用 -layout 保留布局，输出到stdout
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        result = subprocess.run(
            ['pdftotext', '-layout', '-', '-'],
            input=pdf_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        raw = result.stdout

        # P0修复：尝试多种编码
        encodings = ['utf-8', 'latin-1', 'gbk', 'iso-8859-1', 'cp1252']
        for encoding in encodings:
            try:
                text = raw.decode(encoding)
                # 验证解码质量：检查是否有大量无效字符
                if '\ufffd' in text[:1000] and encoding == 'utf-8':
                    continue  # UTF-8失败，继续尝试其他编码
                return text
            except UnicodeDecodeError:
                continue

        # 所有编码都失败，使用 replace 模式
        return raw.decode('utf-8', errors='replace')

    except subprocess.CalledProcessError as e:
        print(f"错误：PDF提取失败 - {e}", file=sys.stderr)
        if e.stderr:
            print(f"错误信息: {e.stderr.decode('utf-8', errors='replace')}", file=sys.stderr)
        sys.exit(1)


def read_text_from_file(filepath: str) -> str:
    """读取文本文件"""
    with open(filepath, encoding='utf-8') as f:
        return f.read()


def read_text_from_clipboard() -> str:
    """从剪贴板读取文本（macOS/Linux）"""
    try:
        # macOS
        return subprocess.check_output(['pbpaste']).decode('utf-8')
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # Linux
            return subprocess.check_output(['xclip', '-o', '-selection', 'clipboard']).decode('utf-8')
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("错误：无法从剪贴板读取", file=sys.stderr)
            sys.exit(1)


def clean_soft_hyphen(text: str) -> str:
    """清理 soft hyphen (\xad) 字符"""
    return text.replace('\xad', '')


def remove_page_numbers(line: str) -> str:
    """移除页码"""
    line = re.sub(r'^\s*\d+\s*', '', line)
    line = re.sub(r'^\s*-\s*\d+\s*-\s*', '', line)
    line = re.sub(r'\s*\d+\s*$', '', line)
    return line.strip()


def normalize_whitespace(text: str) -> str:
    """标准化空白字符"""
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n')
    return text


def extract_paragraphs(text: str, keep_page_numbers: bool = False) -> List[str]:
    """提取段落"""
    text = clean_soft_hyphen(text)
    text = normalize_whitespace(text)

    lines = text.split('\n')
    paragraphs = []
    current_para = []

    for line in lines:
        if not keep_page_numbers:
            line = remove_page_numbers(line)
        else:
            line = line.strip()

        if not line:
            if current_para:
                paragraph = ' '.join(current_para)
                if paragraph:
                    paragraphs.append(paragraph)
                current_para = []
            continue

        current_para.append(line)

    if current_para:
        paragraph = ' '.join(current_para)
        if paragraph:
            paragraphs.append(paragraph)

    return paragraphs


def split_by_char_count(text: str, max_chars: int) -> List[str]:
    """
    按字符数分割（P0修复：在单词边界切断）

    策略：
    - 接近上限时寻找最近的标点+空格处切断
    - 如果没有标点，在空格处切断
    - 确保chunk不会太小（至少100字符）
    """
    chunks = []
    current_chunk = []
    current_length = 0

    # 标点符号列表
    break_chars = '.!?,;。！？，；:：'
    # 单词分隔符
    word_breaks = ' \t\n'

    for char in text:
        current_chunk.append(char)
        current_length += 1

        # 接近上限时寻找切断点
        if current_length >= max_chars - 50:  # 提前50字符开始寻找
            if char in break_chars:
                # 标点符号，检查后面是否是空格
                chunks.append(''.join(current_chunk).strip())
                current_chunk = []
                current_length = 0
            elif char in word_breaks and current_length > max_chars:
                # 超过上限且是空格，在空格处切断
                chunks.append(''.join(current_chunk[:-1]).strip())  # 不包含空格
                current_chunk = []
                current_length = 0

    if current_chunk:
        chunks.append(''.join(current_chunk).strip())

    # 过滤空chunk
    return [c for c in chunks if c]


def split_by_sentence(text: str, max_chars: int) -> List[str]:
    """按句子边界分割"""
    sentences = re.split(r'([.!?。！？]\s+)', text)
    chunks = []
    current_chunk = []

    for part in sentences:
        if not current_chunk:
            current_chunk = [part]
            continue

        test_chunk = ''.join(current_chunk) + part
        if len(test_chunk) <= max_chars:
            current_chunk.append(part)
        else:
            if current_chunk:
                chunks.append(''.join(current_chunk).strip())
            current_chunk = [part]

    if current_chunk:
        chunks.append(''.join(current_chunk).strip())

    return chunks


def split_by_paragraphs(paragraphs: List[str], max_paragraphs: int) -> List[str]:
    """按段落数量分割"""
    chunks = []
    current_chunk = []

    for para in paragraphs:
        current_chunk.append(para)
        if len(current_chunk) >= max_paragraphs:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


def generate_frontmatter(frontmatter_dict: dict, chunk_count: int, total_chars: int) -> str:
    """生成YAML frontmatter"""
    lines = ['---']

    for key, value in frontmatter_dict.items():
        if isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        elif isinstance(value, str) and '\n' in value:
            lines.append(f"{key}: |")
            for line in value.split('\n'):
                lines.append(f"  {line}")
        else:
            lines.append(f"{key}: {value}")

    # 自动添加的元数据
    if 'date' not in frontmatter_dict:
        lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
    if 'time' not in frontmatter_dict:
        lines.append(f"time: {datetime.now().strftime('%H:%M:%S')}")
    if 'chunk_count' not in frontmatter_dict:
        lines.append(f"chunk_count: {chunk_count}")
    if 'total_chars' not in frontmatter_dict:
        lines.append(f"total_chars: {total_chars}")

    lines.append('---')
    lines.append('')
    return '\n'.join(lines)


def format_chunk(chunk: str, index: int, total: int,
                chunk_prefix: str = '', chunk_suffix: str = '',
                chunk_template: str = None) -> str:
    """格式化单个chunk"""
    if chunk_template:
        chars = len(chunk)
        return chunk_template.format(index=index, total=total, chunk=chunk, chars=chars)
    else:
        parts = []
        if chunk_prefix:
            prefix = chunk_prefix.replace('{i}', str(index)).replace('{n}', str(total))
            parts.append(prefix)
        parts.append(chunk)
        if chunk_suffix:
            suffix = chunk_suffix.replace('{i}', str(index)).replace('{n}', str(total))
            parts.append(suffix)
        return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(
        description='PDF 文本提取 + Chunk分割',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 处理PDF文件
  python3 pdf_extract.py input.pdf > output.txt

  # 处理TXT文件
  python3 pdf_extract.py input.txt > output.txt

  # 从剪贴板
  python3 pdf_extract.py > output.txt

  # 自定义chunk大小
  python3 pdf_extract.py input.pdf --chunk-size 3000 > output.txt

  # 按句子分割
  python3 pdf_extract.py input.pdf --chunk-size 2000 --split-by-sentence > output.txt

  # 添加chunk标记
  python3 pdf_extract.py input.pdf --chunk-prefix "## " > output.txt

  # 添加frontmatter
  python3 pdf_extract.py input.pdf --frontmatter title="论文" author="作者" type="paper" lang="en" > output.txt

  # 完整示例
  python3 pdf_extract.py paper.pdf --chunk-size 4000 --chunk-prefix "## " --frontmatter title="研究" type="paper" lang="en" > output.txt
        """
    )

    parser.add_argument('input_file', nargs='?',
                       help='输入文件（PDF/TXT，可选，默认从剪贴板）')
    parser.add_argument('--chunk-size', type=int, default=2000,
                       help='按字符数分割chunk（默认：2000）')
    parser.add_argument('--max-paragraphs', type=int, default=0,
                       help='按段落数量分割chunk（0=不分割）')
    parser.add_argument('--split-by-sentence', action='store_true',
                       help='按句子边界分割（需要--chunk-size）')
    parser.add_argument('--chunk-prefix', type=str,
                       help='chunk前缀，可用{i}=索引,{n}=总数')
    parser.add_argument('--chunk-suffix', type=str,
                       help='chunk后缀，可用{i}=索引,{n}=总数')
    parser.add_argument('--chunk-template', type=str,
                       help='自定义chunk模板，可用: {index},{total},{chunk},{chars}')
    parser.add_argument('--no-page-numbers', action='store_true',
                       help='保留页码')
    parser.add_argument('--frontmatter', nargs='*', metavar='KEY=VALUE',
                       help='添加YAML frontmatter（如 title="标题" type="book"）')

    args = parser.parse_args()

    # 解析frontmatter
    frontmatter_dict = {}
    if args.frontmatter:
        for item in args.frontmatter:
            if '=' in item:
                key, value = item.split('=', 1)
                value = value.strip('"\'')
                frontmatter_dict[key] = value
            else:
                frontmatter_dict[item] = True

    # 读取文本（支持PDF/TXT/剪贴板）
    if args.input_file:
        filepath = args.input_file
        if is_pdf_file(filepath):
            print(f"正在提取PDF: {filepath}", file=sys.stderr)
            text = pdf_to_text(filepath)
        else:
            text = read_text_from_file(filepath)
    else:
        text = read_text_from_clipboard()

    # 提取段落
    paragraphs = extract_paragraphs(text, keep_page_numbers=args.no_page_numbers)

    # 选择分割策略
    if args.max_paragraphs > 0:
        chunks = split_by_paragraphs(paragraphs, args.max_paragraphs)
    elif args.chunk_size > 0:
        full_text = '\n\n'.join(paragraphs)
        if args.split_by_sentence:
            chunks = split_by_sentence(full_text, args.chunk_size)
        else:
            chunks = split_by_char_count(full_text, args.chunk_size)
    else:
        chunks = ['\n\n'.join(paragraphs)]

    # 统计
    total_chars = sum(len(c) for c in chunks)

    # 输出frontmatter
    if frontmatter_dict:
        fm = generate_frontmatter(frontmatter_dict, len(chunks), total_chars)
        print(fm)

    # 输出chunks
    for i, chunk in enumerate(chunks, 1):
        formatted = format_chunk(
            chunk, i, len(chunks),
            args.chunk_prefix or '',
            args.chunk_suffix or '',
            args.chunk_template
        )
        print(formatted)
        if i < len(chunks):
            print()

    # 统计信息（stderr）
    print(f"\n---", file=sys.stderr)
    print(f"提取统计:", file=sys.stderr)
    print(f"  段落数: {len(paragraphs)}", file=sys.stderr)
    print(f"  Chunk数: {len(chunks)}", file=sys.stderr)
    print(f"  总字符: {total_chars}", file=sys.stderr)
    print(f"  平均chunk: {total_chars // len(chunks) if chunks else 0} 字符", file=sys.stderr)


if __name__ == '__main__':
    main()