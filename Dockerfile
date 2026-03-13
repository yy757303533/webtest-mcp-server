# webtest-mcp-server - Python 3.11 + Playwright Chromium
# 支持 macOS (Docker Desktop) / Linux 运行
FROM python:3.11-slim

WORKDIR /app

# Playwright 所需系统依赖（容器内 headless 运行）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# 安装项目
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY projects/ ./projects/
COPY scripts/ ./scripts/
RUN pip install --no-cache-dir -e . && \
    playwright install chromium && \
    playwright install-deps chromium

RUN chmod +x /app/scripts/docker-entrypoint.sh

# 默认启动 MCP 服务
# macOS 上运行登录用例: docker run --rm webtest-mcp-server run-test
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD []
