# TRAE 论坛自动化投票与评论工具

基于 Selenium 浏览器自动化的 Discourse 论坛投票与评论工具，支持智能去重、用户黑名单、评论字数控制等功能。

## 功能特性

- **浏览器自动化**：基于 Selenium Edge 浏览器，自动完成登录、投票、评论全流程
- **浏览器复用**：通过 subprocess 启动独立浏览器进程，脚本结束后浏览器继续运行，下次运行自动复用，无需重复登录
- **分页翻页**：自动获取多页帖子，直到达到目标数量或帖子耗尽
- **智能去重**：
  - 已评价记录持久化（`state.json`）
  - 帖子黑名单（`skip_list.json`）
  - 用户黑名单（`user_blacklist.json`）—— 处理完一个用户的帖子后自动将其加入黑名单，避免重复评价
  - 已投票检测 —— 检测到已投票的帖子自动跳过，并将发帖人加入黑名单
- **评论生成**：基于 DeepSeek API 自动生成评论，以"已投票"开头，末尾添加"相互支持"，字数控制在 15-50 字
- **审批弹窗自动处理**：评论发布后自动点击审批确认按钮
- **浏览器保留**：执行完毕后浏览器独立运行，不会自动关闭，下次运行可复用登录态
- **Web 配置页面**：内置本地 Web 配置界面，无需手动编辑 .env 文件，启动后自动打开浏览器

## 项目结构

```
.
├── .env                  # 环境变量配置文件（不上传，请复制 .env.example）
├── .env.example          # 环境变量配置模板
├── requirements.txt      # Python 依赖
│
├── main_browser.py       # 主脚本（浏览器模式，推荐使用）
├── main.py               # 主脚本（API 模式，Cookie 方式，已废弃）
├── config_server.py      # 本地 Web 配置服务
├── config.html           # 配置页面（Web UI）
│
├── comment_generator.py  # 评论生成器（DeepSeek API）
├── config.py             # 配置管理
├── deepseek_client.py    # DeepSeek API 客户端
├── discourse_client.py   # Discourse API 客户端（获取帖子列表）
│
├── state_manager.py      # 已评价记录管理
├── skip_list_manager.py  # 帖子黑名单管理
├── user_blacklist_manager.py  # 用户黑名单管理
│
├── skip_list.json        # 帖子黑名单数据
├── user_blacklist.json   # 用户黑名单数据
└── state.json            # 已评价记录数据
```

## 快速开始

### 1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 2. 配置环境变量

**方式一：Web 配置页面（推荐）**

启动配置服务，浏览器会自动打开配置页面：

```bash
python config_server.py
```

在页面上修改配置后点击保存即可。默认端口为 8888，如需指定端口：

```bash
python config_server.py 9000
```

**方式二：手动编辑 .env 文件**

复制 `.env.example` 为 `.env`，并填写您的配置：

```bash
cp .env.example .env
```

编辑 `.env`：

```ini
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash

# Discourse 论坛配置
DISCOURSE_BASE_URL=https://forum.trae.cn

# 目标分类 URL（大赛初赛专区）
TARGET_CATEGORY_URL=https://forum.trae.cn/c/38-category/40-category/40

# 每次执行最多评论多少条
MAX_COMMENTS_PER_RUN=5
```



### 3. 配置黑名单（可选）

编辑 `skip_list.json` 添加不想评价的帖子 ID：

```json
{
  "skip_topic_ids": [xxxxx]
}
```

编辑 `user_blacklist.json` 添加不想评价的用户名：

```json
{
  "blacklisted_usernames": ["用户xxxxx"]
}
```

> 用户黑名单会自动维护：成功处理一篇帖子后，发帖人自动加入黑名单。

### 4. 运行脚本

```bash
python main_browser.py
```

运行流程：
1. 检测是否有已运行的浏览器（端口 9222）
2. 如果有 → 直接复用，跳过登录
3. 如果没有 → 启动独立浏览器进程，等待 60 秒让您手动登录
4. 登录完成后自动获取帖子列表（支持多页翻页）
5. 遍历帖子，跳过已评价/黑名单/已投票的帖子
6. 对每篇帖子：投票 → 生成评论 → 发表评论 → 点击审批确认
7. 任务完成后脚本退出，浏览器继续运行（下次可复用）

## 配置说明

| 环境变量 | 说明 | 示例 |
|----------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | `sk-...` |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-v4-flash` |
| `DISCOURSE_BASE_URL` | 论坛地址 | `https://forum.trae.cn` |
| `TARGET_CATEGORY_URL` | 目标板块 URL | `https://forum.trae.cn/c/...` |
| `MAX_COMMENTS_PER_RUN` | 单次最大处理数 | `5` |

## 注意事项

- **登录方式**：脚本通过打开浏览器让用户手动登录，无需提供 Cookie
- **浏览器复用**：首次运行后浏览器会继续运行，再次运行脚本时会自动复用已有浏览器，跳过登录步骤
- **edge_profile 目录**：浏览器配置文件存储目录，保存登录态，请勿删除
- **审批机制**：评论发表后需要版主审批，脚本会自动点击确认弹窗
- **去重机制**：帖子 ID 黑名单、用户黑名单、已评价记录、已投票检测四重去重
- **关闭浏览器**：如需关闭，请手动关闭浏览器窗口即可

## 技术栈

- Python 3.8+
- Selenium 4.x
- Edge WebDriver
- DeepSeek API

## 免责声明

本工具仅供学习和参考使用。请遵守目标论坛的使用条款和社区规范，合理使用自动化工具。
