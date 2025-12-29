package com.backend.be.model;

import lombok.Data;

/**
 * 步行路线分段模型
 * 表示步行路线中的每一段步行方案
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Data
public class WalkingStep {
    
    /**
     * 路段步行指示
     * 例如："向南步行16米左转"
     */
    private String instruction;
    
    /**
     * 道路名称
     * 例如："望京东路辅路"
     */
    private String road;
    
    /**
     * 此路段距离
     * 单位：米
     */
    private Integer distance;
    
    /**
     * 方向
     * 例如："南"、"东南"、"西南"等
     */
    private String orientation;
    
    /**
     * 此路段预计步行时间
     * 单位：秒
     */
    private Integer duration;
    
    /**
     * 此路段坐标点
     * 格式："经度1,纬度1;经度2,纬度2;..."
     */
    private String polyline;
    
    /**
     * 步行主要动作
     * 详情见高德地图步行动作列表
     * 例如："左转"、"右转"、"直行"、"向右前方行走"等
     */
    private String action;
    
    /**
     * 步行辅助动作
     * 详情见高德地图步行动作列表
     * 例如："到达目的地"、"进入右侧道路"等
     */
    private String assistantAction;
    
    /**
     * 道路类型
     * 0：普通道路
     * 1：人行横道
     * 3：地下通道
     * 4：过街天桥
     * 5：地铁通道
     * 6：公园
     * 7：广场
     * 8：扶梯
     * 9：直梯
     * 10：索道
     * 11：空中通道
     * 12：建筑物穿越通道
     * 13：行人通道
     * 14：游船路线
     * 15：观光车路线
     * 16：滑道
     * 18：扩路
     * 19：道路附属连接线
     * 20：阶梯
     * 21：斜坡
     * 22：桥
     * 23：隧道
     * 极行轮渡
     */
    private Integer walkType;
    
    /**
     * 获取道路类型描述
     * 
     * @return 道路类型中文描述
     */
    public String getWalkTypeDescription() {
        switch (walkType) {
            case 0:
                return "普通道路";
            case 1:
                return "人行横道";
            case 3:
                return "地下通道";
            case 4:
                return "过街天桥";
            case 5:
                return "地铁通道";
            case 6:
                return "公园";
            case 7:
                return "广场";
            case 8:
                return "扶梯";
            case 9:
                return "直梯";
            case 10:
                return "索道";
            case 11:
                return "空中通道";
            case 12:
                return "建筑物穿越通道";
            case 13:
                return "行人通道";
            case 14:
                return "游船路线";
            case 15:
                return "观光车路线";
            case 16:
                return "滑道";
            case 18:
                return "扩路";
            case 19:
                return "道路附属连接线";
            case 20:
                return "阶梯";
            case 21:
                return "斜坡";
            case 22:
                return "桥";
            case 23:
                return "隧道";
            default:
                return "未知道路类型";
        }
    }
}