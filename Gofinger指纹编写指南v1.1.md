# Gofinger 指纹编写指南 (v1.1 - 怀梦版)

## 0. 前言

本指南旨在为安全研究人员和开发人员提供一份关于如何为 Gofinger 工具编写自定义指纹规则的详尽说明。Gofinger 的指纹引擎主要使用 **JSON** 格式，同时支持 **YAML** 格式作为主动识别的补充，提供了多种匹配方法来识别 Web 应用、框架、CMS 等。

本指南的目标是，让任何一位新手在认真阅读后，都能独立编写出高质量的指纹规则。它不仅会告诉你"有什么"，更会教会你"怎么想"、"怎么做"和"如何做得更好"。

**注意**: 本指南主要使用 JSON 格式进行示例，YAML 格式仅作为辅助参考。

---

## 1. 指纹体系概述

Gofinger 的指纹识别体系分为两部分：

1.  **被动识别 (Passive)**: 主要依赖 `finger.json` 文件。此部分规则用于匹配从网络空间测绘平台（如 Fofa, Hunter, Quake）获取的已有数据。本指南的后续章节（如“最佳实践”）中提到的通用匹配规则（`method`, `location`, `keyword`）同样适用于 `finger.json`。
2.  **主动识别 (Active)**: 完全由 `finger.yaml` 文件驱动。当启用主动识别模式时，Gofinger 会加载此文件中的规则，向目标发起真实HTTP请求，并根据响应进行匹配。
3.  指纹文件基础
    - **主要格式**: 默认被动指纹规则主要使用 **JSON** 格式
    - **辅助格式**: 同时支持 YAML 格式作为主动给指纹识别库的补充
    - **文件位置**: 指纹文件位于 `library/` 目录下
    - **文件名称**: `finger.json`（主要）和 `finger.yaml`（辅助）
    - **字符编码**: 文件必须使用 `UTF-8` 编码


---

## 2. 指纹规则核心结构

**一个指纹规则包含以下核心字段：**

| 字段名 | 类型 | 是否必须 | 描述 |
| :--- | :--- | :--- | :--- |
| `cms` | `String` | 是 | 指纹/组件的名称。这是识别成功后最终显示的结果。 |
| `path` | `List<String>`| 是 | **主动识别核心字段**。定义了探测时要访问的URL路径列表。程序会依次请求这些路径，任一路径匹配成功则中止。**（finger.json不需要path字段）** |
| `method` | `String` | 是 | 定义关键词的匹配方法，支持 `keyword`, `keyword_any`, `regex`, `faviconhash`。 |
| `location`| `String` | 否 | 定义关键词的匹配位置，支持 `title`, `body`, `header`。若 `method` 为 `faviconhash`，此字段可省略。 |
| `keyword` | `List<String>`| 是 | 用于匹配的关键词或正则表达式。 |

### 2.1 `method` (匹配方法)

#### 2.1.1 `keyword` - 全匹配

- **逻辑**: 所有关键字都必须同时存在
- **适用场景**: 需要多个特征同时满足的情况
- **示例**: 识别 WordPress 需要同时包含 "wp-content" 和 "wp-includes"

#### 2.1.2 `keyword_any` - 任一匹配

- **逻辑**: 任意一个关键字存在即可
- **适用场景**: 多个特征中满足一个即可的情况
- **示例**: 识别 Drupal 包含 "Drupal" 或 "Drupal 8" 任一即可

#### 2.1.3 `regex` - 正则匹配

- **逻辑**: 使用正则表达式进行匹配
- **要求**: keyword 数组只能包含一个正则表达式
- **适用场景**: 需要复杂模式匹配的情况
- **示例**: 匹配版本号、特定格式的字符串等

#### 2.1.4 `faviconhash` - 图标哈希匹配

- **逻辑**: 匹配网站 favicon 的哈希值
- **要求**: keyword 数组只能包含一个哈希值
- **适用场景**: 通过 favicon 特征识别特定应用
- **示例**: 识别 Nginx、Apache 等服务器的默认图标

### 2.2 支持的匹配位置详解

#### 2.2.1 `body` - 响应正文

- **内容**: HTTP 响应体内容
- **适用场景**: 页面源码中的特征标识
- **示例**: HTML 中的注释、meta 标签、JavaScript 代码等

#### 2.2.2 `header` - 响应头

- **内容**: HTTP 响应头信息
- **适用场景**: 服务器标识、安全头、自定义头等
- **示例**: Server 头、X-Powered-By 头等

#### 2.2.3 `title` - 页面标题

- **内容**: HTML 页面的 `<title>` 标签内容
- **适用场景**: 页面标题中的特征标识
- **示例**: 管理后台标题、错误页面标题等

---

## 3. `指纹库` 编写示例

### 3.1 `keyword` (与逻辑) 指纹规则

**JSON 格式（推荐）:**

```json
    {
      "cms": "Nacos",
      "method": "keyword",
      "location": "body",
      "keyword": [
        "<title>Nacos</title>"
      ]
    },
```

**YAML 格式（主动识别）:**

```yaml
  - cms: "Tomcat默认页面"
    path:
      - "/manager/html"
      - "/manager/status"
    method: "keyword_any"
    location: "body"
    keyword:
      - "<title>Apache Tomcat"
      - 'form method="POST" action="j_security_check"'
      - 'input name="j_username"'
```

**解释:**

1.  **`cms`**: 识别出的组件名为 "Tomcat默认页面"。
2.  **`path`**: 探测路径 `/manager/html`、`/manager/status`。
3.  **`method`**: 使用 `keyword` (与逻辑)。
4.  **`location`**: 在响应的 `body` 中查找。
5.  **`keyword`**: 响应体必须同时包含 `<title>Apache Tomcat`、`form...` 和 `input...` 这三个字符串，才算匹配成功。

### 3.2 `keyword_any` (或逻辑) 指纹规则

**JSON 格式（被动识别）:**

```json
    {
      "cms": "xxl-job-admin",
      "method": "keyword_any",
      "location": "title",
      "keyword": [
        "xxl-job-admin",
        "任务调度中心",
        "XXL-JOB管理平台",
        "XXL-JOB任务调度中心",
        "分布式任务调度平台XXL-JOB"
      ]
```

**YAML 格式（主动识别）:**

```yaml
- cms: "xxl-job-admin"
  path:
    - "/xxl-job-admin/toLogin"
    - "/xxl-job/toLogin"
  method: "keyword_any"
  location: "title"
  keyword:
    - "xxl-job-admin"
    - "任务调度中心"
    - "XXL-JOB管理平台"
```

**解释:**

1.  **`cms`**: 识别出的组件名为 "xxl-job-admin"。
2.  **`path`**: 程序会依次尝试访问 `/xxl-job-admin/toLogin` 和 `/xxl-job/toLogin`。**JSON只请求默认路径，不使用path字段**
3.  **`method`**: 使用 `keyword_any` (或逻辑)。
4.  **`location`**: 在响应的 `<title>` 标签中查找。
5.  **`keyword`**: 只要标题中包含 "xxl-job-admin"、"任务调度中心" 或 "XXL-JOB管理平台" 中任意一个，即判定为匹配成功。

### 3.3 正则匹配指纹规则（带版本号）

**JSON 格式（推荐）:**

```json
{
  "cms": "Joomla",
  "method": "regex",
  "location": "body",
  "keyword": ["Joomla! [0-9]+\\.[0-9]+\\.[0-9]+"]
}
```

**YAML 格式（辅助）:**

```yaml
- cms: "Joomla"
  path:
    - "joomla"
  method: "regex"
  location: "body"
  keyword:
    - "Joomla! [0-9]+\\.[0-9]+\\.[0-9]+"
```

**说明**: 使用正则表达式匹配 Joomla 版本号（如 "Joomla! 3.9.0"）。

### 3.4 图标哈希值指纹规则

**JSON 格式（推荐）:**

```json
{
  "cms": "Nginx",
  "method": "faviconhash",
  "location": "body",  # faviconhash 不依赖 location，可设任意值、不要此字段
  "keyword": ["1234567890"]
}
```

**YAML 格式（辅助）:**

```yaml
- cms: "Nginx"
  path：
    - "/test/favicon.ico"
  method: "faviconhash"
  location: "body"  # faviconhash 不依赖 location，可设任意值、不要此字段
  keyword:
    - "1234567890"  # 替换为实际的 favicon 哈希值
```

**说明**: 匹配 favicon 的哈希值，keyword 只能有一个值。

### 3.5 header 指纹规则

**JSON 格式（推荐）:**

```json
{
  "cms": "Apache",
  "method": "keyword",
  "location": "header",
  "keyword": ["Apache/2", "Server: Apache"]
}
```

**YAML 格式（辅助）:**

```yaml
- cms: "Apache"
  path：
    - "/test"
  method: "keyword"
  location: "header"
  keyword:
    - "Apache/2"
    - "Server: Apache"
```

**说明**: 匹配 HTTP 响应头中同时包含 "Apache/2" 和 "Server: Apache" 的情况。

---

## 4. 指纹规则编写最佳实践

### 4.1 规则设计原则

#### 4.1.1 准确性优先
- **避免误报**: 选择具有唯一性的特征
- **避免漏报**: 考虑不同版本、配置的差异
- **测试验证**: 在多个目标上测试规则的有效性

#### 4.1.2 性能考虑
- **避免复杂正则**: 简单的字符串匹配比复杂正则更快
- **合理使用位置**: 优先使用 `title` 和 `header`，减少 `body` 匹配
- **避免过长内容**: 避免在大型响应体中搜索

#### 4.1.3 可维护性
- **清晰命名**: CMS 名称要准确、规范
- **详细注释**: 在 YAML 文件中添加说明注释
- **版本管理**: 为不同版本的应用编写独立规则

### 4.2 常见错误和避免方法

#### 4.2.1 规则过于宽泛
**错误示例:**
```json
{
  "cms": "PHP",
  "method": "keyword",
  "location": "body",
  "keyword": ["php"]
}
```

**问题**: "php" 字符串过于常见，会导致大量误报

**正确做法:**
```json
{
  "cms": "PHP",
  "method": "keyword",
  "location": "header",
  "keyword": ["X-Powered-By: PHP"]
}
```

#### 4.2.2 正则表达式错误
**错误示例:**
```json
{
  "cms": "WordPress",
  "method": "regex",
  "location": "body",
  "keyword": ["wp-content", "wp-includes"]
}
```

**问题**: regex 方法只能有一个 keyword

**正确做法:**
```json
{
  "cms": "WordPress",
  "method": "keyword",
  "location": "body",
  "keyword": ["wp-content", "wp-includes"]
}
```

#### 4.2.3 位置选择不当
**错误示例:**
```json
{
  "cms": "Apache",
  "method": "keyword",
  "location": "body",
  "keyword": ["Apache"]
}
```

**问题**: 服务器信息通常在 header 中，body 中搜索效率低

**正确做法:**
```json
{
  "cms": "Apache",
  "method": "keyword",
  "location": "header",
  "keyword": ["Server: Apache"]
}
```

### 4.3 高级技巧

#### 4.3.1 多版本支持
```json
[
  {
    "cms": "WordPress",
    "method": "keyword",
    "location": "body",
    "keyword": ["wp-content", "wp-includes"]
  },
  {
    "cms": "WordPress 5.x",
    "method": "keyword",
    "location": "body",
    "keyword": ["wp-content", "wp-includes", "wp-json"]
  }
]
```

#### 4.3.2 组合特征识别
```json
{
  "cms": "WordPress + WooCommerce",
  "method": "keyword",
  "location": "body",
  "keyword": ["wp-content", "woocommerce"]
}
```

#### 4.3.3 错误页面识别
```json
{
  "cms": "Laravel",
  "method": "keyword",
  "location": "title",
  "keyword": ["Laravel", "Error"]
}
```

---

## 5. 指纹规则测试和验证

### 5.1 测试环境准备
1. **本地测试**: 搭建目标应用的本地环境
2. **在线测试**: 使用已知的在线实例进行测试
3. **版本覆盖**: 测试不同版本的同一应用

### 5.2 测试方法
1. **正向测试**: 验证规则能正确识别目标应用
2. **反向测试**: 验证规则不会误报其他应用
3. **边界测试**: 测试特殊字符、编码等情况

### 5.3 性能测试
1. **响应时间**: 确保规则不会显著影响扫描速度
2. **内存使用**: 避免过于复杂的正则表达式
3. **并发测试**: 在高并发情况下测试规则稳定性

---

## 6. 指纹规则管理

### 6.1 文件组织
```
library/
├── finger.json      # 主要指纹库（JSON 格式，推荐）
├── finger.yaml      # 扩展指纹库（YAML 格式，辅助）
```

### 6.2 版本控制
- **规则版本**: 为每个规则添加版本信息
- **更新日志**: 记录规则的修改历史
- **兼容性**: 确保新规则与旧版本兼容

### 6.3 社区贡献
- **规则分享**: 将有效的 规则分享给社区
- **问题反馈**: 及时报告和修复问题
- **文档维护**: 保持文档的准确性和时效性

---

## 7. 匹配方法和位置示例

### 7.1 keyword 方法示例

#### body 位置匹配
```json
{
  "cms": "WordPress",
  "method": "keyword",
  "location": "body",
  "keyword": ["wp-content", "wp-includes"]
}
```

#### header 位置匹配
```json
{
  "cms": "Apache",
  "method": "keyword",
  "location": "header",
  "keyword": ["Server: Apache"]
}
```

#### title 位置匹配
```json
{
  "cms": "Laravel Error",
  "method": "keyword",
  "location": "title",
  "keyword": ["Laravel", "Error"]
}
```

### 7.2 keyword_any 方法示例

```json
{
  "cms": "ThinkPHP",
  "method": "keyword_any",
  "location": "body",
  "keyword": ["ThinkPHP", "thinkphp"]
}
```

### 7.3 regex 方法示例

```json
{
  "cms": "Joomla 版本识别",
  "method": "regex",
  "location": "body",
  "keyword": ["Joomla! [0-9]+\\.[0-9]+\\.[0-9]+"]
}
```

### 7.4 faviconhash 方法示例

```json
{
  "cms": "WordPress Favicon",
  "method": "faviconhash",
  "location": "body",
  "keyword": ["-342124385"]
}
```

---

## 8. 完整JSON文件结构示例

以下是一个完整的 `finger.json` 文件结构示例，展示了如何组织多个指纹规则：

```json
{
  "fingerprint": [
    {
      "cms": "WordPress",
      "method": "keyword",
      "location": "body",
      "keyword": ["wp-content", "wp-includes"]
    },
    {
      "cms": "Apache",
      "method": "keyword",
      "location": "header",
      "keyword": ["Server: Apache"]
    },
    {
      "cms": "Laravel Error",
      "method": "keyword",
      "location": "title",
      "keyword": ["Laravel", "Error"]
    },
    {
      "cms": "ThinkPHP",
      "method": "keyword_any",
      "location": "body",
      "keyword": ["ThinkPHP", "thinkphp"]
    },
    {
      "cms": "Joomla 版本识别",
      "method": "regex",
      "location": "body",
      "keyword": ["Joomla! [0-9]+\\.[0-9]+\\.[0-9]+"]
    },
    {
      "cms": "WordPress Favicon",
      "method": "faviconhash",
      "location": "body",
      "keyword": ["-342124385"]
    }
  ]
}
```

**说明**: 
- 文件以 `fingerprint` 数组开始
- 每个指纹规则都是一个独立的JSON对象
- 所有规则都包含必需的四个字段：`cms`、`method`、`location`、`keyword`
- 展示了四种匹配方法：keyword、keyword_any、regex、faviconhash
- 展示了三种匹配位置：body、header、title
- 可以根据需要添加更多规则

---

## 9. 故障排除

### 9.1 常见问题

#### 规则不生效
- **检查语法**: 确保 JSON 语法正确，注意引号、逗号等
- **验证字段**: 确保所有必需字段都存在
- **测试规则**: 使用简单规则进行测试

#### 误报问题
- **优化特征**: 选择更具唯一性的特征
- **增加条件**: 使用多个关键字组合
- **调整位置**: 尝试不同的匹配位置

#### 性能问题
- **简化规则**: 避免复杂的正则表达式
- **优化位置**: 优先使用 header 和 title
- **减少数量**: 避免过多的关键字

### 9.2 调试技巧

#### 启用调试模式
```bash
./gofinger -ll debug -u http://example.com -a
```

#### 查看匹配过程
- 检查日志输出中的匹配信息
- 验证规则是否正确加载
- 确认目标内容是否符合预期

---

## 10. 总结

Gofinger 的指纹规则编写是一个需要不断学习和优化的过程。通过本指南，你应该能够：

1. **理解指纹规则的基本结构**和各个字段的作用
2. **掌握不同匹配方法**的特点和适用场景
3. **编写高质量的指纹规则**，避免常见错误
4. **测试和验证规则**的有效性和性能
5. **管理和维护指纹库**，确保其准确性和时效性

记住，好的指纹规则应该是：
- **准确的**: 避免误报和漏报
- **高效的**: 不影响扫描性能
- **可维护的**: 易于理解和修改
- **可扩展的**: 支持新应用的快速添加

希望本指南能够帮助你更好地使用 Gofinger 进行 Web 应用指纹识别！

---

## 11. 参考资料

- [Gofinger 项目地址](https://github.com/huaimeng666/gofinger)
- [Chainreactors Fingers 项目](https://github.com/chainreactors/fingers)
- [Web 应用指纹识别技术](https://en.wikipedia.org/wiki/Web_application_firewall)
- [常见 CMS 特征识别](https://www.wappalyzer.com/)

---

*本指南基于 Gofinger v0.6 版本编写，如有更新请参考最新版本。* 