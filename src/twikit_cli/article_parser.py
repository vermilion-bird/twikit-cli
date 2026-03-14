#!/usr/bin/env python3
"""
解析Twitter/X Article API返回的数据，提取可读的文本内容
"""


def parse_article_content(article_data):
    """
    解析article数据结构，提取文本内容

    Args:
        article_data: 从API返回的article字典对象

    Returns:
        dict: 包含标题、预览、正文等信息的字典
    """
    try:
        # 获取article_results
        article_result = article_data.get('article_results', {}).get('result', {})

        if not article_result:
            return {"error": "未找到article内容"}

        # 提取元数据
        article_info = {
            'rest_id': article_result.get('rest_id', ''),
            'title': article_result.get('title', ''),
            'preview_text': article_result.get('preview_text', ''),
            'cover_media_url': '',
            'text_content': []
        }

        # 提取封面图片URL
        cover_media = article_result.get('cover_media', {})
        if cover_media:
            media_info = cover_media.get('media_info', {})
            if media_info:
                article_info['cover_media_url'] = media_info.get('original_img_url', '')

        # 提取content_state中的文本块
        content_state = article_result.get('content_state', {})
        blocks = content_state.get('blocks', [])
        entity_map = content_state.get('entityMap', [])

        # 解析每个文本块
        for block in blocks:
            block_type = block.get('type', 'unstyled')
            text = block.get('text', '').strip()

            # 跳过空内容和atomic类型（通常是图片/媒体）
            if not text or block_type == 'atomic':
                continue

            # 根据类型格式化文本
            formatted_text = format_block(block_type, text)
            article_info['text_content'].append(formatted_text)

        return article_info

    except Exception as e:
        return {"error": f"解析失败: {str(e)}"}


def format_block(block_type, text):
    """
    根据块类型格式化文本

    Args:
        block_type: 块的类型（header-one, blockquote等）
        text: 文本内容

    Returns:
        str: 格式化后的文本
    """
    if block_type == 'header-one':
        return f"\n{'#' * 1} {text}\n"
    elif block_type == 'header-two':
        return f"\n{'#' * 2} {text}\n"
    elif block_type == 'header-three':
        return f"\n{'#' * 3} {text}\n"
    elif block_type == 'blockquote':
        return f"> {text}"
    elif block_type == 'unordered-list-item':
        return f"• {text}"
    elif block_type == 'ordered-list-item':
        return f"  {text}"
    elif block_type == 'code-block':
        return f"```\n{text}\n```"
    else:  # unstyled or other
        return text


def print_article(article_info):
    """
    格式化打印article信息

    Args:
        article_info: parse_article_content返回的字典
    """
    if 'error' in article_info:
        print(f"错误: {article_info['error']}")
        return

    print("="*80)
    print(f"标题: {article_info['title']}")
    print(f"ID: {article_info['rest_id']}")
    print(f"\n预览: {article_info['preview_text']}")

    if article_info['cover_media_url']:
        print(f"\n封面图: {article_info['cover_media_url']}")

    print("\n" + "="*80)
    print("正文内容:")
    print("="*80 + "\n")

    for content in article_info['text_content']:
        print(content)


def markdown_article_str(article_info):
    """
    格式化打印article信息

    Args:
        article_info: parse_article_content返回的字典
    """
    if 'error' in article_info:
        print(f"错误: {article_info['error']}")
        return
    markdown_str= ""

    print("="*80)
    print(f"标题: {article_info['title']}")
    print(f"ID: {article_info['rest_id']}")
    print(f"\n预览: {article_info['preview_text']}")

    markdown_str += "="*80
    markdown_str +=f"标题: {article_info['title']}"
    markdown_str +=f"ID: {article_info['rest_id']}"
    markdown_str +=f"\n预览: {article_info['preview_text']}"


    if article_info['cover_media_url']:
        print(f"\n封面图: {article_info['cover_media_url']}")
        markdown_str +=f"\n封面图: {article_info['cover_media_url']}"

    print("\n" + "="*80)
    print("正文内容:")
    print("="*80 + "\n")
    markdown_str +="\n" + "="*80
    markdown_str +="正文内容:"
    markdown_str +="="*80 + "\n"


    for content in article_info['text_content']:
        print(content)
        markdown_str +=content
    return markdown_str

def save_article_to_file(article_info, filename='article_output.txt'):
    """
    保存article内容到文件

    Args:
        article_info: parse_article_content返回的字典
        filename: 输出文件名
    """
    if 'error' in article_info:
        print(f"无法保存: {article_info['error']}")
        return False

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"标题: {article_info['title']}\n")
            f.write(f"ID: {article_info['rest_id']}\n")
            f.write(f"\n预览: {article_info['preview_text']}\n")

            if article_info['cover_media_url']:
                f.write(f"\n封面图: {article_info['cover_media_url']}\n")

            f.write("\n" + "="*80 + "\n")
            f.write("正文内容:\n")
            f.write("="*80 + "\n\n")

            for content in article_info['text_content']:
                f.write(content + "\n")

        print(f"✓ 文章已保存到: {filename}")
        return True

    except Exception as e:
        print(f"保存失败: {str(e)}")
        return False


# 使用示例
if __name__ == '__main__':
    import json
    import sys

    print("Twitter/X Article 解析器")
    print("="*80)

    # 检查命令行参数
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = 'article.json'

    try:
        # 示例：从JSON文件加载
        print(f"正在读取文件: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 提取article数据
        article_data = data['data']['tweetResult']['result']['article']

        # 解析article
        article_info = parse_article_content(article_data)

        # 打印内容
        print_article(article_info)

        # 保存到文件
        output_file = json_file.replace('.json', '_parsed.txt')
        save_article_to_file(article_info, output_file)

    except FileNotFoundError:
        print(f"错误: 文件 '{json_file}' 不存在")
        print("\n使用方法:")
        print("  python article_parser.py [json文件路径]")
        print("\n或者在代码中直接导入使用:")
        print("  from article_parser import parse_article_content")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"错误: JSON格式错误 - {e}")
        print("\n提示: 请确保JSON文件格式正确，字符串中的引号需要转义")
        sys.exit(1)

    except KeyError as e:
        print(f"错误: 数据结构不正确，缺少字段: {e}")
        print("\n提示: 请确保JSON文件包含完整的article数据结构")
        sys.exit(1)

    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)
