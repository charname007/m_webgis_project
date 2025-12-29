package com.backend.be.model;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

/**
 * 骑行路径模型
 * 表示一条完整的骑行路径，包含距离、时间和分段信息
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Data
public class BicyclingPath {
    
    /**
     * 起终点的骑行距离
     * 单位：米
     */
    private Double distance;
    
    /**
     * 起终点的骑行时间
     * 单位：秒
     */
    private Double duration;
    
    /**
     * 骑行分段列表
     */
    private List<BicyclingStep> steps;
    
    /**
     * 默认构造函数
     */
    public BicyclingPath() {
        this.steps = new ArrayList<>();
    }
    
    /**
     * 构造函数
     * 
     * @param distance 骑行距离
     * @param duration 骑行时间
     */
    public BicyclingPath(Double distance, Double duration) {
        this();
        this.distance = distance;
        this.duration = duration;
    }
    
    /**
     * 构造函数
     * 
     * @param distance 骑行距离
     * @param duration 骑行时间
     * @param steps 骑行分段列表
     */
    public BicyclingPath(Double distance, Double duration, List<BicyclingStep> steps) {
        this.distance = distance;
        this.duration = duration;
        this.steps = steps != null ? steps : new ArrayList<>();
    }
    
    /**
     * 添加骑行分段
     * 
     * @param step 骑行分段
     */
    public void addStep(BicyclingStep step) {
        if (steps == null) {
            steps = new ArrayList<>();
        }
        steps.add(step);
    }
    
    /**
     * 获取距离的格式化字符串
     * 
     * @return 格式化后的距离字符串
     */
    public String getFormattedDistance() {
        if (distance == null) {
            return "未知距离";
        }
        
        if (distance < 1000) {
            return distance.intValue() + "米";
        } else {
            return String.format("%.1f公里", distance / 1000.0);
        }
    }
    
    /**
     * 获取耗时的格式化字符串
     * 
     * @return 格式化后的耗时字符串
     */
    public String getFormattedDuration() {
        if (duration == null) {
            return "未知时间";
        }
        
        int minutes = (int) (duration / 60);
        int seconds = (int) (duration % 60);
        
        if (minutes > 0) {
            return minutes + "分钟" + seconds + "秒";
        } else {
            return seconds + "秒";
        }
    }
    
    /**
     * 获取总分段数
     * 
     * @return 分段数量
     */
    public int getStepCount() {
        return steps != null ? steps.size() : 0;
    }
    
    /**
     * 验证路径数据的有效性
     * 
     * @return 是否有效
     */
    public boolean isValid() {
        return distance != null && distance > 0 && 
               duration != null && duration > 0 &&
               steps != null && !steps.isEmpty();
    }
    
    /**
     * 获取路径的简要描述
     * 
     * @return 路径描述
     */
    public String getDescription() {
        return String.format("骑行%s，预计耗时%s，共%d个分段", 
                           getFormattedDistance(), 
                           getFormattedDuration(), 
                           getStepCount());
    }
    
    /**
     * 获取第一个分段
     * 
     * @return 第一个分段，如果没有则返回null
     */
    public BicyclingStep getFirstStep() {
        if (steps != null && !steps.isEmpty()) {
            return steps.get(0);
        }
        return null;
    }
    
    /**
     * 获取最后一个分段
     * 
     * @return 最后一个分段，如果没有则返回null
     */
    public BicyclingStep getLastStep() {
        if (steps != null && !steps.isEmpty()) {
            return steps.get(steps.size() - 1);
        }
        return null;
    }
}