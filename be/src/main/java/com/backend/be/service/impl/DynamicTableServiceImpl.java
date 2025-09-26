package com.backend.be.service.impl;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.backend.be.mapper.DynamicTableMapper;
import com.backend.be.model.SpatialTableRequest;
import com.backend.be.service.DynamicTableService;

@Service
public class DynamicTableServiceImpl implements DynamicTableService {

    @Autowired
    private DynamicTableMapper tableMapper;

    @Override
    public List<String> getAllTableNames() {
        return tableMapper.getAllTableNames();
    }

    @Override
    public List<Map<String, Object>> getTableData(String tableName) {
        validateTableName(tableName);
        return tableMapper.getTableData(tableName);
    }

    @Override
    public List<Map<String, Object>> getTableSchema(String tableName) {
        validateTableName(tableName);
        return tableMapper.getTableSchema(tableName);
    }

    private void validateTableName(String tableName) {
        if (!tableName.matches("^[a-zA-Z_][a-zA-Z0-9_]*$")) {
            throw new IllegalArgumentException("无效的表名: " + tableName);
        }
        if (!tableMapper.tableExists(tableName)) {
            throw new IllegalArgumentException("表不存在: " + tableName);
        }
    }
    @Override
    public List<String> getSpatialTables() {
        // TODO Auto-generated method stub
        // throw new UnsupportedOperationException("Unimplemented method 'getSpatialTables'");
        return tableMapper.getSpatialTables();
    }

    public String getSpatialTableGeojson(String tableName) {
        // TODO Auto-generated method stub
        // throw new UnsupportedOperationException("Unimplemented method 'getSpatialTableGeojson'");
        return tableMapper.getSpatialTableGeojson(tableName);
    }

    @Override
    public String getSpatialTablesGeojson(SpatialTableRequest request) {
        // 如果表名为"all"或为空，则查询所有空间表
        if ("all".equals(request.getTable()) || request.getTable() == null || request.getTable().isEmpty()) {
            // 获取所有空间表名
            List<String> spatialTables = tableMapper.getSpatialTables();
            StringBuilder combinedGeoJSON = new StringBuilder();
            combinedGeoJSON.append("{\"type\":\"FeatureCollection\",\"features\":[");
            
            boolean firstTable = true;
            for (String tableName : spatialTables) {
                try {
                    // 为每个表创建查询请求
                    SpatialTableRequest tableRequest = new SpatialTableRequest();
                    tableRequest.setTable(tableName);
                    tableRequest.setName(request.getName());
                    tableRequest.setCategories(request.getCategories());
                    tableRequest.setGeom(request.getGeom());
                    
                    // 直接调用Mapper的方法，但使用不同的逻辑避免递归
                    // 这里我们直接调用Mapper的单个表查询方法（不带查询条件）
                    String tableGeoJSON = tableMapper.getSpatialTableGeojson(tableName);
                    
                    // 调试信息
                    System.out.println("表 " + tableName + " 的GeoJSON长度: " + (tableGeoJSON != null ? tableGeoJSON.length() : 0));
                    if (tableGeoJSON != null && !tableGeoJSON.isEmpty()) {
                        System.out.println("表 " + tableName + " 的GeoJSON内容: " + tableGeoJSON.substring(0, Math.min(200, tableGeoJSON.length())));
                    }
                    
                    // 解析GeoJSON并提取features
                    if (tableGeoJSON != null && !tableGeoJSON.isEmpty()) {
                        // 简单的JSON解析来提取features数组
                        String featuresPart = extractFeaturesFromGeoJSON(tableGeoJSON);
                        System.out.println("表 " + tableName + " 提取的features长度: " + (featuresPart != null ? featuresPart.length() : 0));
                        if (featuresPart != null && !featuresPart.isEmpty()) {
                            // 确保featuresPart是有效的JSON数组内容
                            if (featuresPart.startsWith("[")) {
                                featuresPart = featuresPart.substring(1);
                            }
                            if (featuresPart.endsWith("]")) {
                                featuresPart = featuresPart.substring(0, featuresPart.length() - 1);
                            }
                            
                            if (!firstTable && !featuresPart.isEmpty()) {
                                combinedGeoJSON.append(",");
                            }
                            if (!featuresPart.isEmpty()) {
                                combinedGeoJSON.append(featuresPart);
                                firstTable = false;
                            }
                        }
                    }
                } catch (Exception e) {
                    // 忽略单个表的错误，继续处理其他表
                    System.err.println("查询表 " + tableName + " 时出错: " + e.getMessage());
                    e.printStackTrace();
                }
            }
            
            combinedGeoJSON.append("]}");
            return combinedGeoJSON.toString();
        } else {
            // 正常查询单个表
            return tableMapper.getSpatialTablesGeojson(request);
        }
    }
    
    private String extractFeaturesFromGeoJSON(String geoJSON) {
        try {
            // 简单的字符串处理来提取features数组
            // 查找 "features": [ 或 "features":[
            int featuresStart = geoJSON.indexOf("\"features\": [");
            if (featuresStart == -1) {
                featuresStart = geoJSON.indexOf("\"features\":[");
            }
            
            if (featuresStart == -1) {
                System.out.println("未找到features数组");
                return "";
            }
            
            // 跳过 "features": [ 或 "features":[
            if (geoJSON.charAt(featuresStart + 11) == ' ') {
                featuresStart += 12; // 跳过 "\"features\": ["
            } else {
                featuresStart += 11; // 跳过 "\"features\":["
            }
            
            int featuresEnd = geoJSON.lastIndexOf("]");
            if (featuresEnd <= featuresStart) {
                System.out.println("features结束位置不正确");
                return "";
            }
            
            String features = geoJSON.substring(featuresStart, featuresEnd);
            System.out.println("提取的features内容: " + features.substring(0, Math.min(100, features.length())));
            return features;
        } catch (Exception e) {
            System.out.println("提取features时出错: " + e.getMessage());
            return "";
        }
    }
}
