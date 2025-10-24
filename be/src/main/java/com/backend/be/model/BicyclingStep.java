package com.backend.be.model;

import lombok.Data;

/**
 * 骑行路线分段模型
 * 表示骑行路线中的一个分段，包含详细的骑行指示和道路信息
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Data
public class BicyclingStep {
    
    /**
     * 路段骑行指示
     * 例如："骑行54米右转"
     */
    private String instruction;
    
    /**
     * 此段路道路名称
     * 有可能出现空，需要特别指出，日后会用null表示
     * 例如："建国门北大街"
     */
    private String road;
    
    /**
     * 此段路骑行距离
     * 单位：米
     */
    private Double distance;
    
    /**
     * 此段路骑行方向
     * 例如："南"
     */
    private String orientation;
    
    /**
     * 此段路骑行耗时
     * 单位：秒
     */
    private Double duration;
    
    /**
     * 此段路骑行的坐标点
     * 格式：X,Y;X1,Y1;X2,Y2
     */
    private String polyline;
    
    /**
     * 此段路骑行主要动作
     * 内容为中文指示。骑行主要动作，可能为空，也可能为左转、右转、向左前方行驶、向右前方行驶等
     */
    private String action;
    
    /**
     * 此段路骑行辅助动作
     * 内容为中文提示。例如："到达目的地"
     */
    private String assistantAction;
    
    /**
     * 步行类型（骑行API中保留字段）
     * 骑行API中此字段通常为0
     */
    private Integer walkType;
    
    /**
     * 默认构造函数
     */
    public BicyclingStep() {
    }
    
    /**
     * 全参构造函数
     * 
     * @param instruction 路段骑行指示
     * @param road 道路名称
     * @param distance 骑行距离
     * @param orientation 骑行方向
     * @param duration 骑行耗时
     * @param polyline 坐标点
     * @param action 主要动作
     * @param assistantAction 辅助动作
     * @param walkType 步行类型
     */
    public BicyclingStep(String instruction, String road, Double distance, String orientation, 
                        Double duration, String polyline, String action, String assistantAction, 
                        Integer walkType) {
        this.instruction = instruction;
        this.road = road;
        this.distance = distance;
        this.orientation = orientation;
        this.duration = duration;
        this.polyline = polyline;
        this.action = action;
        this.assistantAction = assistantAction;
        this.walkType = walkType;
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
     * 获取完整的骑行指示信息
     * 
     * @return 完整的骑行指示信息
     */
    public String getFullInstruction() {
        StringBuilder sb = new StringBuilder();
        
        if (instruction != null && !instruction.isEmpty()) {
            sb.append(instruction);
        }
        
        if (action != null && !action.isEmpty()) {
            sb.append("，动作：").append(action);
        }
        
        if (assistantAction != null && !assistantAction.isEmpty()) {
            sb.append("，提示：").append(assistantAction);
        }
        
        return sb.toString();
    }
    
    /**
     * 验证分段数据的有效性
     * 
     * @return 是否有效
     */
    public boolean isValid() {
        return distance != null && distance > 0 && 
               duration != null && duration > 0 &&
               polyline != null && !polyline.trim().isEmpty();
    }
}