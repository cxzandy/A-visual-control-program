# 🌐 Web控制界面

这个目录包含Tiaozhanbei2.0系统的Web控制界面。

## 📁 目录结构

```
web/
├── web_simple.py          # Flask Web服务器
├── templates/             # HTML模板
│   └── index.html        # 主页面模板
├── static/               # 静态文件目录（CSS、JS、图片）
└── WEB_GUIDE.md          # 详细使用指南
```

## 🚀 快速启动

### 从项目根目录启动

```bash
# 方法1：使用启动脚本（推荐）
./start_web.sh

# 方法2：使用演示脚本
./demo_web.sh

# 方法3：直接运行
conda run -n tiao python web/web_simple.py
```

### 访问地址

- **本地访问**: http://localhost:5000
- **局域网访问**: http://[您的IP地址]:5000

## ✨ 功能特色

- 🎮 **图形化控制** - 点击按钮操作系统
- 📊 **实时监控** - 状态、FPS、检测结果
- 🖼️ **图像显示** - 四象限管道检测可视化
- 📱 **响应式设计** - 支持桌面和移动端
- 📝 **日志记录** - 实时操作和系统日志

## 📚 详细说明

更多详细使用说明请参考 [WEB_GUIDE.md](WEB_GUIDE.md)。
