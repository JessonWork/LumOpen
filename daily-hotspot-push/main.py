import os
import time
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('hotspot_push.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 加载配置
load_dotenv()
SEARCH_API = os.getenv('SEARCH_API', 'http://127.0.0.1:8300/res/v1/web/search')
FEISHU_WEBHOOK = os.getenv('FEISHU_WEBHOOK', '')
FEISHU_CHAT_ID = os.getenv('FEISHU_CHAT_ID', 'oc_c54312d70f4b25f669391cbeb7842208')
PUSH_TIME = os.getenv('PUSH_TIME', '09:00')
RETRY_TIMES = int(os.getenv('RETRY_TIMES', 2))

# 领域配置：关键词、标签、颜色
CATEGORIES = [
    {"name": "AI", "keyword": "24小时内AI行业热点 大模型 Agent 人工智能", "color": "#165DFF"},
    {"name": "互联网", "keyword": "24小时内互联网行业热点 大厂动态 产品发布", "color": "#00B42A"},
    {"name": "科技", "keyword": "24小时内科技行业热点 半导体 硬件 前沿技术", "color": "#FF7D00"}
]

def fetch_hotspots(category: dict) -> list:
    """采集单个领域的热点"""
    try:
        params = {
            "q": category["keyword"],
            "count": 5,
            "freshness": "day"
        }
        response = requests.get(SEARCH_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        results = data.get("web", {}).get("results", [])
        
        # 格式化每条热点
        hotspots = []
        for item in results:
            title = item.get("title", "").strip()
            url = item.get("url", "").strip()
            description = item.get("description", "").strip()[:100] + "..." if len(item.get("description", "")) > 100 else item.get("description", "").strip()
            if title and url and description:
                hotspots.append({
                    "title": title,
                    "url": url,
                    "description": description,
                    "category": category["name"],
                    "color": category["color"]
                })
        return hotspots[:5]
    except Exception as e:
        logger.error(f"采集{category['name']}领域热点失败：{str(e)}")
        return []

def format_content(all_hotspots: dict) -> str:
    """格式化为飞书富文本内容"""
    today = datetime.now().strftime("%Y-%m-%d")
    total = sum([len(v) for v in all_hotspots.values()])
    
    # 头部
    content = f"📰 每日行业热点 | {today}\n"
    content += f"<font color=\"gray\">今日共收录{total}条热点，覆盖AI/互联网/科技领域</font>\n"
    content += "---\n\n"
    
    if total == 0:
        content += "⚠️ 今日暂未获取到有效行业热点，请稍后手动触发重试。"
        return content
    
    # 各领域热点
    index = 1
    for category, hotspots in all_hotspots.items():
        if not hotspots:
            continue
        # 领域标签
        color = [c["color"] for c in CATEGORIES if c["name"] == category][0]
        content += f"<font color=\"{color}\">● {category}</font>\n\n"
        # 热点列表
        for hotspot in hotspots:
            content += f"{index}. **[{hotspot['title']}]({hotspot['url']})**\n"
            content += f"> <font color=\"gray\">{hotspot['description']}</font>\n\n"
            index += 1
    
    # 底部说明
    content += "<font color=\"gray\">数据来源：全网公开信息，每日自动推送，异常可手动触发补发</font>"
    return content

def push_to_feishu(content: str) -> bool:
    """推送到飞书群，支持重试"""
    for i in range(RETRY_TIMES + 1):
        try:
            # 飞书webhook推送格式
            payload = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": f"📰 每日行业热点 {datetime.now().strftime('%Y-%m-%d')}",
                            "content": [
                                [{"tag": "text", "text": content}]
                            ]
                        }
                    }
                }
            }
            response = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("code") == 0:
                logger.info("推送成功")
                return True
            logger.error(f"推送失败，返回：{result}")
        except Exception as e:
            logger.error(f"第{i+1}次推送失败：{str(e)}")
        if i < RETRY_TIMES:
            time.sleep(2)
    logger.error("所有重试均失败")
    return False

def run_task(manual_trigger=False):
    """执行完整推送任务"""
    logger.info(f"{'手动触发' if manual_trigger else '定时启动'}热点推送任务")
    
    # 采集所有领域热点
    all_hotspots = {}
    for category in CATEGORIES:
        hotspots = fetch_hotspots(category)
        all_hotspots[category["name"]] = hotspots
        logger.info(f"{category['name']}领域采集到{len(hotspots)}条热点")
    
    # 格式化内容
    content = format_content(all_hotspots)
    
    # 推送
    success = push_to_feishu(content)
    return success, content

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'manual':
        # 手动触发
        success, content = run_task(manual_trigger=True)
        print("推送成功" if success else "推送失败")
        sys.exit(0 if success else 1)
    
    # 定时任务模式
    scheduler = BlockingScheduler(timezone='Asia/Shanghai')
    hour, minute = PUSH_TIME.split(':')
    scheduler.add_job(run_task, 'cron', hour=int(hour), minute=int(minute), id='daily_hotspot_push')
    logger.info(f"定时任务已启动，每日{PUSH_TIME}推送热点")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("定时任务已停止")
