# 微信公众号文章内容提取工具
绕过微信公众平台反爬限制，输入文章链接即可提取完整文本内容，支持命令行调用和Web接口两种使用方式。

## 特性
✅ 绕过反爬：使用真实浏览器内核模拟访问，规避微信反爬拦截
✅ 结构化输出：自动提取标题、作者、发布时间、正文内容
✅ 两种使用模式：命令行本地调用 / Web接口服务化部署
✅ 高性能：浏览器上下文复用，无需重复启动浏览器进程
✅ 低资源消耗：禁用图片/样式等无关资源加载，解析速度快

## 安装步骤
1. 安装Python依赖
```bash
pip install -r requirements.txt
```

2. 安装Playwright浏览器依赖
```bash
playwright install chromium
playwright install-deps chromium
```

## 使用方式

### 1. 命令行模式（本地使用）
直接输入文章链接，输出解析结果：
```bash
python wechat_parser.py "https://mp.weixin.qq.com/s/xxxxxxx"
```

指定输出文件保存结果：
```bash
python wechat_parser.py "https://mp.weixin.qq.com/s/xxxxxxx" -o article.txt
```

### 2. Web接口模式（服务化部署）
启动服务（默认端口9001）：
```bash
python wechat_parser.py serve
```

调用接口：
```bash
curl -X POST http://localhost:9001/parse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://mp.weixin.qq.com/s/xxxxxxx"}'
```

返回格式：
```json
{
  "success": true,
  "data": {
    "title": "文章标题",
    "author": "公众号名称",
    "publish_time": "2024-03-13",
    "content": "正文内容",
    "original_url": "原文链接"
  }
}
```

## 部署到服务器
### 后台启动服务
```bash
nohup python wechat_parser.py serve > /var/log/wechat-parser.log 2>&1 &
```

### 服务访问地址
http://115.190.182.67:9001/parse

## 注意事项
1. 仅支持公开可访问的微信公众号文章，需要登录/付费阅读的文章无法解析
2. 微信文章链接具有时效性，过期链接会无法访问
3. 单IP短时间大量请求可能触发微信验证码限制，建议控制请求频率不超过1次/秒
