# 海外痛点挖掘与微型资产定义专家

基于 Christal.Z 心法的全自动痛点挖掘系统，从 Reddit、ProductHunt 抓取原生数据，筛选商业价值痛点并定义微型软件资产。

## 功能特性

- ✅ 五大黄金信号检测（愿付标签、崩溃标签、寻找标签、抱团信号）
- ✅ 自动噪声过滤
- ✅ 微型资产定义（MVP 生成、定价策略、引流钩子）
- ✅ 极简 Web 界面
- ✅ RESTful API

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 Reddit API 密钥
```

### 3. 启动服务

```bash
python main.py
```

访问 http://localhost:8000 即可使用。

## 技术栈

- Python 3.8+
- FastAPI（后端 API）
- 原生 JavaScript + HTML/CSS（前端）
- PRAW（Reddit API）

## 项目结构

```
/workspace
├── main.py              # FastAPI 主程序入口
├── scraper.py           # Reddit/ProductHunt 数据抓取模块
├── analyzer.py          # 痛点分析和黄金信号检测模块
├── config.py            # 配置文件
├── requirements.txt     # 依赖列表
├── .env.example         # 环境变量模板
└── static/
    └── index.html       # 极简 Web 界面
```
