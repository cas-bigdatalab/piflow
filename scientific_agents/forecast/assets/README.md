# 报告位置地图资源

- `china.geojson`：阿里云 DataV GeoAtlas 中国省级底图原始数据，保留全部 35 个要素（含岛屿相关要素），未简化边界。
- 来源：https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json
- 本次保存 SHA256：`99adfeded5223848bbe37a0a12f8023e11ee12161c7800521c27db42fdeac275`。
- DataV 地图坐标说明：https://help.aliyun.com/en/datav/datav-7-0/user-guide/map-data-format-1 。绘图按 GCJ02 底图处理，WGS84/BD09 台站坐标仅在绘图时转换，不改配置或结果中的原始坐标。仅供全国范围位置示意，不作测量使用。
- 坐标换算参考 MIT 项目 https://github.com/wandergis/coordtransform ，许可保存在 `coordtransform-LICENSE.txt`。换算仅用于地图，未引入运行时网络请求或额外依赖。

部署时连同 `assets` 目录发布。报告保存 `location_N.png`，HTML 与 PDF 使用同一张图；底图不在每次生成报告时联网下载。主图和南海诸岛附图使用相同数据。
