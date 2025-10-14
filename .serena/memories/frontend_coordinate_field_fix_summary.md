# 前端坐标字段名修复总结

## 问题描述
前端发送的坐标数据在a_sight表中显示为null，原因是字段名不匹配。

## 问题根源
- 前端发送的数据使用`lng_wgs84`和`lat_wgs84`字段名
- 后端ASight实体类需要`lngWgs84`和`latWgs84`字段名
- 字段名不匹配导致数据无法正确映射

## 解决方案
修改前端`TouristSpotEditModal.vue`中的请求数据格式：

### 修改前
```javascript
lng_wgs84: formData.value.lng_wgs84 ? parseFloat(formData.value.lng_wgs84) : null,
lat_wgs84: formData.value.lat_wgs84 ? parseFloat(formData.value.lat_wgs84) : null,
```

### 修改后
```javascript
lngWgs84: formData.value.lng_wgs84 ? parseFloat(formData.value.lng_wgs84) : null,
latWgs84: formData.value.lat_wgs84 ? parseFloat(formData.value.lat_wgs84) : null,
```

## 修改的文件
- `m_WGP_vue3/src/components/TouristSpotEditModal.vue`

## 预期效果
现在前端发送的数据字段名与后端实体类字段名完全匹配，坐标数据应该能正确保存到数据库中。