# ScienceDirect 论文访问助手

## 项目简介
这是一个用于自动化访问 ScienceDirect 论文的 Python 插件。通过上海交通大学的教育账号，实现自动登录和内容抓取功能。

## 安全说明
1. 账户安全
   - 请勿在代码中硬编码账号密码
   - 使用 .env 文件存储敏感信息
   - 确保 .env 文件已添加到 .gitignore
   - 定期更改密码
   - 使用强密码（至少8位）

2. 访问安全
   - 支持手动处理人机验证
   - 使用随机化的浏览器指纹
   - 自动化行为模拟真实用户
   - 遵守网站使用条款
   - 合理控制访问频率

## 技术栈
- Python 3.8+
- Selenium 4.15.2
- BeautifulSoup4 4.12.2
- Edge WebDriver

## 依赖库
- selenium==4.15.2
- python-dotenv==1.0.0
- webdriver-manager==4.0.1
- beautifulsoup4==4.12.2
- requests==2.31.0
- fake-useragent==1.3.0

## 功能模块
1. 登录模块 (已完成)
   - 自动化登录流程
   - Cookie 管理
   - 异常处理
   - 人机验证处理
   - 账户安全验证

2. 内容获取模块 (已完成)
   - 论文内容抓取
   - 数据解析
   - 反爬虫处理
   - 自动重试机制
   - Cookie 有效性验证

3. 安全模块 (已完成)
   - 凭据安全管理
   - 浏览器指纹随机化
   - 访问行为模拟
   - 异常处理机制
   - 日志记录与监控

4. 错误处理模块 (已完成)
   - 异常日志记录
   - 自动重试机制
   - 错误恢复策略
   - 调试信息保存

## 新增功能
- 添加代理IP支持
- 实现重试机制（指数退避策略）
- 添加单元测试
- 优化错误处理
- Edge WebDriver 自动管理

## 使用说明
1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
创建 .env 文件，添加以下内容：
```
SJTU_USERNAME=你的交大邮箱
SJTU_PASSWORD=你的交大密码（至少8位）
PROXY_API_=你的代理供应商API
```

3. 运行测试：
```bash
python -m unittest test_sciencedirect_accessor.py
```

## 开发进度
- [x] 基础框架搭建
- [x] 登录模块完成
- [x] 内容抓取模块完成
- [ ] 代理管理模块开发中
- [ ] 错误处理优化中
- [ ] 单元测试完善中

## 注意事项
1. 请确保已安装最新版本的 Microsoft Edge 浏览器
2. 需要稳定的网络连接
3. 当出现人机验证时，需要手动完成验证
4. 请勿频繁访问以避免触发反爬虫机制
5. 定期检查并更新账户密码

## 更新日志
### 2024-02-07
- 增加了账户安全验证机制
- 添加了浏览器指纹随机化
- 优化了人机验证处理流程
- 改进了错误处理和日志记录
- 更新了依赖库版本

## 使用代理
要使用代理功能，请在 .env 文件中添加您的代理供应商API：