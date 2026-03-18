# twikit-cli 使用说明

基于 [twikit](https://github.com/d60/twikit) 构建的 Twitter/X 信息检索命令行工具，无需官方 API Key。

---

## 安装

在项目根目录执行：

```bash
# 推荐：使用 uv（速度更快）
uv venv && uv pip install -e .
source .venv/bin/activate

# 或使用传统 pip（需先创建虚拟环境）
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

安装完成后 `twikit-cli` 命令即可在当前虚拟环境中使用。

> **注意：** 每次新开终端需要重新激活虚拟环境：`source .venv/bin/activate`

---

## 快速开始

```bash
# 第一步：配置认证（二选一）
twikit-cli auth login                      # 用账号密码登录
twikit-cli auth set-cookies cookies.json   # 导入浏览器 cookies

# 第二步：开始检索
twikit-cli search tweets "人工智能"
twikit-cli trends
twikit-cli user info elonmusk
```

---

## 全局选项

所有命令均支持以下选项，写在命令名之后、子命令之前：

```
twikit-cli [全局选项] <命令> [命令选项]
```

| 选项 | 环境变量 | 默认值 | 说明 |
|------|----------|--------|------|
| `--proxy URL` | `TWIKIT_PROXY` | 无 | 代理地址，如 `http://127.0.0.1:7890` |
| `--cookies FILE` | `TWIKIT_COOKIES` | `~/.config/twikit/cookies.json` | cookies 文件路径 |
| `--lang CODE` | — | `en-US` | 语言代码，如 `zh-CN` |
| `--json-output` | — | 关闭 | 输出原始 JSON，便于脚本处理 |
| `--version` | — | — | 显示版本号 |
| `--help` | — | — | 显示帮助 |

**通过环境变量设置代理（推荐）：**

```bash
export TWIKIT_PROXY=http://127.0.0.1:7890
twikit-cli search tweets "OpenAI"
```

---

## auth — 认证管理

### auth login

交互式登录，自动将 cookies 保存到配置目录。

```bash
twikit-cli auth login
```

```
# 提示输入：
Username: your_username
Password: ********
```

**选项：**

| 选项 | 说明 |
|------|------|
| `--username TEXT` | Twitter 用户名 / 邮箱 / 手机号 |
| `--password TEXT` | 密码（不传则交互提示，输入不回显） |
| `--email TEXT` | 二次验证邮箱（Twitter 要求时填写） |

---

### auth set-cookies

从浏览器导出的 cookies 文件中导入认证信息，支持数组格式（EditThisCookie / Cookie-Editor 导出）。

```bash
twikit-cli auth set-cookies ~/Downloads/twitter_cookies.json
```

> cookies 文件将被复制到 `~/.config/twikit/cookies.json`

---

## search — 搜索

### search tweets

按关键词搜索推文。

```bash
twikit-cli search tweets <关键词> [选项]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `QUERY` | 搜索关键词，支持 `#话题`、`@用户`、`"精确短语"` 等语法 |

**选项：**

| 选项 | 可选值 | 默认 | 说明 |
|------|--------|------|------|
| `--type` | `Latest` `Top` `Media` | `Latest` | 搜索类型：最新 / 热门 / 媒体 |
| `--count N` | 整数 | `20` | 返回数量 |

**示例：**

```bash
# 搜索最新推文
twikit-cli search tweets "ChatGPT"

# 搜索热门话题
twikit-cli search tweets "#WorldCup" --type Top

# 只看媒体推文，取 10 条
twikit-cli search tweets "NASA" --type Media --count 10

# 使用代理搜索，输出 JSON
twikit-cli --proxy http://127.0.0.1:7890 --json-output search tweets "AI"
```

**输出列：** 作者 `@handle` · 推文内容 · 日期 · ❤ 点赞 · 🔁 转推 · 💬 回复

---

### search users

按关键词搜索用户。

```bash
twikit-cli search users <关键词> [选项]
```

**选项：**

| 选项 | 默认 | 说明 |
|------|------|------|
| `--count N` | `10` | 返回数量 |

**示例：**

```bash
twikit-cli search users "Elon Musk"
twikit-cli search users "AI researcher" --count 20
```

**输出列：** 显示名 · @handle · 简介 · 粉丝数 · 蓝标认证

---

## user — 用户操作

`@` 前缀可写可不写。

### user info

查看用户主页信息。

```bash
twikit-cli user info <用户名>
```

**示例：**

```bash
twikit-cli user info elonmusk
twikit-cli user info @OpenAI
twikit-cli --json-output user info sama
```

**输出内容：** 显示名 · @handle · 用户 ID · 简介 · 地区 · 注册时间 · 粉丝数 / 关注数 / 推文数 / 点赞数

---

### user tweets

获取用户时间线。

```bash
twikit-cli user tweets <用户名> [选项]
```

**选项：**

| 选项 | 可选值 | 默认 | 说明 |
|------|--------|------|------|
| `--type` | `Tweets` `Replies` `Media` `Likes` | `Tweets` | 时间线类型 |
| `--count N` | 整数 | `20` | 返回数量 |

**示例：**

```bash
# 获取最新推文
twikit-cli user tweets elonmusk

# 获取回复（含对话）
twikit-cli user tweets @OpenAI --type Replies

# 获取媒体推文
twikit-cli user tweets NASA --type Media --count 30

# 获取点赞列表
twikit-cli user tweets sama --type Likes --count 10
```

**输出列：** 日期 · 推文内容 · ❤ 点赞 · 🔁 转推 · 💬 回复

---

### user followers

获取用户的粉丝列表。

```bash
twikit-cli user followers <用户名> [选项]
```

**选项：**

| 选项 | 默认 | 说明 |
|------|------|------|
| `--count N` | `20` | 返回数量 |

**示例：**

```bash
twikit-cli user followers elonmusk --count 50
twikit-cli --json-output user followers @OpenAI
```

**输出列：** 显示名 · @handle · 简介 · 粉丝数

---

## trends — 热门趋势

获取当前热门话题榜单。

```bash
twikit-cli trends [选项]
```

**选项：**

| 选项 | 可选值 | 默认 | 说明 |
|------|--------|------|------|
| `--category` | `trending` `for-you` `news` `sports` `entertainment` | `trending` | 趋势分类 |
| `--count N` | 整数 | `20` | 返回数量 |

**示例：**

```bash
# 全球趋势
twikit-cli trends

# 科技新闻趋势
twikit-cli trends --category news

# 体育热点，前 10 名
twikit-cli trends --category sports --count 10

# 娱乐趋势，输出 JSON
twikit-cli --json-output trends --category entertainment
```

**输出列：** 排名 · 话题名称 · 分类上下文 · 推文量

---

## tweet — 单条推文

### tweet get

通过推文 ID 查看推文详情。

```bash
twikit-cli tweet get <推文ID>
```

**示例：**

```bash
twikit-cli tweet get 1234567890123456789
twikit-cli --json-output tweet get 1234567890123456789
```

**输出内容：** 作者 · 发布时间 · 完整正文 · ❤ 点赞 · 🔁 转推 · 💬 回复 · 🔖 收藏 · 👁 浏览量 · 媒体类型

> 推文 ID 可从推文 URL 中获取：`https://x.com/user/status/`**`1234567890123456789`**

---

## JSON 输出

所有命令加上 `--json-output` 后输出结构化 JSON,方便管道处理：

```bash
# 搜索推文并用 jq 提取正文
twikit-cli --json-output search tweets "Python" | jq '.[].text'

# 获取用户粉丝数
twikit-cli --json-output user info elonmusk | jq '.followers_count'

# 获取趋势话题名列表
twikit-cli --json-output trends --category sports | jq '.[].name'

# 保存结果到文件
twikit-cli --json-output user tweets OpenAI --count 50 > openai_tweets.json
```

### 增强型 JSON 输出 (v2.0+)

从 v2.0 开始，JSON 输出包含更完整的数据结构，支持 AI 智能体和高级数据分析场景。

**新增内容：**
- 完整的作者对象（包含头像、认证状态、粉丝数等）
- 实体提取（hashtags、mentions、URLs 及其位置索引）
- 媒体信息（图片、视频 URL 及元数据）
- 关系追踪（回复、引用、转推关系）
- 高级指标（浏览量、书签数、引用数）
- 文章结构化输出（blocks、markdown、纯文本）

---

### JSON 输出迁移指南

**⚠️ 重要变更**

v2.0 对 JSON 输出格式进行了破坏性更新，以提供更完整的数据结构。

#### 变更 1：`user` → `author`

推文的用户信息字段从 `user` 改为 `author`，且包含完整的用户对象。

**旧格式 (v1.x):**
```json
{
  "id": "123",
  "text": "Hello world",
  "user": {
    "name": "John Doe",
    "screen_name": "johndoe"
  }
}
```

**新格式 (v2.0+):**
```json
{
  "id": "123",
  "text": "Hello world",
  "author": {
    "id": "456",
    "name": "John Doe",
    "screen_name": "johndoe",
    "profile_image_url": "https://...",
    "verified": false,
    "is_blue_verified": true,
    "followers_count": 1000,
    ...
  }
}
```

**迁移方案：**
```bash
# 旧脚本
jq '.[].user.name'

# 新脚本
jq '.[].author.name'

# 兼容方案（同时支持新旧版本）
jq '.[] | (.author // .user).name'
```

#### 变更 2：指标分组到 `metrics` 对象

点赞数、转推数等指标从顶层移到 `metrics` 嵌套对象中。

**旧格式:**
```json
{
  "id": "123",
  "text": "Hello",
  "retweet_count": 100,
  "favorite_count": 500,
  "reply_count": 10
}
```

**新格式:**
```json
{
  "id": "123",
  "text": "Hello",
  "metrics": {
    "retweet_count": 100,
    "favorite_count": 500,
    "reply_count": 10,
    "quote_count": 20,
    "bookmark_count": 50,
    "view_count": 10000
  }
}
```

**迁移方案：**
```bash
# 旧脚本
jq '.[].favorite_count'

# 新脚本
jq '.[].metrics.favorite_count'

# 兼容方案
jq '.[] | (.metrics.favorite_count // .favorite_count)'
```

#### 向后兼容支持

为平滑迁移，v2.0 **临时保留**了旧字段（标记为 DEPRECATED）：
- `user`（指向 `author`）
- `retweet_count`、`favorite_count`、`reply_count`（指向 `metrics.*`）

这些字段将在未来版本中移除，建议尽快迁移到新字段。

---

### 增强型 JSON 架构参考

#### 推文对象 (Tweet)

```json
{
  "id": "1234567890",
  "text": "推文文本（可能被截断）",
  "full_text": "完整推文文本",
  "created_at": "Mon Jan 01 00:00:00 +0000 2024",
  "lang": "zh",

  "author": {
    "id": "123456",
    "name": "显示名",
    "screen_name": "username",
    "description": "用户简介",
    "profile_image_url": "https://...",
    "profile_banner_url": "https://...",
    "followers_count": 1000,
    "following_count": 500,
    "verified": false,
    "is_blue_verified": true,
    "protected": false
  },

  "metrics": {
    "reply_count": 10,
    "retweet_count": 100,
    "favorite_count": 500,
    "quote_count": 20,
    "bookmark_count": 50,
    "view_count": 10000
  },

  "entities": {
    "hashtags": [
      {"text": "AI", "indices": [0, 3]}
    ],
    "urls": [{
      "url": "https://t.co/xxx",
      "expanded_url": "https://example.com",
      "display_url": "example.com",
      "indices": [10, 33]
    }],
    "user_mentions": [{
      "id": "789",
      "name": "Mentioned User",
      "screen_name": "mentioned",
      "indices": [5, 15]
    }]
  },

  "media": [{
    "type": "photo",
    "url": "https://...",
    "media_url_https": "https://...",
    "expanded_url": "https://..."
  }],

  "relationships": {
    "in_reply_to_user_id": null,
    "in_reply_to_status_id": null,
    "quoted_status_id": null,
    "is_quote_status": false,
    "is_retweet": false,
    "retweeted_status_id": null
  },

  "context": {
    "possibly_sensitive": false,
    "place": null
  }
}
```

#### 用户对象 (User)

```json
{
  "id": "123456",
  "name": "显示名",
  "screen_name": "username",
  "description": "用户简介",
  "location": "地理位置",
  "url": "https://example.com",
  "created_at": "Mon Jan 01 00:00:00 +0000 2010",

  "profile_image_url": "https://pbs.twimg.com/profile_images/.../xxx.jpg",
  "profile_banner_url": "https://pbs.twimg.com/profile_banners/.../xxx",

  "followers_count": 1000,
  "following_count": 500,
  "statuses_count": 1234,
  "favourites_count": 5678,

  "verified": false,
  "is_blue_verified": true,
  "protected": false
}
```

#### 文章对象 (Article) - 新增

当推文包含长文章时，使用 `--json-output` 会返回结构化文章数据：

```json
{
  "id": "article_id",
  "title": "文章标题",
  "preview_text": "预览文本...",
  "cover_media_url": "https://...",

  "content": {
    "blocks": [
      {
        "type": "header-one",
        "text": "一级标题"
      },
      {
        "type": "unstyled",
        "text": "段落文本"
      }
    ],
    "markdown": "# 一级标题\n\n段落文本...",
    "plain_text": "一级标题 段落文本..."
  }
}
```

**Block 类型：**
- `header-one`、`header-two`、`header-three` - 标题
- `unstyled` - 普通段落
- `blockquote` - 引用
- `unordered-list-item` - 无序列表项
- `code-block` - 代码块

---

### AI 智能体使用示例

增强型 JSON 输出专为 AI 智能体和数据分析设计，以下是常见使用场景：

#### 1. 提取所有 hashtag 标签

```bash
twikit-cli --json-output search tweets "#AI" | \
  jq '[.[] | .entities.hashtags[].text] | unique | sort'
```

**输出：**
```json
["AI", "MachineLearning", "DeepLearning", "NLP"]
```

#### 2. 构建用户提及关系图

```bash
twikit-cli --json-output search tweets "Python" | \
  jq '.[] | {
    author: .author.screen_name,
    mentions: [.entities.user_mentions[].screen_name]
  }'
```

**输出：**
```json
{"author": "alice", "mentions": ["bob", "charlie"]}
{"author": "dave", "mentions": ["alice"]}
```

用于构建社交网络分析、影响力追踪等。

#### 3. 分析互动率

```bash
twikit-cli --json-output user tweets OpenAI --count 50 | \
  jq '.[] | {
    text: .text[:50],
    engagement: (.metrics.favorite_count + .metrics.retweet_count),
    engagement_rate: (
      (.metrics.favorite_count + .metrics.retweet_count) /
      (.metrics.view_count // 1) * 100 | floor
    )
  } | select(.engagement > 1000)' | \
  jq -s 'sort_by(.engagement) | reverse | .[0:5]'
```

筛选高互动推文，计算互动率。

#### 4. 追踪对话链

```bash
twikit-cli --json-output search tweets "from:elonmusk" | \
  jq '.[] | select(.relationships.in_reply_to_status_id != null) | {
    tweet_id: .id,
    text: .text[:80],
    reply_to: .relationships.in_reply_to_status_id
  }'
```

识别回复关系，重建对话树。

#### 5. 提取文章内容

```bash
twikit-cli --json-output tweet get 1234567890123456789 | \
  jq -r '.content.markdown' > article.md
```

将长文章导出为 Markdown 格式。

#### 6. 批量提取媒体 URL

```bash
twikit-cli --json-output search tweets "NASA" --type Media | \
  jq -r '.[] | .media[]? | .media_url_https' | \
  sort -u > nasa_images.txt

# 下载所有图片
cat nasa_images.txt | xargs -n 1 -P 4 wget -q
```

#### 7. 统计用户认证状态

```bash
twikit-cli --json-output user followers elonmusk --count 100 | \
  jq '{
    total: length,
    blue_verified: [.[] | select(.is_blue_verified)] | length,
    legacy_verified: [.[] | select(.verified)] | length,
    protected: [.[] | select(.protected)] | length
  }'
```

**输出：**
```json
{
  "total": 100,
  "blue_verified": 45,
  "legacy_verified": 12,
  "protected": 3
}
```

#### 8. 检测敏感内容

```bash
twikit-cli --json-output search tweets "news" --count 100 | \
  jq '[.[] | select(.context.possibly_sensitive == true) | {
    id: .id,
    text: .text[:100],
    author: .author.screen_name
  }]'
```

#### 9. 分析发布时间分布

```bash
twikit-cli --json-output user tweets NASA --count 100 | \
  jq -r '.[].created_at' | \
  awk '{print $4}' | \
  cut -d: -f1 | \
  sort | uniq -c | \
  sort -rn
```

统计各小时的发布频率。

#### 10. 导出关注者信息到 CSV

```bash
twikit-cli --json-output user followers OpenAI --count 200 | \
  jq -r '.[] | [
    .id,
    .name,
    .screen_name,
    .followers_count,
    .following_count,
    .is_blue_verified
  ] | @csv' > followers.csv
```

---

## 配置文件

| 路径 | 说明 |
|------|------|
| `~/.config/twikit/cookies.json` | 默认 cookies 存储路径 |

可通过 `--cookies` 选项或 `TWIKIT_COOKIES` 环境变量指定其他路径，适合多账号场景：

```bash
twikit-cli --cookies ~/.config/twikit/account_a.json search tweets "news"
twikit-cli --cookies ~/.config/twikit/account_b.json search tweets "news"
```

---

## 常见问题

**Q: 提示 `No cookies found`**

需要先登录或导入 cookies：

```bash
twikit-cli auth login
# 或
twikit-cli auth set-cookies your_cookies.json
```

**Q: 网络连接超时**

配置代理后重试：

```bash
export TWIKIT_PROXY=http://127.0.0.1:7890
twikit-cli trends
```

**Q: 如何从浏览器导出 cookies？**

推荐使用浏览器扩展：
- Chrome / Edge：[Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/)（Export 选 JSON 格式）
- Firefox：Cookie-Editor 同名扩展

登录 x.com 后，在扩展内点击 Export → JSON，保存文件后执行：

```bash
twikit-cli auth set-cookies ~/Downloads/cookies.json
```

**Q: 输出中文乱码**

```bash
export PYTHONIOENCODING=utf-8
```

---

## 完整命令树

```
twikit-cli
├── --proxy URL
├── --cookies FILE
├── --lang CODE
├── --json-output
│
├── auth
│   ├── login        [--username] [--password] [--email]
│   └── set-cookies  <file>
│
├── search
│   ├── tweets  <query>   [--type Latest|Top|Media] [--count N]
│   └── users   <query>   [--count N]
│
├── user
│   ├── info       <@handle>
│   ├── tweets     <@handle>  [--type Tweets|Replies|Media|Likes] [--count N]
│   └── followers  <@handle>  [--count N]
│
├── trends  [--category trending|for-you|news|sports|entertainment] [--count N]
│
└── tweet
    └── get  <tweet_id>
```
