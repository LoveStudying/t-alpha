# AmazingData SDK 安装说明

`/api/v1/market/stock/prices` 依赖 `AmazingData` 和 `tgw` 两个 SDK 包。它们不在公开 PyPI 源中，不能只在 `backend/` 下执行 `python -m pip install -e ".[dev]"`。

## 安装步骤

在项目根目录激活虚拟环境后执行：

```powershell
git clone --depth 1 https://gitee.com/cgs2026/xysz.git $env:TEMP\xysz-sdk
python -m pip install "$env:TEMP\xysz-sdk\xysz\xysz_tools\tgw-1.0.8.7-py3-none-any.whl"
python -m pip install "$env:TEMP\xysz-sdk\xysz\xysz_tools\AmazingData\AmazingData-1.1.8-cp311-none-any.whl"
```

本项目当前使用 Python 3.11，因此应安装 `cp311` wheel。如果后续换成 Python 3.12/3.13，需要改成同目录下对应的 `cp312`/`cp313` wheel。

## 验证

```powershell
python -c "import AmazingData, tgw; print('AmazingData SDK ok')"
python -m pip show AmazingData tgw
```

如果导入成功，再确认 `backend/.env` 中已有：

```env
AD_USERNAME=your_amazingdata_username
AD_PASSWORD=your_amazingdata_password
AD_HOST=your_amazingdata_host
AD_PORT=8600
```

缺少 SDK 时，接口会在 `import AmazingData as ad` 处失败并返回 500；缺少或错误的账号、服务器、端口配置时，才会进入 AmazingData 登录或连接错误。

## Docker 部署

`backend/Dockerfile` 会在构建阶段从 SDK 仓库安装 `tgw` 和 `AmazingData` wheel，然后再安装本项目代码。账号密码和服务器地址不要写进镜像，运行容器时从 `backend/.env` 注入：

```powershell
docker build -t t-alpha backend
docker run --rm -p 8867:8867 --env-file backend\.env t-alpha
```

如果需要持久化 AmazingData 本地缓存，可以把容器内缓存目录挂载到宿主机目录，并在 `backend/.env` 中把 `AMAZINGDATA_LOCAL_PATH` 设置成容器内路径：

```powershell
docker run --rm -p 8867:8867 --env-file backend\.env -v D:\AmazingData_local_data:/data/amazingdata t-alpha
```

```env
AMAZINGDATA_LOCAL_PATH=/data/amazingdata
```
