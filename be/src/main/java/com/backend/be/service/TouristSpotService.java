package com.backend.be.service;

import java.util.List;

import com.backend.be.model.TouristSpot;

/**
 * TouristSpot 业务逻辑层接口
 */
public interface TouristSpotService {

    /**
     * 获取所有旅游景点
     */
    List<TouristSpot> getAllTouristSpots();

    /**
     * 根据ID获取旅游景点
     */
    TouristSpot getTouristSpotById(Integer id);

    /**
     * 根据城市获取旅游景点
     */
    List<TouristSpot> getTouristSpotsByCity(String city);

    /**
     * 根据名称搜索旅游景点
     */
    List<TouristSpot> searchTouristSpotsByName(String name);

    /**
     * 创建旅游景点
     */
    TouristSpot createTouristSpot(TouristSpot touristSpot);

    /**
     * 更新旅游景点
     */
    TouristSpot updateTouristSpot(TouristSpot touristSpot);

    /**
     * 删除旅游景点
     */
    boolean deleteTouristSpot(Integer id);

    /**
     * 获取旅游景点总数
     */
    int getTouristSpotCount();
}
