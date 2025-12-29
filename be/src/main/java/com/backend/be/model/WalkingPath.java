package com.backend.be.model;

import lombok.Data;
import java.util.List;

/**
 * 步行路径模型
 * 表示一条完整的步行路线方案
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Data
public class WalkingPath {
    
    /**
     * 起点和终点的步行距离
     * 单位：米
     */
    private Integer distance;
    
    /**
     * 步行时间预计
     * 单位：秒
     */
    private Integer duration;
    
    /**
     * 步行分段列表
     * 包含路线中的每一段步行方案
     */
    private List<WalkingStep> steps;
    
    /**
     * 起点坐标
     * 格式："经度,纬度"
     */
    private String origin;
    
    /**
     * 终点坐标
     * 格式："经度,纬度"
     */
    private String destination;
    
    /**
     * 获取总步行时间（分钟）
     * 
     * @return 步行时间（分钟）
     */
    public Integer getDurationInMinutes() {
        return duration != null ? duration / 60 : 0;
    }
    
    /**
     * 获取总步行距离（公里）
     * 
     * @return 步行距离（公里）
     */
    public Double getDistanceInKilometers() {
        return distance != null ? distance / 1000.0 : 0.0;
    }
}