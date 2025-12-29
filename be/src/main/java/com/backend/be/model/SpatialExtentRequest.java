package com.backend.be.model;

public class SpatialExtentRequest {
    
    private Double minLon;
    private Double minLat;
    private Double maxLon;
    private Double maxLat;

    // 默认构造函数
    public SpatialExtentRequest() {
    }

    // 带参数的构造函数
    public SpatialExtentRequest(Double minLon, Double minLat, Double maxLon, Double maxLat) {
        this.minLon = minLon;
        this.minLat = minLat;
        this.maxLon = maxLon;
        this.maxLat = maxLat;
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

    /**
     * 验证坐标范围是否有效
     * @return true 如果坐标范围有效
     */
    public boolean isValidExtent() {
        return minLon != null && minLat != null && maxLon != null && maxLat != null 
                && minLon < maxLon && minLat < maxLat;
    }

    /**
     * 获取坐标范围描述
     * @return 坐标范围字符串
     */
    public String getExtentDescription() {
        return String.format("经度: [%.6f, %.6f], 纬度: [%.6f, %.6f]", 
                minLon, maxLon, minLat, maxLat);
    }

    @Override
    public String toString() {
        return "SpatialExtentRequest{" +
                "minLon=" + minLon +
                ", minLat=" + minLat +
                ", maxLon=" + maxLon +
                ", maxLat=" + maxLat +
                '}';
    }
}
