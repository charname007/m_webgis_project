package com.backend.be.model;

import lombok.Data;

import java.util.List;

/**
 * GeoJSON Feature模型
 * 表示路线规划中的单个分段
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Data
public class RouteFeature {
    
    /**
     * GeoJSON类型，固定为"Feature"
     */
    private final String type = "Feature";
    
    /**
     * 几何信息
     * 包含LineString类型的坐标点
     */
    private Geometry geometry;
    
    /**
     * 分段属性信息
     * 包含道路名称、行驶指示、距离、时间等
     */
    private RouteProperties properties;
    
    /**
     * 几何信息内部类
     * 表示LineString类型的几何对象
     */
    @Data
    public static class Geometry {
        
        /**
         * 几何类型，固定为"LineString"
         */
        private final String type = "LineString";
        
        /**
         * 坐标点数组
         * 格式：[[经度1, 纬度1], [经度2, 纬度2], ...]
         * 使用WGS84坐标系
         */
        private List<double[]> coordinates;
    }
    
    /**
     * 分段属性内部类
     * 包含路线分段的详细信息
     */
    @Data
    public static class RouteProperties {
        
        /**
         * 行驶指示
         * 例如："沿长安街行驶"
         */
        private String instruction;
        
        /**
         * 进入道路方向
         * 例如："北"、"东北"等
         */
        private String orientation;
        
        /**
         * 道路名称
         * 例如："长安街"
         */
        private String roadName;
        
        /**
         * 分段距离
         * 单位：米
         */
        private Double stepDistance;
        
        /**
         * 分段耗时
         * 单位：秒
         */
        private Double duration;
        
        /**
         * 分段收费
         * 单位：元
         */
        private Double tolls;
        
        /**
         * 路况信息
         * 包括：未知、畅通、缓行、拥堵、严重拥堵
         */
        private String tmcStatus;
        
        /**
         * 导航主要动作指令
         * 例如："直行"、"左转"、"右转"等
         */
        private String action;
        
        /**
         * 导航辅助动作指令
         */
        private String assistantAction;
        
        /**
         * 分段索引
         * 在当前路径中的分段序号
         */
        private Integer stepIndex;
    }
}