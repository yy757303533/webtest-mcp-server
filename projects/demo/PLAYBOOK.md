# demo 项目测试说明

- **用途**: 示例项目，使用 [the-internet.herokuapp.com](https://the-internet.herokuapp.com)
- **模块**: 登录(smoke)
- **用例文件**:
  - `smoke_cases.xlsx` - 冒烟（无需外网，data URL）
  - `login_cases.xlsx` - 登录流程（需访问 the-internet.herokuapp.com）
  - `cases.xlsx` - 其他用例
- **注意**: 登录用例需外网；冒烟用例无需外网，适合 CI 验证
