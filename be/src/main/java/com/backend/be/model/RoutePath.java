package com.backend.be.model;

import lombok.Data;

import java.util.List;

/**
 * 单条路径模型
 * 表示路线规划中的一条完整路径，使用GeoJSON FeatureCollection格式
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Data
public class RoutePath {
    
    /**
     * GeoJSON类型，固定为"FeatureCollection"
     */
    private final String type = "FeatureCollection";
    
    /**
     * 路线分段列表
     * 每个分段是一个RouteFeature对象
     */
    private List<RouteFeature> features;
    
    /**
     * 路径整体属性
     * 包含路径的总距离、总时间、总收费等信息
     */
    private PathProperties properties;
    
    /**
     * 路径属性内部类
     * 包含路径的整体信息
     */
    @Data
    public static class PathProperties {
        
        /**
         * 路径索引
         * 在多条路径中的序号，从0开始
         */
        private Integer pathIndex;
        
        /**
         * 总距离
         * 单位：米
         */
        private Double totalDistance;
        
        /**
         * 总时间
         * 单位：秒
         */
        private Double totalDuration;
        
        /**
         * 总收费
         * 单位：元
         */
        private Double totalTolls;
        
        /**
         * 收费路段里程
         * 单位：米
         */
        private Double tollDistance;
        
        /**
         * 主要收费道路
         */
        private String tollRoad;
        
        /**
         * 预计出租车费用
         * 单位：元
         */
        private Double taxiFee;
        
        /**
         * 红绿灯个数
         * 单位：个
         */
        private Integer trafficLights;
        
        /**
         * 是否有限行路段
         * false 代表限行已规避或未限行
         * true 代表限行无法规避
         */
        private Boolean restriction;
        
        /**
         * 路径策略描述
         * 例如："高速优先"、"躲避拥堵"等
         */
        private String strategyDescription;
    }
}