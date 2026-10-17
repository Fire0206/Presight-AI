<div align="center">
  <img src="assets/presight-mark.svg" alt="知几标识" width="68" height="68" />
  <h1>知几 Presight</h1>
  <p><strong>基金、股票和市场资讯，放在一个工作台里。</strong></p>
  <p><a href="https://presight.cloud"><strong>访问知几 Presight：presight.cloud →</strong></a></p>
</div>

知几是一款面向个人投资者的市场研究工具。你可以查看基金和股票行情、记录持仓与自选、跟踪市场热点，也可以创建符合自己研究习惯的智能体，结合实时行情、新闻和个人资料进行分析。

## 产品页面

### 基金中心

查看主要指数、基金板块和基金行情，也可以搜索基金、查看自选。

![基金中心：指数、板块与基金行情](assets/fund-center.png)

### 股票中心

搜索股票，查看价格、交易指标和 K 线，并将关注的股票加入自选。

![股票中心：股票行情与 K 线图](assets/stock-center.png)

### 市场热点

浏览新闻、行业主题和相关公司，继续查看热点可能影响的市场方向。

![市场热点：新闻、主题和相关市场信息](assets/market-hotspots.png)

### 智能体中心

创建不同用途的智能体，为它们选择知识资料和 Skills，并设置各自的回答风格。

![智能体中心：智能体、知识库与 Skills 配置](assets/agent-center.png)

截图展示产品的实际页面。行情、新闻和界面内容会随时间变化；持仓示例来自新用户教程，不代表真实账户或投资建议。

## 主要功能

- **基金与股票**：搜索行情、管理持仓和自选，查看走势及相关指标。
- **市场热点**：集中浏览新闻与行业主题，查看相关标的和事件信息。
- **专属智能体**：按研究目标创建智能体，设置回答风格、知识资料和可用 Skills。
- **个人资料检索**：上传 PDF、Word、图片等资料，在对话中查询和总结。
- **对话记忆**：保存用户选择的偏好，让后续交流更贴合个人习惯。
- **多端使用**：适配电脑和手机，也提供 Android 应用内测版本。

## 技术栈

- **前端**：Vue 3、TypeScript、Vite、Pinia、Vue Router、Tailwind CSS、ECharts
- **移动端**：Capacitor、Android
- **后端**：Python、FastAPI、SQLAlchemy（异步）、PostgreSQL、Alembic
- **资料处理与网络请求**：MarkItDown、Pillow、HTTPX

## 仓库内容

这里公开了可以独立阅读和复用的前端组件、数据格式化示例，以及智能体配置和工具接口的样例：

- [`examples/components/WorkspacePageTitle.vue`](examples/components/WorkspacePageTitle.vue)：Vue 页面标题组件
- [`examples/format-market-data.mjs`](examples/format-market-data.mjs)：金额与涨跌幅格式化函数
- [`examples/agent-profile.example.json`](examples/agent-profile.example.json)：智能体配置示例
- [`examples/tool-contracts.example.json`](examples/tool-contracts.example.json)：工具输入与输出示例
- [`docs/architecture.md`](docs/architecture.md)：产品模块关系与设计说明

示例不连接线上服务。生产环境的账户、模型调用、市场数据接入、数据库和管理服务仍由线上系统负责；仓库不会包含生产密钥、用户资料或生产配置。

## 本地运行示例测试

格式化函数使用 Node.js 内置测试，无需安装第三方依赖：

```bash
npm test
```

## 许可范围

MIT 许可适用于本仓库公开的代码示例与文档。知几 / Presight 名称、标识、产品截图及其他品牌素材不包含在该许可范围内。

市场信息仅供参考，不构成投资建议。欢迎通过 GitHub Issues 反馈公开示例或产品体验问题；请勿提交账户信息、个人持仓、访问令牌或安全漏洞细节。
