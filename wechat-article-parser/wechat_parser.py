import asyncio
from playwright.async_api import async_playwright, BrowserContext
from bs4 import BeautifulSoup
import argparse
from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# 浏览器上下文全局复用，提升性能
browser_context: BrowserContext = None

async def init_browser():
    """初始化浏览器上下文，复用避免重复启动"""
    global browser_context
    if browser_context is None:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--start-maximized'
            ]
        )
        browser_context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        # 注入JS绕过webdriver检测
        await browser_context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
        """)
    return browser_context

async def parse_wechat_article(url: str) -> dict:
    """
    解析微信公众号文章
    :param url: 微信文章链接
    :return: 解析结果，包含标题、作者、发布时间、正文内容、原文链接
    """
    context = await init_browser()
    page = await context.new_page()
    
    try:
        # 禁用图片、CSS、字体等资源加载，提升速度
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"] else route.continue_())
        
        # 访问页面，等待正文加载完成
        response = await page.goto(url, timeout=30000, wait_until='domcontentloaded')
        if response.status != 200:
            return {"success": False, "error": f"访问失败，HTTP状态码：{response.status}"}
        
        # 等待正文元素加载
        await page.wait_for_selector('#js_content', timeout=15000)
        
        # 获取页面HTML
        html = await page.content()
        soup = BeautifulSoup(html, 'lxml')
        
        # 提取基础信息
        title = soup.select_one('#activity-name')
        title = title.get_text(strip=True) if title else ''
        
        author = soup.select_one('#js_name')
        author = author.get_text(strip=True) if author else ''
        
        publish_time = soup.select_one('#publish_time')
        if not publish_time:
            # 尝试从meta标签提取
            publish_time = soup.find('meta', attrs={'name': 'weibo:article:create_at'})
            publish_time = publish_time['content'] if publish_time else ''
        else:
            publish_time = publish_time.get_text(strip=True)
        
        # 提取正文内容，过滤所有标签保留文本和换行
        content_ele = soup.select_one('#js_content')
        if not content_ele:
            return {"success": False, "error": "未找到正文内容，可能链接无效或需要登录"}
        
        # 处理正文，保留段落结构
        for br in content_ele.find_all('br'):
            br.replace_with('\n')
        for p in content_ele.find_all('p'):
            p.append('\n\n')
        content = content_ele.get_text()
        # 清理多余空白
        content = re.sub(r'\n{3,}', '\n\n', content).strip()
        
        return {
            "success": True,
            "data": {
                "title": title,
                "author": author,
                "publish_time": publish_time,
                "content": content,
                "original_url": url
            }
        }
    except Exception as e:
        return {"success": False, "error": f"解析失败：{str(e)}"}
    finally:
        await page.close()

# 命令行模式
def cli_mode():
    parser = argparse.ArgumentParser(description='微信公众号文章内容提取工具')
    parser.add_argument('url', help='微信公众号文章链接')
    parser.add_argument('--output', '-o', help='输出文件路径，可选，默认打印到控制台')
    args = parser.parse_args()
    
    async def run():
        result = await parse_wechat_article(args.url)
        if result['success']:
            data = result['data']
            output = f"""【标题】{data['title']}
【作者】{data['author']}
【发布时间】{data['publish_time']}
【原文链接】{data['original_url']}

【正文内容】
{data['content']}
            """
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"解析完成，结果已保存到：{args.output}")
            else:
                print(output)
        else:
            print(f"错误：{result['error']}")
    
    asyncio.run(run())

# Web接口模式
@app.route('/parse', methods=['POST'])
def api_parse():
    url = request.json.get('url') if request.is_json else request.form.get('url')
    if not url:
        return jsonify({"success": False, "error": "缺少参数url"}), 400
    result = asyncio.run(parse_wechat_article(url))
    return jsonify(result)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        # 启动web服务
        asyncio.run(init_browser())
        app.run(host='0.0.0.0', port=9001, debug=False)
    else:
        # 命令行模式
        cli_mode()
