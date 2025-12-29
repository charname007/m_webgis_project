package com.backend.be.util;

import com.backend.be.model.RouteFeature;

import java.util.ArrayList;
import java.util.List;

/**
 * GeoJSON格式处理工具类
 * 用于构建和组装GeoJSON格式的路线数据
 * 
 * @author Claude
 * @create 2025-10-24
 */
public class GeoJsonUtil {
    
    /**
     * 创建LineString几何对象
     * 
     * @param coordinates 坐标点数组 [[经度, 纬度], ...]
     * @return LineString几何对象
     */
    public static RouteFeature.Geometry createLineStringGeometry(double[][] coordinates) {
        RouteFeature.Geometry geometry = new RouteFeature.Geometry();
        
        // 将二维数组转换为List<double[]>
        List<double[]> coordList = new ArrayList<>();
        for (double[] coord : coordinates) {
            coordList.add(coord);
        }
        geometry.setCoordinates(coordList);
        
        return geometry;
    }
    
    /**
     * 创建路线分段Feature
     * 
     * @param coordinates 分段坐标点数组
     * @param instruction 行驶指示
     * @param roadName 道路名称
     * @param stepDistance 分段距离
     * @param duration 分段耗时
     * @param stepIndex 分段索引
     * @return 路线分段Feature
     */
    public static RouteFeature createRouteFeature(double[][] coordinates, 
                                                  String instruction, 
                                                  String roadName, 
                                                  Double stepDistance, 
                                                  Double duration, 
                                                  Integer stepIndex) {
        RouteFeature feature = new RouteFeature();
        
        // 设置几何信息
        RouteFeature.Geometry geometry = createLineStringGeometry(coordinates);
        feature.setGeometry(geometry);
        
        // 设置属性信息
        RouteFeature.RouteProperties properties = new RouteFeature.RouteProperties();
        properties.setInstruction(instruction);
        properties.setRoadName(roadName);
        properties.setStepDistance(stepDistance);
        properties.setDuration(duration);
        properties.setStepIndex(stepIndex);
        
        feature.setProperties(properties);
        
        return feature;
    }
    
    /**
     * 创建完整的路线分段Feature
     * 
     * @param coordinates 分段坐标点数组
     * @param instruction 行驶指示
     * @param orientation 进入道路方向
     * @param roadName 道路名称
     * @param stepDistance 分段距离
     * @param duration 分段耗时
     * @param tolls 分段收费
     * @param tmcStatus 路况信息
     * @param action 导航动作指令
     * @param assistantAction 导航辅助动作指令
     * @param stepIndex 分段索引
     * @return 完整的路线分段Feature
     */
    public static RouteFeature createFullRouteFeature(double[][] coordinates,
                                                      String instruction,
                                                      String orientation,
                                                      String roadName,
                                                      Double stepDistance,
                                                      Double duration,
                                                      Double tolls,
                                                      String tmcStatus,
                                                      String action,
                                                      String assistantAction,
                                                      Integer stepIndex) {
        RouteFeature feature = new RouteFeature();
        
        // 设置几何信息
        RouteFeature.Geometry geometry = createLineStringGeometry(coordinates);
        feature.setGeometry(geometry);
        
        // 设置完整属性信息
        RouteFeature.RouteProperties properties = new RouteFeature.RouteProperties();
        properties.setInstruction(instruction);
        properties.setOrientation(orientation);
        properties.setRoadName(roadName);
        properties.setStepDistance(stepDistance);
        properties.setDuration(duration);
        properties.setTolls(tolls);
        properties.setTmcStatus(tmcStatus);
        properties.setAction(action);
        properties.setAssistantAction(assistantAction);
        properties.setStepIndex(stepIndex);
        
        feature.setProperties(properties);
        
        return feature;
    }
    
    /**
     * 解析坐标点字符串
     * 将高德地图返回的坐标点字符串解析为二维数组
     * 
     * @param polyline 坐标点字符串，格式："经度1,纬度1;经度2,纬度2;..."
     * @return 坐标点二维数组
     */
    public static double[][] parsePolyline(String polyline) {
        if (polyline == null || polyline.trim().isEmpty()) {
            return new double[0][2];
        }
        
        String[] points = polyline.split(";");
        double[][] coordinates = new double[points.length][2];
        
        for (int i = 0; i < points.length; i++) {
            String[] coords = points[i].split(",");
            if (coords.length >= 2) {
                coordinates[i][0] = Double.parseDouble(coords[0]);
                coordinates[i][1] = Double.parseDouble(coords[1]);
            }
        }
        
        return coordinates;
    }
    
    /**
     * 解析单个坐标点
     * 
     * @param coordString 坐标点字符串，格式："经度,纬度"
     * @return 坐标点数组 [经度, 纬度]
     */
    public static double[] parseCoordinate(String coordString) {
        if (coordString == null || coordString.trim().isEmpty()) {
            return new double[2];
        }
        
        String[] coords = coordString.split(",");
        if (coords.length >= 2) {
            return new double[]{
                Double.parseDouble(coords[0]),
                Double.parseDouble(coords[1])
            };
        }
        
        return new double[2];
    }
}