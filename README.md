# YNU 电费自动查询

本项目会自动登录云南大学一卡通系统并查询宿舍剩余电量。

## 1. 配置方式

只需要修改一个文件：`query_config.json`。

你需要填写：

- `account.name`：账号
- `account.password`：密码
- `query.*`：宿舍定位参数（校区/区域/楼栋/楼层/房间）

统一写入日志文件 `query.log`（追加模式）。

建议按下面顺序改：

1. `query.campusName`（例如：`呈贡`）
2. `query.districtKeyword`（例如：`梓苑1`）
3. `query.buildingKeyword`（例如：`梓1A`）
4. `query.floorName`（例如：`1楼`）
5. `query.roomName`（例如：`A101`）


说明：

- 这些字段是“关键字匹配”，不是必须完整全名。
- 若报“未找到匹配项”，通常是关键字与页面名称不一致，改成更贴近页面显示文本即可。

## 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 3. 首次配置

先复制示例配置，再填写你自己的账号和宿舍信息：

```bash
copy query_config.example.json query_config.json
```

## 4. 运行

```bash
python main.py
```

运行后：

- 终端会继续输出运行日志与查询摘要
- 同一份日志会追加写入 `query.log`
- 每次查询的结构化结果以 `QUERY_RESULT {...}` 记录在日志中


## 5. 常见问题

- 登录失败（账号密码问题）：检查 `account.name` / `account.password`
- 登录失败（验证码问题）：程序会自动重试，连续失败可重跑
- 电费查询失败（匹配项找不到）：检查 `query` 下的关键字配置

## 6. 配置示例（B202）

`query_config.json` 默认就是呈贡校区梓1A栋1楼A101示例，你可以直接替换为自己的宿舍信息。
