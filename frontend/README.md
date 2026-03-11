# Garmin AI Coach 网页端

这是 Garmin AI Coach 的网页端实现，基于 React + TypeScript + Tailwind CSS 构建，与小程序功能保持一致。

## 功能特点

- 首页概览：显示最近一次跑步、今日准备度、周/月统计和教练简评
- 每日分析：查看详细的训练分析和 AI 建议
- 历史记录：查看过去的训练记录
- 晨间报告：基于睡眠和训练负荷的晨间建议
- 晚间复盘：基于今日训练的晚间复盘和恢复建议
- 周度总结：过去 7 天的训练回顾和下周建议
- 伤病记录：记录和管理伤病情况
- 运动员档案：管理个人训练数据和目标
- AI 对话：与 AI 教练进行对话
- Garmin 绑定：绑定/解绑 Garmin 账号，同步数据

## 技术栈

- React 18
- TypeScript
- Tailwind CSS
- React Router
- Axios
- React Query
- Recharts
- React Markdown

## 安装和运行

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

复制 `.env.example` 文件为 `.env`，并根据需要修改配置：

```bash
cp .env.example .env
```

默认配置：

```
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

开发服务器默认运行在 `http://localhost:5173`。

### 4. 构建生产版本

```bash
npm run build
```

构建结果将输出到 `dist` 目录。

### 5. 预览生产版本

```bash
npm run preview
```

## 项目结构

```
frontend/
├── public/          # 静态资源
├── src/
│   ├── api/         # API 调用
│   ├── components/   # 通用组件
│   ├── hooks/        # 自定义钩子
│   ├── pages/        # 页面组件
│   ├── types/        # 类型定义
│   ├── App.tsx       # 应用入口
│   ├── main.tsx      # 主文件
│   └── index.css     # 全局样式
├── .env.example      # 环境变量示例
├── package.json      # 项目配置
├── tsconfig.json     # TypeScript 配置
└── vite.config.ts    # Vite 配置
```

## 页面说明

### 首页 (`/`)
- 显示最近一次跑步记录
- 显示今日准备度评分
- 显示周/月统计数据
- 显示教练简评
- 提供教练功能入口
- 提供 Garmin 绑定功能

### 分析页 (`/analysis`)
- 显示每日训练分析
- 显示 AI 教练建议
- 支持查看历史日期的分析

### 历史页 (`/history`)
- 显示最近 7 天的训练记录
- 点击可查看对应日期的详细分析

### 晨间报告 (`/morning-report`)
- 基于昨晚睡眠和近期训练负荷的晨间建议
- 显示准备度评分和睡眠摘要

### 晚间复盘 (`/evening-review`)
- 基于今日训练的晚间复盘
- 显示今日活动和恢复指标
- 提供 AI 教练复盘和建议

### 周度总结 (`/weekly-summary`)
- 过去 7 天的训练回顾
- 显示周度统计和训练负荷
- 提供 AI 周度总结和下周建议

### 伤病记录 (`/injury-log`)
- 记录和管理伤病情况
- 支持添加、编辑和标记伤病状态

### 运动员档案 (`/profile`)
- 管理个人训练数据和目标
- 支持同步 Garmin 档案数据

### AI 对话 (`/chat`)
- 与 AI 教练进行对话
- 显示聊天历史记录

## API 接口

网页端使用与小程序相同的 API 接口，主要包括：

- `/api/coach/daily-analysis` - 获取每日分析
- `/api/coach/home-summary` - 获取首页摘要
- `/api/coach/period-analysis` - 获取周期分析
- `/api/coach/morning-report` - 获取晨间报告
- `/api/coach/evening-review` - 获取晚间复盘
- `/api/coach/weekly-summary` - 获取周度总结
- `/api/coach/injury-log` - 管理伤病记录
- `/api/coach/profile` - 管理运动员档案
- `/api/coach/sync-garmin-profile` - 同步 Garmin 档案
- `/api/wechat/bind-garmin` - 绑定 Garmin 账号
- `/api/wechat/unbind-garmin` - 解绑 Garmin 账号
- `/api/wechat/profile` - 获取用户信息
- `/api/wechat/chat` - 与 AI 对话
- `/api/wechat/chat/history` - 获取聊天历史

## 性能优化

- 代码分割：将第三方库拆分为独立的 chunks
- 懒加载：对大型组件进行懒加载
- 缓存策略：使用 React Query 缓存 API 响应
- 响应式设计：适配不同屏幕尺寸

## 维护指南

### 添加新页面

1. 在 `src/pages/` 目录下创建新的页面组件
2. 在 `src/App.tsx` 中添加路由配置
3. 在 `src/components/Layout.tsx` 中添加导航项

### 添加新 API 接口

1. 在 `src/api/coach.ts` 中添加新的 API 调用函数
2. 在相应的页面组件中使用该函数

### 样式修改

- 使用 Tailwind CSS 类进行样式调整
- 如需自定义样式，可在 `src/index.css` 中添加

## 故障排除

### API 连接失败
- 确保后端服务正在运行
- 检查 `.env` 文件中的 `VITE_API_BASE_URL` 配置
- 检查网络连接和 CORS 配置

### 构建失败
- 检查 TypeScript 错误
- 检查依赖是否安装正确
- 检查环境变量配置

### 页面加载缓慢
- 检查网络连接
- 检查后端 API 响应时间
- 考虑优化图片和资源大小

## 部署

1. 构建生产版本：`npm run build`
2. 将 `dist` 目录部署到静态网站托管服务
3. 配置后端 API 地址
4. 确保 CORS 配置正确

## 注意事项

- 网页端与小程序使用相同的后端 API，确保后端服务正常运行
- 绑定 Garmin 账号时，确保输入正确的账号密码
- 中国区用户需要勾选"中国区账号"选项
- 同步 Garmin 数据可能需要一定时间，请耐心等待

## 许可证

MIT License
