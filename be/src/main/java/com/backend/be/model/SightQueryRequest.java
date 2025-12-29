package com.backend.be.model;

import java.util.List;

/**
 * 景区查询请求模型
 * 用于查询指定范围内的景区要素，支持按等级筛选
 */
public class SightQueryRequest {
    
    private Double minLon;
    private Double minLat;
    private Double maxLon;
    private Double maxLat;
    private List<String> levels;
    
    // 默认构造函数
    public SightQueryRequest() {
    }
    
    // 带参数的构造函数
    public SightQueryRequest(Double minLon, Double minLat, Double maxLon, Double maxLat, List<String> levels) {
        this.minLon = minLon;
        this.minLat = minLat;
        this.maxLon = maxLon;
        this.maxLat = maxLat;
        this.levels = levels;
    }
    
    // Getter 和 Setter 方法
    public Double getMinLon() {
        return minLon;
    }
    
    public void setMinLon(Double minLon) {
        this.minLon = minLon;
    }
    
    public Double getMinLat() {
        return minLat;
    }
    
    public void setMinLat(Double minLat) {
        this.minLat = minLat;
    }
    
    public Double getMaxLon() {
        return maxLon;
    }
    
    public void setMaxLon(Double maxLon) {
        this.maxLon = maxLon;
    }
    
    public Double getMaxLat() {
        return maxLat;
    }
    
    public void setMaxLat(Double maxLat) {
        this.maxLat = maxLat;
    }
    
    public List<String> getLevels() {
        return levels;
    }
    
    public void setLevels(List<String> levels) {
        this.levels = levels;
    }
    
    /**
     * 验证坐标范围是否有效
     * @return true 如果坐标范围有效
     */
    public boolean isValidExtent() {
        return minLon != null && minLat != null && maxLon != null && maxLat != null 
                && minLon < maxLon && minLat < maxLat;
    }
    
    /**
     * 验证等级列表是否有效
     * @return true 如果等级列表有效
     */
    public boolean hasValidLevels() {
        return levels != null && !levels.isEmpty();
    }
    
    /**
     * 获取坐标范围描述
     * @return 坐标范围字符串
     */
    public String getExtentDescription() {
        return String.format("经度: [%.6f, %.6f], 纬度: [%.6f, %.6f]", 
                minLon, maxLon, minLat, maxLat);
    }
    
    /**
     * 获取等级描述
     * @return 等级列表字符串
     */
    public String getLevelsDescription() {
        if (levels != null && !levels.isEmpty()) {
            return String.join(", ", levels);
        } else {
            return "所有等级";
        }
    }
    
    @Override
    public String toString() {
        return "SightQueryRequest{" +
                "minLon=" + minLon +
                ", minLat=" + minLat +
                ", maxLon=" + maxLon +
                ", maxLat=" + maxLat +
                ", levels=" + levels +
                '}';
    }
}
