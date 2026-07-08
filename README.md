# TRAE 论坛自动化投票与评论工具

基于 Selenium 浏览器自动化的 Discourse 论坛投票与评论工具，支持智能去重、用户黑名单、评论字数控制等功能。

## 功能特性

- **浏览器自动化**：基于 Selenium Edge 浏览器，自动完成登录、投票、评论全流程
- **智能去重**：
  - 已评价记录持久化（`state.json`）
  - 帖子黑名单（`skip_list.json`）
  - 用户黑名单（`user_blacklist.json`）—— 处理完一个用户的帖子后自动将其加入黑名单，避免重复评价
  - 已投票检测 —— 检测到已投票的帖子自动跳过
- **评论生成**：基于 DeepSeek API 自动生成评论，以"已投票"开头，字数控制在 15-50 字
- **审批弹窗自动处理**：评论发布后自动点击审批确认按钮
- **浏览器保留**：执行完毕后保留浏览器窗口，无需重复登录

## 项目结构

```
.
├── .env                  # 环境变量配置文件（不上传，请复制 .env.example）
├── .env.example          # 环境变量配置模板
├── requirements.txt      # Python 依赖
│
├── main_browser.py       # 主脚本（浏览器模式，推荐使用）
├── main.py               # 主脚本（API 模式，Cookie 方式，已废弃）
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
1. 自动打开 Edge 浏览器
2. 访问论坛页面，**等待 60 秒让您手动登录**
3. 登录完成后自动获取帖子列表
4. 遍历帖子，跳过已评价/黑名单/已投票的帖子
5. 对每篇帖子：投票 → 生成评论 → 发表评论 → 点击审批确认
6. 任务完成后浏览器保持打开（按回车键关闭）

## 配置说明

| 环境变量 | 说明 | 示例 |
|----------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | `sk-...` |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-v4-flash` |
| `TARGET_CATEGORY_URL` | 目标板块 URL | `https://forum.trae.cn/c/...` |
| `MAX_COMMENTS_PER_RUN` | 单次最大处理数 | `5` |

## 注意事项

- **登录方式**：脚本通过打开浏览器让用户手动登录，无需提供 Cookie
- **审批机制**：评论发表后需要版主审批，脚本会自动点击确认弹窗
- **浏览器保留**：执行完毕后浏览器不会自动关闭，方便下次运行
- **去重机制**：帖子 ID 黑名单、用户黑名单、已评价记录三重去重

## 技术栈

- Python 3.8+
- Selenium 4.x
- Edge WebDriver
- DeepSeek API

## 免责声明

本工具仅供学习和参考使用。请遵守目标论坛的使用条款和社区规范，合理使用自动化工具。
