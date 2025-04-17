# SkyMind 智慧城市低空AI平台

基于FastAPI、LangChain、CAMEL.ai框架和YOLOv8目标检测模型，开发的多智能体协同的智慧城市低空AI平台。

## 项目功能

* 实时异常事件检测（YOLO模型）
* 智能路径规划（A*算法或强化学习）
* 异常事件智能响应Agent（LLM模型驱动）
* 多智能体协作系统
* 3D可视化监控界面

## 技术栈

### 后端技术栈
- Python 3.9+
- FastAPI - 高性能API框架
- LangChain - 大语言模型应用框架
- CAMEL.ai - 多智能体通信框架
- YOLOv8 - 实时目标检测
- MongoDB - 数据存储
- Beanie - MongoDB的ODM
- Websockets - 实时通信

### 前端技术栈
- Vue 3 - 前端框架
- Vite - 构建工具
- Pinia - 状态管理
- Vue Router - 路由管理
- Naive UI - UI组件库
- Tailwind CSS - 原子化CSS框架
- Mapbox GL - 地图展示
- deck.gl - 大规模数据可视化
- Three.js - 3D渲染
- Chart.js - 数据图表

## 项目结构

```
skymind/
├── backend/                    # 后端代码
│   ├── main.py                 # FastAPI主入口
│   ├── config/                 # 项目配置
│   ├── database/               # 数据库模型和连接
│   ├── agents/                 # 智能体模块
│   ├── api/                    # API接口
│   ├── core/                   # 核心功能
│   ├── schemas/                # 数据模式
│   ├── services/               # 业务服务
│   └── utils/                  # 工具函数
│
└── frontend/                   # 前端代码
    ├── public/                 # 静态资源
    ├── src/
    │   ├── api/                # API请求
    │   ├── assets/             # 资源文件
    │   ├── components/         # 组件
    │   │   ├── layout/         # 布局组件
    │   │   ├── map/            # 地图组件
    │   │   ├── drones/         # 无人机组件
    │   │   └── emergency/      # 应急组件
    │   ├── router/             # 路由配置
    │   ├── store/              # 状态管理
    │   ├── utils/              # 工具函数
    │   ├── views/              # 页面视图
    │   ├── App.vue             # 根组件
    │   └── main.js             # 入口文件
    ├── package.json            # 项目依赖
    └── vite.config.js          # Vite配置
```

## 如何运行

### 后端

1. 安装依赖
```bash
cd backend
pip install -r requirements.txt #首次启动时需要
```

2. 启动服务
```bash
uvicorn main:app --reload
```

### 前端

1. 安装依赖
```bash
cd frontend
npm install #首次启动时需要
```

2. 开发模式启动
```bash
npm run dev
```

3. 构建生产版本
```bash
npm run build
```

## 多智能体系统

* 监控智能体 - 基于YOLOv8实时检测异常事件
* 路径规划智能体 - 优化无人机飞行路径
* 应急响应智能体 - 分析事件并生成应急方案
* 物流调度智能体 - 协调物资配送和任务分配
* 安防巡检智能体 - 管理安全巡逻路线和事件追踪

## 作者

SkyMind团队 啊aaa