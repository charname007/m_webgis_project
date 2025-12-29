package com.backend.be.model;

/**
 * 要素详情查询请求模型
 * 用于查询空间要素的详细信息，包括属性数据和图片链接
 */
public class FeatureDetailRequest {
    
    private String tableName;
    private String featureId;
    private String[] fields;
    private String[] imageFields;

    // 默认构造函数
    public FeatureDetailRequest() {
    }

    // 带参数的构造函数
    public FeatureDetailRequest(String tableName, String featureId) {
        this.tableName = tableName;
        this.featureId = featureId;
    }

    // Getter 和 Setter 方法
    public String getTableName() {
        return tableName;
    }

    public void setTableName(String tableName) {
        this.tableName = tableName;
    }

    public String getFeatureId() {
        return featureId;
    }

    public void setFeatureId(String featureId) {
        this.featureId = featureId;
    }

    public String[] getFields() {
        return fields;
    }

    public void setFields(String[] fields) {
        this.fields = fields;
    }

    public String[] getImageFields() {
        return imageFields;
    }

    public void setImageFields(String[] imageFields) {
        this.imageFields = imageFields;
    }

    /**
     * 验证请求参数是否有效
     * @return true 如果参数有效
     */
    public boolean isValid() {
        return tableName != null && !tableName.trim().isEmpty() 
                && featureId != null && !featureId.trim().isEmpty();
    }

    @Override
    public String toString() {
        return "FeatureDetailRequest{" +
                "tableName='" + tableName + '\'' +
                ", featureId='" + featureId + '\'' +
                '}';
    }
}
