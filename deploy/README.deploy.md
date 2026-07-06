# ZKONER 部署方案：Vercel + Railway

## 架构

```
https://zkoner.com ──→ Vercel (Next.js 前端)
                            │
                            │ fetch API calls
                            ▼
https://zkoner-backend.up.railway.app ──→ Railway (FastAPI 后端 + SQLite)
```

---

## 一、Vercel — 部署前端

### 1. 创建项目

1. 打开 [vercel.com](https://vercel.com)，用 GitHub 登录
2. Import 这个仓库，选择 `frontend` 目录（不是根目录，是 `frontend/`）
   - Framework Preset: 自动检测为 **Next.js**
   - Root Directory: `frontend/`

### 2. 环境变量

在 Vercel 项目 Settings → Environment Variables 中添加：

| Name | Value | 说明 |
|------|-------|------|
| `NEXT_PUBLIC_API_URL` | `https://zkoner-backend.up.railway.app/api` | 上线后换成 Railway 的实际 URL |

### 3. 绑定域名

1. Vercel 项目 → Domains → 添加 `zkoner.com`
2. 按照提示，在你的域名 DNS 中添加 CNAME：
   - `www.zkoner.com` → `cname.vercel-dns.com`
   - (如果要用裸域 `zkoner.com`，Vercel 会提供 A 记录 IP)
3. Vercel 自动签发 SSL 证书

### 4. 自动部署

- 每次 push 到 GitHub main 分支，Vercel 自动重新部署
- 可以设置 Preview Deployments 做 PR 预览

---

## 二、Railway — 部署后端

### 1. 创建项目

1. 打开 [railway.app](https://railway.app)，用 GitHub 登录
2. New Project → Deploy from GitHub repo
3. 选择同一个仓库，Root Directory 设为 `backend/`
4. 检测到 `Dockerfile`，自动用 Docker 构建

### 2. 环境变量

在 Railway 项目 Variables 中设置：

| Name | Value | 说明 |
|------|-------|------|
| `AI_ENGINE` | `auto` | 引擎选择 |
| `DEEPSEEK_API_KEY` | `你的key` | (已有) |
| `DOUBAO_API_KEY` | (可选) | 火山引擎 API Key |
| `CLAUDE_API_KEY` | (可选) | Claude API Key（开启语义级评估） |
| `CORS_ORIGINS` | `https://zkoner.com,https://www.zkoner.com` | 允许前端跨域请求 |

### 3. 数据持久化 (SQLite)

Railway 的容器重启后文件会丢失，需要 Volume 保存数据库：

1. Railway 项目 → Volumes → New Volume
2. 名称: `zkoner-data`
3. 挂载路径: `/app/data`
4. 大小: 1GB（免费额度内）

### 4. 获取 API URL

部署完成后，Railway 自动分配一个 `*.railway.app` 域名。
- 在项目 Settings → Networking → Domain 中可以看到
- 例如：`https://zkoner-backend.up.railway.app`
- 把这个 URL 填回 Vercel 的 `NEXT_PUBLIC_API_URL`

### 5. (可选) 配置 api 子域名

如果想用 `api.zkoner.com` 而不是 Railway 域名：

1. Railway → Settings → Domains → Custom Domain
2. 输入 `api.zkoner.com`
3. 在你的 DNS 添加 CNAME：`api.zkoner.com` → Railway 提供的域名

---

## 三、DNS 配置总览

| 记录 | 类型 | 目标 | 用途 |
|------|------|------|------|
| `www.zkoner.com` | CNAME | `cname.vercel-dns.com` | 前端 |
| `zkoner.com` | A | `76.76.21.21` | 裸域 → Vercel |
| `api.zkoner.com` | CNAME | Railway 域名 | (可选) API |

---

## 四、Railway Volume 说明

SQLite 文件存放在 `/app/data/zkoner.db`。
创建 Volume 时 Mount Path 填 `/app/data`，
分析结果和历史数据就会持久化保存。

如果 **不配置 Volume**，每次 Railway 容器重启数据会丢失。

---

## 五、成本汇总

| 项目 | 费用 | 说明 |
|------|------|------|
| 域名 | ~$10/年 | zkoner.com |
| Vercel | $0 | Hobby 计划完全够用 |
| Railway | $0-5/月 | Starter 计划 $5 额度，500 小时/月运行时间 |
| **合计** | **< $15/年 + $0-5/月** | |

---

## 六、验证

部署完成后：

```bash
# 检查后端
curl https://zkoner-backend.up.railway.app/api/health
# → {"status":"ok","version":"0.1.0"}

# 打开浏览器访问
open https://zkoner.com
```
