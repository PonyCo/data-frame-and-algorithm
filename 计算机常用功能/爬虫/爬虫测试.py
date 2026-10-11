"""
智能PDF下载器：处理多种HTML页面结构
功能：自动识别页面结构，提取所有链接，下载PDF并用标题重命名
"""

import os
import re
import requests
import time
import json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import PyPDF2
import io
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class WebPageItem:
    """网页条目数据类"""
    title: str
    detail_url: str
    pdf_url: Optional[str] = None
    filepath: Optional[str] = None
    success: bool = False
    error_msg: Optional[str] = None

class SmartPDFDownloader:
    """智能PDF下载器，适应多种页面结构"""

    def __init__(self, headers: Optional[Dict] = None):
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.visited_urls = set()  # 已访问的URL集合
        self.download_history = []  # 下载历史

    def clean_filename(self, filename: str) -> str:
        """清理文件名，使其适合作为文件名"""
        # 移除括号内容（如日期）
        filename = re.sub(r'\(.*?\)', '', filename).strip()
        # 移除特殊字符
        illegal_chars = r'[<>:"/\\|?*]'
        filename = re.sub(illegal_chars, '_', filename)
        # 替换空格为下划线
        filename = filename.replace(' ', '_')
        # 移除多余的下划线
        filename = re.sub(r'_+', '_', filename)
        # 限制长度
        if len(filename) > 150:
            filename = filename[:150]
        return filename

    def extract_links_from_page(self, url: str, link_text_patterns: List[str] = None) -> List[Tuple[str, str]]:
        """
        从页面中提取符合条件的链接

        参数:
        - url: 页面URL
        - link_text_patterns: 链接文本匹配模式列表

        返回: [(链接文本, 链接URL), ...]
        """
        if link_text_patterns is None:
            link_text_patterns = ['获奖名单', '通知', '公告', '结果', '名单']#（可改）

        items = []
        try:
            logger.info(f"正在分析页面: {url}")

            # 检查是否已访问
            if url in self.visited_urls:
                logger.debug(f"跳过已访问页面: {url}")
                return items

            self.visited_urls.add(url)

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # 检测页面编码
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # 保存页面内容用于调试（可选）
            # self._save_page_for_debug(url, soup)

            # 策略1：查找所有链接并筛选
            for link in soup.find_all('a', href=True):
                href = link['href'].strip()
                text = link.get_text(strip=True)

                # 跳过无效链接
                if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    continue

                # 转换相对URL为绝对URL
                absolute_url = urljoin(url, href)

                # 避免重复
                if absolute_url in self.visited_urls:
                    continue

                # 判断是否为目标链接
                if self._is_target_link(text, href, link_text_patterns):
                    items.append((text, absolute_url))
                    logger.debug(f"发现链接: {text} -> {absolute_url}")

            # 策略2：如果策略1没找到足够链接，尝试其他方法
            if len(items) < 3:
                items.extend(self._find_links_alternative_methods(url, soup, link_text_patterns))

            logger.info(f"从页面提取到 {len(items)} 个链接")
            return items

        except Exception as e:
            logger.error(f"提取页面链接失败 {url}: {e}")
            return []

    def _is_target_link(self, text: str, href: str, patterns: List[str]) -> bool:
        """判断链接是否为目标链接"""
        # 文本长度过滤
        if len(text) < 4:
            return False

        # 匹配文本模式
        text_matches = any(pattern in text for pattern in patterns)

        # 匹配URL模式
        url_matches = any(pattern in href for pattern in ['.html', '.htm', '/node/', 'detail'])

        # 排除不需要的链接
        excluded_patterns = ['.jpg', '.png', '.gif', '.css', '.js', '.zip', '.rar']
        excluded = any(pattern in href.lower() for pattern in excluded_patterns)

        return text_matches and url_matches and not excluded

    def _find_links_alternative_methods(self, base_url: str, soup: BeautifulSoup, patterns: List[str]) -> List[Tuple[str, str]]:
        """使用备选方法查找链接"""
        items = []

        # 方法A：查找列表项中的链接
        for li in soup.find_all(['li', 'div', 'p']):
            # 检查元素是否包含目标关键词
            li_text = li.get_text(strip=True)
            if any(pattern in li_text for pattern in patterns):
                # 查找其中的链接
                links = li.find_all('a', href=True)
                if links:
                    for link in links:
                        href = link['href'].strip()
                        if href:
                            absolute_url = urljoin(base_url, href)
                            link_text = link.get_text(strip=True) or li_text[:50]
                            items.append((link_text, absolute_url))

        # 方法B：查找包含特定class或id的链接
        selectors = ['.list a', '.news a', '.content a', 'a[href*=".html"]', 'a[href*="/node/"]']
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    href = elem.get('href', '').strip()
                    text = elem.get_text(strip=True)
                    if href and text and len(text) > 3:
                        absolute_url = urljoin(base_url, href)
                        items.append((text, absolute_url))
            except:
                continue

        return list(set(items))  # 去重

    def _save_page_for_debug(self, url: str, soup: BeautifulSoup):
        """保存页面内容用于调试"""
        debug_dir = "page_debug"
        os.makedirs(debug_dir, exist_ok=True)

        # 生成文件名
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path) or "index"
        if not filename.endswith('.html'):
            filename += '.html'

        # 保存文件
        filepath = os.path.join(debug_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"<!-- URL: {url} -->\n")
            f.write(f"<!-- Time: {time.strftime('%Y-%m-%d %H:%M:%S')} -->\n")
            f.write(str(soup))

        logger.debug(f"页面已保存到: {filepath}")

    def find_pdf_in_page(self, url: str) -> Optional[str]:
        """
        在页面中查找PDF链接

        返回: PDF的下载链接，如果找不到则返回None
        """
        try:
            logger.debug(f"在页面中查找PDF: {url}")

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # 检查是否直接返回PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' in content_type or 'application/pdf' in content_type:
                logger.info(f"页面直接返回PDF: {url}")
                return url

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找PDF链接的多种方法
            pdf_candidates = []

            # 1. 查找直接链接
            pdf_links = []
            for link in soup.find_all('a', href=True):
                href = link['href'].strip()
                if href.lower().endswith('.pdf'):
                    absolute_url = urljoin(url, href)
                    pdf_links.append(absolute_url)

            # 2. 查找iframe、embed、object
            for tag_name in ['iframe', 'embed', 'object']:
                for tag in soup.find_all(tag_name, src=True):
                    src = tag.get('src', '').strip()
                    if src:
                        absolute_url = urljoin(url, src)
                        pdf_candidates.append(absolute_url)

            # 3. 查找object的data属性
            for obj in soup.find_all('object', data=True):
                data = obj.get('data', '').strip()
                if data:
                    absolute_url = urljoin(url, data)
                    pdf_candidates.append(absolute_url)

            # 合并所有候选链接
            all_candidates = list(set(pdf_links + pdf_candidates))

            # 过滤并选择最佳PDF链接
            for candidate in all_candidates:
                # 优先选择包含特定关键词的链接
                candidate_lower = candidate.lower()
                if any(keyword in candidate_lower for keyword in ['download', 'file', 'pdf', '获奖', 'list']):
                    logger.info(f"找到PDF链接: {candidate}")
                    return candidate

            # 如果没有明显关键词，返回第一个PDF链接
            if pdf_links:
                logger.info(f"找到PDF链接: {pdf_links[0]}")
                return pdf_links[0]

            # 检查页面中是否有重定向到PDF的按钮
            for button in soup.find_all(['button', 'input']):
                onclick = button.get('onclick', '').lower()
                if '.pdf' in onclick:
                    # 提取PDF URL
                    match = re.search(r'["\'](.*?\.pdf)["\']', onclick)
                    if match:
                        pdf_url = match.group(1)
                        absolute_url = urljoin(url, pdf_url)
                        logger.info(f"从按钮找到PDF链接: {absolute_url}")
                        return absolute_url

            logger.warning(f"页面中未找到PDF链接: {url}")
            return None

        except Exception as e:
            logger.error(f"查找PDF失败 {url}: {e}")
            return None

    def download_pdf(self, pdf_url: str, title: str, save_dir: str) -> Tuple[bool, str]:
        """下载PDF文件"""
        try:
            # 准备文件名
            clean_title = self.clean_filename(title)
            filename = f"{clean_title}.pdf"
            filepath = os.path.join(save_dir, filename)

            # 处理文件名冲突
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(filepath):
                filename = f"{base_name}_{counter}{ext}"
                filepath = os.path.join(save_dir, filename)
                counter += 1

            logger.info(f"正在下载: {clean_title}")
            logger.info(f"PDF链接: {pdf_url[:100]}...")

            # 下载文件
            response = self.session.get(pdf_url, timeout=30, stream=True)
            response.raise_for_status()

            # 检查文件大小
            content_length = response.headers.get('content-length')
            if content_length:
                file_size = int(content_length)
                if file_size > 100 * 1024 * 1024:  # 100MB限制
                    logger.warning(f"文件过大 ({file_size/1024/1024:.1f}MB)，可能不是PDF")

            # 保存文件
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            actual_size = os.path.getsize(filepath)
            logger.info(f"下载完成: {filename} ({actual_size/1024:.1f} KB)")

            # 验证PDF
            if self._validate_pdf(filepath):
                return True, filepath
            else:
                os.remove(filepath)  # 删除无效文件
                return False, "PDF文件无效或损坏"

        except requests.exceptions.RequestException as e:
            return False, f"下载失败: {e}"
        except Exception as e:
            return False, f"保存失败: {e}"

    def _validate_pdf(self, filepath: str) -> bool:
        """验证PDF文件是否有效"""
        try:
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                # 尝试读取第一页
                if len(pdf_reader.pages) > 0:
                    _ = pdf_reader.pages[0].extract_text()
                    return True
            return False
        except:
            return False

    def process_website(self,
                       start_urls: List[str],
                       save_dir: str,
                       max_pages: int = 100,
                       link_patterns: List[str] = None) -> Dict:
        """
        处理整个网站

        参数:
        - start_urls: 起始URL列表
        - save_dir: 保存目录
        - max_pages: 最大处理页面数
        - link_patterns: 链接文本匹配模式

        返回: 处理结果统计
        """
        if link_patterns is None:
            link_patterns = ['获奖名单', '通知', '公告', '结果', '名单', '公示']#可改，如果链接是无效或读取不出来，则令Link为这些关键词链接

        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)

        # 初始化队列和结果
        url_queue = start_urls.copy()
        all_items = []

        logger.info(f"开始处理网站，起始URL: {len(start_urls)} 个")
        logger.info(f"保存目录: {save_dir}")
        logger.info(f"最大页面数: {max_pages}")

        # 广度优先遍历
        while url_queue and len(self.visited_urls) < max_pages:
            current_url = url_queue.pop(0)

            # 提取当前页面的链接
            page_items = self.extract_links_from_page(current_url, link_patterns)

            for title, detail_url in page_items:
                # 创建条目对象
                item = WebPageItem(title=title, detail_url=detail_url)

                # 在详情页查找PDF
                pdf_url = self.find_pdf_in_page(detail_url)

                if pdf_url:
                    item.pdf_url = pdf_url

                    # 下载PDF
                    success, result = self.download_pdf(pdf_url, title, save_dir)

                    if success:
                        item.success = True
                        item.filepath = result
                        logger.info(f"✓ 成功下载: {title}")
                    else:
                        item.success = False
                        item.error_msg = result
                        logger.error(f"✗ 下载失败: {title} - {result}")
                else:
                    item.error_msg = "未找到PDF链接"
                    logger.warning(f"未找到PDF: {title}")

                all_items.append(item)

                # 延迟
                time.sleep(1)

            # 如果还有未访问的链接，添加到队列（限制深度）
            for _, detail_url in page_items:
                if detail_url not in self.visited_urls and len(self.visited_urls) < max_pages:
                    url_queue.append(detail_url)

        # 统计结果
        successful = [item for item in all_items if item.success]
        failed = [item for item in all_items if not item.success]

        results = {
            'total_pages_visited': len(self.visited_urls),
            'total_items_found': len(all_items),
            'successful_downloads': len(successful),
            'failed_downloads': len(failed),
            'save_dir': save_dir,
            'start_urls': start_urls,
            'successful_items': successful,
            'failed_items': failed
        }

        # 保存下载历史
        self._save_download_history(save_dir, results)

        return results

    def _save_download_history(self, save_dir: str, results: Dict):
        """保存下载历史到JSON文件"""
        history_file = os.path.join(save_dir, "download_history.json")

        history_data = {
            'download_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': {
                'total_pages_visited': results['total_pages_visited'],
                'total_items_found': results['total_items_found'],
                'successful_downloads': results['successful_downloads'],
                'failed_downloads': results['failed_downloads']
            },
            'successful_items': [
                {
                    'title': item.title,
                    'detail_url': item.detail_url,
                    'pdf_url': item.pdf_url,
                    'filepath': item.filepath
                }
                for item in results['successful_items']
            ],
            'failed_items': [
                {
                    'title': item.title,
                    'detail_url': item.detail_url,
                    'error': item.error_msg
                }
                for item in results['failed_items']
            ]
        }

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)

        logger.info(f"下载历史已保存到: {history_file}")

def print_summary(results: Dict):
    """打印下载摘要"""
    print("\n" + "="*60)
    print("PDF下载摘要")
    print("="*60)
    print(f"起始URL数量: {len(results['start_urls'])}")
    print(f"访问页面总数: {results['total_pages_visited']}")
    print(f"发现条目总数: {results['total_items_found']}")
    print(f"成功下载: {results['successful_downloads']}")
    print(f"下载失败: {results['failed_downloads']}")

    # 计算总文件大小
    total_size = 0
    for item in results['successful_items']:
        if item.filepath and os.path.exists(item.filepath):
            total_size += os.path.getsize(item.filepath)

    if total_size > 0:
        print(f"总下载大小: {total_size/1024/1024:.2f} MB")

    # 显示部分成功下载的文件
    if results['successful_items']:
        print(f"\n成功下载的文件 (前10个):")
        for i, item in enumerate(results['successful_items'][:10], 1):
            filename = os.path.basename(item.filepath)
            print(f"  {i:2d}. {filename}")

    # 显示失败原因
    if results['failed_items']:
        print(f"\n失败原因统计:")
        error_counts = {}
        for item in results['failed_items']:
            error = item.error_msg or "未知错误"
            if error not in error_counts:
                error_counts[error] = 0
            error_counts[error] += 1

        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error}: {count} 次")

def save_detailed_report(results: Dict, save_dir: str):
    """保存详细报告"""
    report_file = os.path.join(save_dir, "detailed_report.txt")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("PDF下载详细报告\n")
        f.write("="*60 + "\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"起始URL:\n")
        for url in results['start_urls']:
            f.write(f"  - {url}\n")
        f.write(f"\n访问页面总数: {results['total_pages_visited']}\n")
        f.write(f"发现条目总数: {results['total_items_found']}\n")
        f.write(f"成功下载: {results['successful_downloads']}\n")
        f.write(f"下载失败: {results['failed_downloads']}\n")

        # 成功下载列表
        if results['successful_items']:
            f.write("\n成功下载的文件列表:\n")
            for i, item in enumerate(results['successful_items'], 1):
                filename = os.path.basename(item.filepath)
                file_size = os.path.getsize(item.filepath) if os.path.exists(item.filepath) else 0
                f.write(f"{i:4d}. {filename} ({file_size/1024:.1f} KB)\n")
                f.write(f"     标题: {item.title}\n")
                f.write(f"     详情页: {item.detail_url}\n")
                f.write(f"     PDF链接: {item.pdf_url}\n\n")

        # 失败列表
        if results['failed_items']:
            f.write("\n下载失败的条目:\n")
            for i, item in enumerate(results['failed_items'], 1):
                f.write(f"{i:4d}. {item.title}\n")
                f.write(f"     详情页: {item.detail_url}\n")
                f.write(f"     失败原因: {item.error_msg}\n\n")

    print(f"\n详细报告已保存到: {report_file}")

# ==================== 使用示例 ====================
def main():
    print("=" * 60)

    # 检查必要的库
    try:
        import requests
        import bs4
        import PyPDF2
    except ImportError as e:
        print(f"错误：缺少必要的库，请运行以下命令安装：")
        print(f"  pip install requests beautifulsoup4 PyPDF2")
        exit(1)

    # ========== 配置参数 ==========
    # 1. 起始URL列表（可以添加多个不同的页面）
    start_urls = [
        "https://www.mcm.edu.cn/html_cn/node/f1241bf39c38153b57bdb27125fa2d72.html",
        "https://www.mcm.edu.cn/html_cn/node/3aa4e9fc4c5a755da53b343660cdaf59.html",
        "https://www.mcm.edu.cn/html_cn/node/495b16715673eaee3a770d99aaf9d857.html",
    ]

    # 2. 保存目录
    save_dir = r"E:\101321131熊可\测试"
    # 3. 链接文本匹配模式（用于识别目标链接）
    link_patterns = [
        '获奖名单'
    ]
    # 4. 最大处理页面数
    max_pages = 6
    # ========== 执行下载 ==========
    try:
        # 创建下载器
        downloader = SmartPDFDownloader()
        # 处理网站
        results = downloader.process_website(
            start_urls=start_urls,
            save_dir=save_dir,
            max_pages=max_pages,
            link_patterns=link_patterns
        )
        print("\n程序执行完成！")
    except KeyboardInterrupt:
        print("\n\n程序被用户中断。")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
    main()