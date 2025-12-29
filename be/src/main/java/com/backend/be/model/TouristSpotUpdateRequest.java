package com.backend.be.model;

/**
 * 景点更新请求DTO
 * 用于接收前端发送的嵌套JSON结构，包含两个表的数据
 */
public class TouristSpotUpdateRequest {
    
    private TouristSpot tourist_spot;
    private ASight a_sight;
    
    // 默认构造函数
    public TouristSpotUpdateRequest() {
    }
    
    // Getter 和 Setter 方法
    
    public TouristSpot getTourist_spot() {
        return tourist_spot;
    }
    
    public void setTourist_spot(TouristSpot tourist_spot) {
        this.tourist_spot = tourist_spot;
    }
    
    public ASight getA_sight() {
        return a_sight;
    }
    
    public void setA_sight(ASight a_sight) {
        this.a_sight = a_sight;
    }
    
    @Override
    public String toString() {
        return "TouristSpotUpdateRequest{" +
                "tourist_spot=" + tourist_spot +
                ", a_sight=" + a_sight +
                '}';
    }
}