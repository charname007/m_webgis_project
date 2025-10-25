package com.backend.be.model;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

/**
 * 骑行路线规划响应模型
 * 表示骑行路线规划API的完整响应
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Data
public class BicyclingRouteResponse {
    
    /**
     * 返回结果状态值
     * 0：请求失败；1：请求成功
     */
    private Integer status;
    
    /**
     * 返回状态说明
     * 当status为0时，info会返回具体错误原因
     */
    private String info;
    
    /**
     * 返回状态码
     * 10000：正常；详见错误码说明
     */
    private String infocode;
    
    /**
     * 骑行路径数量
     */
    private Integer count;
    
    /**
     * 骑行路径列表
     */
    private List<BicyclingPath> route;
    
    /**
     * 默认构造函数
     */
    public BicyclingRouteResponse() {
        this.route = new ArrayList<>();
    }
    
    /**
     * 构造函数
     * 
     * @param status 状态值
     * @param info 状态说明
     * @param infocode 状态码
     */
    public BicyclingRouteResponse(Integer status, String info, String infocode) {
        this();
        this.status = status;
        this.info = info;
        this.infocode = infocode;
    }
    
    /**
     * 构造函数
     * 
     * @param status 状态值
     * @param info 状态说明
     * @param infocode 状态码
     * @param count 路径数量
     * @param route 路径列表
     */
    public BicyclingRouteResponse(Integer status, String info, String infocode, 
                                 Integer count, List<BicyclingPath> route) {
        this.status = status;
        this.info = info;
        this.infocode = infocode;
        this.count = count;
        this.route = route != null ? route : new ArrayList<>();
    }
    
    /**
     * 创建成功响应
     * 
     * @param route 骑行路径列表
     * @return 成功响应对象
     */
    public static BicyclingRouteResponse success(List<BicyclingPath> route) {
        BicyclingRouteResponse response = new BicyclingRouteResponse();
        response.setStatus(1);
        response.setInfo("OK");
        response.setInfocode("10000");
        response.setRoute(route);
        response.setCount(route != null ? route.size() : 0);
        return response;
    }
    
    /**
     * 创建成功响应（单一路径）
     * 
     * @param path 骑行路径
     * @return 成功响应对象
     */
    public static BicyclingRouteResponse success(BicyclingPath path) {
        List<BicyclingPath> route = new ArrayList<>();
        if (path != null) {
            route.add(path);
        }
        return success(route);
    }
    
    /**
     * 创建错误响应
     * 
     * @param info 错误信息
     * @param infocode 错误码
     * @return 错误响应对象
     */
    public static BicyclingRouteResponse error(String info, String infocode) {
        BicyclingRouteResponse response = new BicyclingRouteResponse();
        response.setStatus(0);
        response.setInfo(info);
        response.setInfocode(infocode);
        response.setCount(0);
        return response;
    }
    
    /**
     * 创建错误响应（默认错误码）
     * 
     * @param info 错误信息
     * @return 错误响应对象
     */
    public static BicyclingRouteResponse error(String info) {
        return error(info, "30000");
    }
    
    /**
     * 检查响应是否成功
     * 
     * @return 是否成功
     */
    public boolean isSuccess() {
        return status != null && status == 1;
    }
    
    /**
     * 检查是否有有效的骑行路径
     * 
     * @return 是否有有效路径
     */
    public boolean hasValidRoute() {
        return route != null && !route.isEmpty() && 
               route.stream().anyMatch(BicyclingPath::isValid);
    }
    
    /**
     * 获取第一个有效路径
     * 
     * @return 第一个有效路径，如果没有则返回null
     */
    public BicyclingPath getFirstValidPath() {
        if (route != null) {
            return route.stream()
                       .filter(BicyclingPath::isValid)
                       .findFirst()
                       .orElse(null);
        }
        return null;
    }
    
    /**
     * 获取最短距离的路径
     * 
     * @return 最短距离路径，如果没有则返回null
     */
    public BicyclingPath getShortestPath() {
        if (route != null && !route.isEmpty()) {
            return route.stream()
                       .filter(BicyclingPath::isValid)
                       .min((p1, p2) -> Double.compare(p1.getDistance(), p2.getDistance()))
                       .orElse(null);
        }
        return null;
    }
    
    /**
     * 获取最短时间的路径
     * 
     * @return 最短时间路径，如果没有则返回null
     */
    public BicyclingPath getFastestPath() {
        if (route != null && !route.isEmpty()) {
            return route.stream()
                       .filter(BicyclingPath::isValid)
                       .min((p1, p2) -> Double.compare(p1.getDuration(), p2.getDuration()))
                       .orElse(null);
        }
        return null;
    }
    
    /**
     * 获取响应摘要信息
     * 
     * @return 摘要信息
     */
    public String getSummary() {
        if (isSuccess()) {
            if (hasValidRoute()) {
                BicyclingPath firstPath = getFirstValidPath();
                return String.format("骑行路线规划成功，共%d条路径，推荐路径：%s", 
                                   count, firstPath.getDescription());
            } else {
                return "骑行路线规划成功，但无有效路径";
            }
        } else {
            return String.format("骑行路线规划失败：%s（错误码：%s）", info, infocode);
        }
    }
}