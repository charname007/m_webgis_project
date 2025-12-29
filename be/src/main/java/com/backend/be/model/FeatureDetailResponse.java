package com.backend.be.model;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 要素详情查询响应模型
 * 包含空间要素的详细信息，包括属性数据和图片链接
 */
public class FeatureDetailResponse {
    
    private String tableName;
    private String featureId;
    private Map<String, Object> attributes;
    private List<String> imageUrls;
    private boolean success;
    private String message;

    // 默认构造函数
    public FeatureDetailResponse() {
        this.attributes = new HashMap<>();
        this.success = true;
    }

    // 成功响应的构造函数
    public FeatureDetailResponse(String tableName, String featureId, Map<String, Object> attributes, List<String> imageUrls) {
        this.tableName = tableName;
        this.featureId = featureId;
        this.attributes = attributes != null ? attributes : new HashMap<>();
        this.imageUrls = imageUrls;
        this.success = true;
        this.message = "查询成功";
    }

    // 错误响应的构造函数
    public FeatureDetailResponse(String tableName, String featureId, String errorMessage) {
        this.tableName = tableName;
        this.featureId = featureId;
        this.attributes = new HashMap<>();
        this.imageUrls = null;
        this.success = false;
        this.message = errorMessage;
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

    public Map<String, Object> getAttributes() {
        return attributes;
    }

    public void setAttributes(Map<String, Object> attributes) {
        this.attributes = attributes;
    }

    public List<String> getImageUrls() {
        return imageUrls;
    }

    public void setImageUrls(List<String> imageUrls) {
        this.imageUrls = imageUrls;
    }

    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    /**
     * 添加属性
     * @param key 属性键
     * @param value 属性值
     */
    public void addAttribute(String key, Object value) {
        this.attributes.put(key, value);
    }

    /**
     * 获取属性值
     * @param key 属性键
     * @return 属性值
     */
    public Object getAttribute(String key) {
        return this.attributes.get(key);
    }

    /**
     * 创建成功响应
     * @param tableName 表名
     * @param featureId 要素ID
     * @param attributes 属性数据
     * @param imageUrls 图片URL列表
     * @return 成功响应对象
     */
    public static FeatureDetailResponse success(String tableName, String featureId, 
                                               Map<String, Object> attributes, List<String> imageUrls) {
        return new FeatureDetailResponse(tableName, featureId, attributes, imageUrls);
    }

    /**
     * 创建错误响应
     * @param tableName 表名
     * @param featureId 要素ID
     * @param errorMessage 错误信息
     * @return 错误响应对象
     */
    public static FeatureDetailResponse error(String tableName, String featureId, String errorMessage) {
        return new FeatureDetailResponse(tableName, featureId, errorMessage);
    }

    @Override
    public String toString() {
        return "FeatureDetailResponse{" +
                "tableName='" + tableName + '\'' +
                ", featureId='" + featureId + '\'' +
                ", attributes=" + attributes +
                ", imageUrls=" + imageUrls +
                ", success=" + success +
                ", message='" + message + '\'' +
                '}';
    }
}
