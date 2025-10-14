package com.backend.be.service.impl;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.backend.be.mapper.TouristSpotMapper;
import com.backend.be.model.TouristSpot;
import com.backend.be.service.ASightService;
import com.backend.be.service.TouristSpotService;

/**
 * TouristSpot 业务逻辑层实现
 */
@Service
public class TouristSpotServiceImpl implements TouristSpotService {

    @Autowired
    private TouristSpotMapper touristSpotMapper;

    @Autowired
    private ASightService aSightService;

    @Override
    public List<TouristSpot> getAllTouristSpots() {
        return touristSpotMapper.findAll();
    }

    @Override
    public TouristSpot getTouristSpotById(Integer id) {
        return touristSpotMapper.findById(id);
    }

    @Override
    public List<TouristSpot> getTouristSpotsByCity(String city) {
        return touristSpotMapper.findByCity(city);
    }

    @Override
    public List<TouristSpot> searchTouristSpotsByName(String name) {
        return touristSpotMapper.findByName(name);
    }

    @Override
    public TouristSpot createTouristSpot(TouristSpot touristSpot) {
        int result = touristSpotMapper.insert(touristSpot);
        if (result > 0) {
            return touristSpot;
        }
        return null;
    }

    @Override
    public TouristSpot updateTouristSpot(TouristSpot touristSpot) {
        int result = touristSpotMapper.update(touristSpot);
        if (result > 0) {
            return touristSpotMapper.findById(touristSpot.getId());
        }
        return null;
    }

    @Override
    public TouristSpot updateTouristSpotWithSight(com.backend.be.model.TouristSpotUpdateRequest updateRequest) {
        // 更新 tourist_spot 表
        TouristSpot touristSpot = updateRequest.getTourist_spot();

        // 使用部分更新策略，只更新非null字段，避免将未传递的字段设置为null
        int spotResult = touristSpotMapper.updateByIdSelective(touristSpot);

        if (spotResult > 0) {
            // 更新 a_sight 表 - 通过名称匹配
            com.backend.be.model.ASight aSight = updateRequest.getA_sight();
            if (aSight != null && aSight.getName() != null) {
                // 使用 ASightService 进行upsert操作
                boolean sightResult = aSightService.upsertByName(aSight);
                if (sightResult) {
                    System.out.println("双表upsert成功 - 景点名称: " + aSight.getName());
                } else {
                    System.out.println("a_sight 表upsert失败 - 景点名称: " + aSight.getName());
                }
            }

            // 返回更新后的旅游景点信息
            return touristSpotMapper.findById(touristSpot.getId());
        }
        return null;
    }

    @Override
    public TouristSpot updateTouristSpotByNameWithSight(com.backend.be.model.TouristSpotUpdateRequest updateRequest) {
        // 获取两个表的数据
        TouristSpot touristSpot = updateRequest.getTourist_spot();
        com.backend.be.model.ASight aSight = updateRequest.getA_sight();

        if (touristSpot != null && touristSpot.getName() != null) {
            // 1. 处理 tourist_spot 表 - 使用 upsert 逻辑
            int spotResult;

            // 先检查记录是否存在
            List<TouristSpot> existingSpots = touristSpotMapper.findByName(touristSpot.getName());
            if (existingSpots != null && !existingSpots.isEmpty()) {
                // 记录存在，执行部分更新（只更新非null字段）
                spotResult = touristSpotMapper.updateByNameSelective(touristSpot);
                System.out.println("tourist_spot 表部分更新 - 名称: " + touristSpot.getName() + ", 影响行数: " + spotResult);
            } else {
                // 记录不存在，执行插入
                spotResult = touristSpotMapper.insert(touristSpot);
                System.out.println("tourist_spot 表插入 - 名称: " + touristSpot.getName() + ", 影响行数: " + spotResult);
            }

            if (spotResult > 0) {
                // 2. 处理 a_sight 表 - 使用 upsert 逻辑
                if (aSight != null && aSight.getName() != null) {
                    boolean sightResult;

                    // 使用upsert操作，自动处理更新或插入
                    sightResult = aSightService.upsertByName(aSight);
                    if (sightResult) {
                        System.out.println("a_sight 表upsert成功 - 名称: " + aSight.getName());
                    } else {
                        System.out.println("a_sight 表upsert失败 - 名称: " + aSight.getName());
                    }
                }

                // 返回更新/插入后的旅游景点信息
                return touristSpotMapper.findByName(touristSpot.getName()).stream().findFirst().orElse(null);
            } else {
                System.out.println("tourist_spot 表操作失败 - 名称: " + touristSpot.getName());
            }
        }
        return null;
    }

    @Override
    public boolean deleteTouristSpot(Integer id) {
        int result = touristSpotMapper.deleteById(id);
        return result > 0;
    }

    @Override
    public int getTouristSpotCount() {
        return touristSpotMapper.count();
    }
}
