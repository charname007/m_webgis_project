package com.backend.be.model;

import lombok.Data;
import java.util.List;

/**
 * 步行路线规划响应模型
 * 包含步行路线规划的所有结果信息
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Data
public class WalkingRouteResponse {
    
    /**
     * 返回状态
     * 1：成功；0：失败
     */
    private Integer status;
    
    /**
     * 返回的状态信息
     * status为0时，info返回错误原因；否则返回"OK"
     */
    private String info;
    
    /**
     * 信息码
     * 详情见高德地图API信息码表
     */
    private String infocode;
    
    /**
     * 返回结果总数目
     * 通常为1，步行路线规划只返回一条路径
     */
    private Integer count;
    
    /**
     * 步行路径列表
     * 包含所有步行路线方案
     */
    private List<WalkingPath> paths;
    
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
     * 构造成功的步行路线响应
     * 
     * @param paths 步行路径列表
     * @return 步行路线响应
     */
    public static WalkingRouteResponse success(List<WalkingPath> paths) {
        WalkingRouteResponse response = new WalkingRouteResponse();
        response.setStatus(1);
        response.setInfo("OK");
        response.setInfocode("10000");
        response.setCount(paths != null ? paths.size() : 0);
        response.setPaths(paths);
        return response;
    }
    
    /**
     * 构造失败的步行路线响应
     * 
     * @param errorInfo 错误信息
     * @param errorCode 错误码
     * @return 步行路线响应
     */
    public static WalkingRouteResponse error(String errorInfo, String errorCode) {
        WalkingRouteResponse response = new WalkingRouteResponse();
        response.setStatus(0);
        response.setInfo(errorInfo);
        response.setInfocode(errorCode);
        response.setCount(0);
        return response;
    }
    
    /**
     * 检查响应是否成功
     * 
     * @return true表示成功，false表示失败
     */
    public boolean isSuccess() {
        return status != null && status == 1;
    }
}