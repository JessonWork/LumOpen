# 国内搜索代理服务
将原Brave Search API无缝替换为字节跳动Doubao搜索API，100%兼容原有调用接口，上层业务无需修改任何代码，国内服务器可直接访问无网络限制。

## 特性
✅ 完全兼容Brave API请求参数、返回格式，上层业务零修改
✅ 基于字节跳动Doubao搜索服务，国内访问稳定无超时，内容更贴合中文场景
✅ 低延迟，平均响应时间<1s
✅ 支持原有所有搜索参数：q(关键词)、count(返回数量)、offset(分页偏移)、country(地区)等

## 部署步骤
1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 环境变量配置（已默认继承系统ARK_API_KEY，无需额外配置）
```bash
# 已使用系统内置的ARK_API_KEY（和豆包大模型共用密钥）
# 如需单独配置，可在.env文件中添加：
# ARK_API_KEY=你的豆包API密钥
```

3. 启动服务
```bash
# 前台启动
python app.py

# 后台持久化运行
nohup python app.py > /var/log/search-proxy.log 2>&1 &
```

## 使用方式
### 完全兼容原有Brave API调用，仅需修改请求域名即可：
原Brave调用地址：`https://api.search.brave.com/res/v1/web/search?q=xxx&count=10`
替换为新地址：`http://127.0.0.1:8300/res/v1/web/search?q=xxx&count=10`

### 调用示例
```bash
curl "http://127.0.0.1:8300/res/v1/web/search?q=今天北京天气&count=5"
```

### 返回格式（和Brave API完全一致）
```json
{
  "type": "search",
  "web": {
    "results": [
      {
        "title": "北京天气_今日_明天_一周_15天",
        "url": "https://xxx.com/beijing",
        "description": "北京今日天气：晴，10~22℃，微风...",
        "page_age": "2026-03-13",
        "site": "中国天气网"
      }
    ],
    "total": 5
  },
  "query": {
    "original": "今天北京天气",
    "show_query": "今天北京天气"
  }
}
```

## 服务配置
- 监听端口：8300
- 内部访问地址：`http://127.0.0.1:8300`
- 外部访问地址：`http://115.190.182.67:8300`
