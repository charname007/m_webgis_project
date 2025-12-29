package com.backend.be.model;

import lombok.Data;

/**
 * 驾车路线规划请求模型
 * 用于接收前端传递的路线规划参数
 * 
 * @author Claude
 * @create 2025-10-24
 */
@Data
public class RouteRequest {
    
    /**
     * 起点坐标 (WGS84坐标系)
     * 格式："经度,纬度"，例如："116.397428,39.90923"
     * 经度在前，纬度在后，小数点后不得超过6位
     */
    private String origin;
    
    /**
     * 终点坐标 (WGS84坐标系)
     * 格式："经度,纬度"，例如："116.397428,39.90923"
     * 经度在前，纬度在后，小数点后不得超过6位
     */
    private String destination;
    
    /**
     * 驾车算路策略
     * 32：默认，高德推荐，同高德地图APP默认
     * 33：躲避拥堵
     * 34：高速优先
     * 35：不走高速
     * 36：少收费
     * 37：大路优先
     * 38：速度最快
     * 39：躲避拥堵＋高速优先
     * 40：躲避拥堵＋不走高速
     * 41：躲避拥堵＋少收费
     * 42：少收费＋不走高速
     * 43：躲避拥堵＋少收费＋不走高速
     * 44：躲避拥堵＋大路优先
     * 45：躲避拥堵＋速度最快
     */
    private Integer strategy = 32;
    
    /**
     * 途经点
     * 途径点坐标串，多个途径点坐标按顺序以英文分号;分隔
     * 格式："经度1,纬度1;经度2,纬度2"
     * 最大支持16个途经点
     */
    private String waypoints;
    
    /**
     * 避让区域
     * 区域避让，多个区域坐标按顺序以英文竖线符号分隔
     * 每个区域最多可有16个顶点
     * 最大支持32个避让区域
     */
    private String avoidpolygons;
    
    /**
     * 避让道路名
     * 只支持一条避让道路
     */
    private String avoidroad;
    
    /**
     * 车牌号码
     * 车牌号，如 京AHA322，支持6位传统车牌和7位新能源车牌
     * 用于判断限行相关
     */
    private String plate;
    
    /**
     * 车辆类型
     * 0：普通燃油汽车
     * 1：纯电动汽车
     * 2：插电式混动汽车
     */
    private Integer cartype = 0;
    
    /**
     * 是否使用轮渡
     * 0:使用渡轮
     * 1:不使用渡轮
     */
    private Integer ferry = 0;
    
    /**
     * 起点POI ID
     * 起点为POI时，建议填充此值，可提升路线规划准确性
     */
    private String originId;
    
    /**
     * 终点POI ID
     * 目的地为POI时，建议填充此值，可提升路线规划准确性
     */
    private String destinationId;
    
    /**
     * 数字签名
     * 用于API签名验证，详情见高德地图API文档
     */
    private String sig;
    
    /**
     * 返回数据格式
     * 可选值：JSON，XML，默认JSON
     */
    private String output = "JSON";
    
    /**
     * 回调函数
     * callback值是用户定义的函数名称，此参数只在output=JSON时有效
     */
    private String callback;
}