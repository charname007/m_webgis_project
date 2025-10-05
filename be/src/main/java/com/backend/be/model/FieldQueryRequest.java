package com.backend.be.model;

import java.util.Map;

/**
 * 字段查询请求模型
 * 用于查询指定表的指定字段匹配的要素
 */
public class FieldQueryRequest {
    
    private String tableName;
    private Map<String, Object> fieldConditions;
    
    // 默认构造函数
    public FieldQueryRequest() {
    }
    
    // 带参数的构造函数
    public FieldQueryRequest(String tableName, Map<String, Object> fieldConditions) {
        this.tableName = tableName;
        this.fieldConditions = fieldConditions;
    }
    
    // Getter 和 Setter 方法
    public String getTableName() {
        return tableName;
    }
    
    public void setTableName(String tableName) {
        this.tableName = tableName;
    }
    
    public Map<String, Object> getFieldConditions() {
        return fieldConditions;
    }
    
    public void setFieldConditions(Map<String, Object> fieldConditions) {
        this.fieldConditions = fieldConditions;
    }
    
    /**
     * 验证请求是否有效
     * @return true 如果请求有效
     */
    public boolean isValid() {
        return tableName != null && !tableName.trim().isEmpty() 
                && fieldConditions != null && !fieldConditions.isEmpty();
    }
    
    /**
     * 获取查询条件描述
     * @return 查询条件字符串
     */
    public String getQueryDescription() {
        StringBuilder sb = new StringBuilder();
        sb.append("表名: ").append(tableName).append(", 查询条件: ");
        if (fieldConditions != null && !fieldConditions.isEmpty()) {
            fieldConditions.forEach((key, value) -> {
                sb.append(key).append("=").append(value).append("; ");
            });
        } else {
            sb.append("无");
        }
        return sb.toString();
    }
    
    @Override
    public String toString() {
        return "FieldQueryRequest{" +
                "tableName='" + tableName + '\'' +
                ", fieldConditions=" + fieldConditions +
                '}';
    }
}
