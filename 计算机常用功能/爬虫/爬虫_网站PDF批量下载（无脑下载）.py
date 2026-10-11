import os
import re
import requests
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def sanitize_filename(filename):
    filename = re.sub(r'\?.*$', '', filename)
    filename = re.sub(r'#.*$', '', filename)
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200] + ext

    return filename


def get_all_links(base_url, soup, exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = []
    links = set()
    for tag in soup.find_all('a', href=True):
        href = tag['href'].strip()
        if not href or href.startswith('javascript:'):
            continue
        if any(pattern in href for pattern in exclude_patterns):
            continue
        absolute_url = urljoin(base_url, href)
        if is_valid_url(absolute_url):
            if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                links.add(absolute_url)
    return links


def is_pdf_link(url):
    """检查链接是否是PDF文件"""
    if url.lower().endswith('.pdf'):
        return True
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        content_type = response.headers.get('content-type', '').lower()
        return 'pdf' in content_type or 'application/pdf' in content_type
    except:
        return False


def download_pdf(pdf_url, save_path, headers=None, timeout=30):
    """
    下载单个PDF文件
    参数:
    - pdf_url: PDF文件的URL
    - save_path: 保存目录路径
    - headers: 请求头（可选）
    - timeout: 超时时间（秒）
    返回:
    - 成功: (文件路径, 文件大小)
    - 失败: (None, 错误信息)
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    try:
        parsed_url = urlparse(pdf_url)
        filename = os.path.basename(parsed_url.path)
        if not filename or not filename.lower().endswith('.pdf'):
            # 如果没有文件名或不是.pdf，创建一个
            filename = f"pdf_{hash(pdf_url) % 1000000}.pdf"
        filename = sanitize_filename(filename)
        filepath = os.path.join(save_path, filename)
        #检查文件是否已存在
        if os.path.exists(filepath):
            #如果文件已存在，添加后缀
            base_name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filepath):
                filename = f"{base_name}_{counter}{ext}"
                filepath = os.path.join(save_path, filename)
                counter += 1

        logger.info(f"正在下载: {pdf_url}")
        logger.info(f"保存为: {filename}")

        #下载文件
        response = requests.get(pdf_url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        #检查是否为PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and 'application/pdf' not in content_type:
            if not pdf_url.lower().endswith('.pdf'):
                logger.warning(f"URL可能不是PDF文件: {pdf_url}")

        #保存文件
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        file_size = os.path.getsize(filepath)
        logger.info(f"下载完成: {filename} ({file_size / 1024:.2f} KB)")

        return filepath, file_size

    except requests.exceptions.RequestException as e:
        logger.error(f"下载失败 {pdf_url}: {e}")
        return None, str(e)
    except Exception as e:
        logger.error(f"保存文件失败 {pdf_url}: {e}")
        return None, str(e)


def crawl_and_download_pdfs(base_url, save_path, max_pages=50, max_depth=3, delay=1):
    """
    主函数：爬取网站并下载所有PDF文件

    参数:
    - base_url:起始URL
    - save_path:保存PDF文件的目录
    - max_pages:最大爬取页面数（防止无限循环）
    - max_depth:最大爬取深度
    - delay: 请求之间的延迟（秒），避免被封

    返回:
    - 下载统计信息字典
    """
    os.makedirs(save_path, exist_ok=True)

    visited_urls = set()
    pdf_urls_found = set()
    pdf_urls_downloaded = []
    pdf_urls_failed = []
    to_crawl = [(base_url, 0)]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    logger.info(f"开始爬取: {base_url}")
    logger.info(f"保存路径: {save_path}")
    logger.info(f"最大页面数: {max_pages}, 最大深度: {max_depth}")

    while to_crawl and len(visited_urls) < max_pages:
        current_url, depth = to_crawl.pop(0)
        if current_url in visited_urls:
            continue
        if depth > max_depth:
            continue

        try:
            logger.info(f"爬取 [{depth}] {current_url}")
            time.sleep(delay)
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()
            visited_urls.add(current_url)

            soup = BeautifulSoup(response.text, 'html.parser')

            if is_pdf_link(current_url):
                pdf_urls_found.add(current_url)
                logger.info(f"当前页面就是PDF: {current_url}")

            exclude_patterns = [
                'mailto:', 'tel:', 'javascript:',
                '.jpg', '.jpeg', '.png', '.gif', '.css', '.js'
            ]

            all_links = get_all_links(current_url, soup, exclude_patterns)
            for link in all_links:
                if link in visited_urls:
                    continue

                if is_pdf_link(link):
                    pdf_urls_found.add(link)
                else:
                    #添加到待爬取队列
                    if depth + 1 <= max_depth:
                        to_crawl.append((link, depth + 1))
            logger.info(f"已发现 {len(pdf_urls_found)} 个PDF，待爬取 {len(to_crawl)} 个页面")

        except requests.exceptions.RequestException as e:
            logger.error(f"爬取失败 {current_url}: {e}")
        except Exception as e:
            logger.error(f"解析失败 {current_url}: {e}")
    #下载所有发现的PDF文件
    logger.info(f"\n{'=' * 60}")
    logger.info(f"开始下载 {len(pdf_urls_found)} 个PDF文件...")

    for i, pdf_url in enumerate(pdf_urls_found, 1):
        logger.info(f"\n[{i}/{len(pdf_urls_found)}]")
        result = download_pdf(pdf_url, save_path, headers)
        if result[0]:
            pdf_urls_downloaded.append((pdf_url, result[0], result[1]))
        else:
            pdf_urls_failed.append((pdf_url, result[1]))
        time.sleep(delay)
    stats = {
        'total_pages_crawled': len(visited_urls),
        'total_pdfs_found': len(pdf_urls_found),
        'total_pdfs_downloaded': len(pdf_urls_downloaded),
        'total_pdfs_failed': len(pdf_urls_failed),
        'total_size_downloaded': sum(size for _, _, size in pdf_urls_downloaded),
        'save_path': save_path,
        'base_url': base_url,
        'downloaded_files': [path for _, path, _ in pdf_urls_downloaded],
        'failed_urls': pdf_urls_failed
    }
    return stats
def print_statistics(stats):
    """打印下载统计信息"""
    print("\n" + "=" * 60)
    print("PDF下载统计报告")
    print("=" * 60)
    print(f"起始网址: {stats['base_url']}")
    print(f"保存目录: {stats['save_path']}")
    print(f"爬取页面数: {stats['total_pages_crawled']}")
    print(f"发现PDF数: {stats['total_pdfs_found']}")
    print(f"成功下载: {stats['total_pdfs_downloaded']}")
    print(f"下载失败: {stats['total_pdfs_failed']}")
    print(f"总下载大小: {stats['total_size_downloaded'] / 1024 / 1024:.2f} MB")
    if stats['downloaded_files']:
        print("\n下载的文件:")
        for i, filepath in enumerate(stats['downloaded_files'], 1):
            filename = os.path.basename(filepath)
            print(f"  {i:3d}. {filename}")
    if stats['failed_urls']:
        print("\n失败的URL:")
        for url, error in stats['failed_urls']:
            print(f" - {url}")
            print(f"错误: {error}")
def main():
    #目标网站
    base_url = "https://www.mcm.edu.cn/html_cn/node/f1241bf39c38153b57bdb27125fa2d72.html"
    #保存路径
    save_path = r"E:\101321131熊可\测试"
    #参数修改
    stats = crawl_and_download_pdfs(
        base_url=base_url,
        save_path=save_path,
        max_pages=3,#最多爬取100个页面
        max_depth=1,#最大爬取深度为2层
        delay=1
    )
    return stats
if __name__ == "__main__":
    try:
        main()
        print("\n程序执行完成！")
    except KeyboardInterrupt:
        print("\n\n程序被用户中断。")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        import traceback

        traceback.print_exc()