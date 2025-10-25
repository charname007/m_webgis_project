package com.backend.be.util;

/**
 * 坐标转换工具类
 * 实现WGS84坐标系与GCJ02坐标系之间的相互转换
 * GCJ02是中国国家测绘局制定的坐标系，俗称火星坐标系
 * 
 * @author Claude
 * @create 2025-10-24
 */
public class CoordinateConverter {
    
    /**
     * 圆周率
     */
    private static final double PI = 3.1415926535897932384626;
    
    /**
     * 地球长半轴
     */
    private static final double A = 6378245.0;
    
    /**
     * 地球扁率
     */
    private static final double EE = 0.00669342162296594323;
    
    /**
     * 将WGS84坐标转换为GCJ02坐标
     * 
     * @param wgsLng WGS84经度
     * @param wgsLat WGS84纬度
     * @return 转换后的GCJ02坐标 [经度, 纬度]
     */
    public static double[] wgs84ToGcj02(double wgsLng, double wgsLat) {
        if (outOfChina(wgsLng, wgsLat)) {
            return new double[]{wgsLng, wgsLat};
        }
        double dLat = transformLat(wgsLng - 105.0, wgsLat - 35.0);
        double dLng = transformLng(wgsLng - 105.0, wgsLat - 35.0);
        double radLat = wgsLat / 180.0 * PI;
        double magic = Math.sin(radLat);
        magic = 1 - EE * magic * magic;
        double sqrtMagic = Math.sqrt(magic);
        dLat = (dLat * 180.0) / ((A * (1 - EE)) / (magic * sqrtMagic) * PI);
        dLng = (dLng * 180.0) / (A / sqrtMagic * Math.cos(radLat) * PI);
        double mgLat = wgsLat + dLat;
        double mgLng = wgsLng + dLng;
        return new double[]{mgLng, mgLat};
    }
    
    /**
     * 将GCJ02坐标转换为WGS84坐标
     * 
     * @param gcjLng GCJ02经度
     * @param gcjLat GCJ02纬度
     * @return 转换后的WGS84坐标 [经度, 纬度]
     */
    public static double[] gcj02ToWgs84(double gcjLng, double gcjLat) {
        if (outOfChina(gcjLng, gcjLat)) {
            return new double[]{gcjLng, gcjLat};
        }
        double dLat = transformLat(gcjLng - 105.0, gcjLat - 35.0);
        double dLng = transformLng(gcjLng - 105.0, gcjLat - 35.0);
        double radLat = gcjLat / 180.0 * PI;
        double magic = Math.sin(radLat);
        magic = 1 - EE * magic * magic;
        double sqrtMagic = Math.sqrt(magic);
        dLat = (dLat * 180.0) / ((A * (1 - EE)) / (magic * sqrtMagic) * PI);
        dLng = (dLng * 180.0) / (A / sqrtMagic * Math.cos(radLat) * PI);
        double mgLat = gcjLat + dLat;
        double mgLng = gcjLng + dLng;
        return new double[]{gcjLng * 2 - mgLng, gcjLat * 2 - mgLat};
    }
    
    /**
     * 批量转换WGS84坐标到GCJ02
     * 
     * @param coordinates WGS84坐标数组 [[经度, 纬度], ...]
     * @return 转换后的GCJ02坐标数组
     */
    public static double[][] batchWgs84ToGcj02(double[][] coordinates) {
        double[][] result = new double[coordinates.length][2];
        for (int i = 0; i < coordinates.length; i++) {
            result[i] = wgs84ToGcj02(coordinates[i][0], coordinates[i][1]);
        }
        return result;
    }
    
    /**
     * 批量转换GCJ02坐标到WGS84
     * 
     * @param coordinates GCJ02坐标数组 [[经度, 纬度], ...]
     * @return 转换后的WGS84坐标数组
     */
    public static double[][] batchGcj02ToWgs84(double[][] coordinates) {
        double[][] result = new double[coordinates.length][2];
        for (int i = 0; i < coordinates.length; i++) {
            result[i] = gcj02ToWgs84(coordinates[i][0], coordinates[i][1]);
        }
        return result;
    }
    
    /**
     * 检查坐标是否在中国境外
     * 
     * @param lng 经度
     * @param lat 纬度
     * @return true表示在境外，false表示在境内
     */
    private static boolean outOfChina(double lng, double lat) {
        return lng < 72.004 || lng > 137.8347 || lat < 0.8293 || lat > 55.8271;
    }
    
    /**
     * 纬度转换
     * 
     * @param x 经度偏移量
     * @param y 纬度偏移量
     * @return 纬度转换值
     */
    private static double transformLat(double x, double y) {
        double ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
        ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
        ret += (20.0 * Math.sin(y * PI) + 40.0 * Math.sin(y / 3.0 * PI)) * 2.0 / 3.0;
        ret += (160.0 * Math.sin(y / 12.0 * PI) + 320 * Math.sin(y * PI / 30.0)) * 2.0 / 3.0;
        return ret;
    }
    
    /**
     * 经度转换
     * 
     * @param x 经度偏移量
     * @param y 纬度偏移量
     * @return 经度转换值
     */
    private static double transformLng(double x, double y) {
        double ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
        ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
        ret += (20.0 * Math.sin(x * PI) + 40.0 * Math.sin(x / 3.0 * PI)) * 2.0 / 3.0;
        ret += (150.0 * Math.sin(x / 12.0 * PI) + 300.0 * Math.sin(x / 30.0 * PI)) * 2.0 / 3.0;
        return ret;
    }
}