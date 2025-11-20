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
    public TouristSpot createTouristSpotWithSight(com.backend.be.model.TouristSpotUpdateRequest createRequest) {
        TouristSpot touristSpot = createRequest.getTourist_spot();
        com.backend.be.model.ASight aSight = createRequest.getA_sight();

        if (touristSpot != null) {
            // 1. 插入 tourist_spot 表
            int spotResult = touristSpotMapper.insert(touristSpot);

            if (spotResult > 0) {
                // 2. 插入 a_sight 表
                if (aSight != null && aSight.getName() != null) {
                    boolean sightResult = aSightService.upsertByName(aSight);
                    if (sightResult) {
                        System.out.println("双表插入成功 - 景点名称: " + aSight.getName());
                    } else {
                        System.out.println("a_sight 表插入失败 - 景点名称: " + aSight.getName());
                    }
                }

                // 返回创建后的旅游景点信息
                return touristSpotMapper.findById(touristSpot.getId());
            } else {
                System.out.println("tourist_spot 表插入失败");
            }
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
    public boolean deleteTouristSpotWithSight(Integer id) {
        // 1. 先获取要删除的旅游景点信息，用于获取名称
        TouristSpot touristSpot = touristSpotMapper.findById(id);
        if (touristSpot == null) {
            System.out.println("旅游景点不存在 - ID: " + id);
            return false;
        }

        // 2. 删除 tourist_spot 表中的记录
        int spotResult = touristSpotMapper.deleteById(id);

        if (spotResult > 0) {
            // 3. 删除 a_sight 表中的相关记录
            boolean sightResult = aSightService.deleteByName(touristSpot.getName());
            if (sightResult) {
                System.out.println("双表删除成功 - 景点名称: " + touristSpot.getName());
                return true;
            } else {
                System.out.println("a_sight 表删除失败，但tourist_spot表删除成功 - 景点名称: " + touristSpot.getName());
                return true; // 即使a_sight删除失败，tourist_spot删除成功也算成功
            }
        } else {
            System.out.println("tourist_spot 表删除失败 - ID: " + id);
            return false;
        }
    }

    @Override
    public boolean deleteTouristSpotByNameWithSight(String name) {
        // 1. 提取中文名称
        String chineseName = extractChineseName(name);

        // 2. 删除 a_sight 表中的记录
        boolean sightResult = aSightService.deleteByName(chineseName);

        // 3. 删除 tourist_spot 表中的记录
        int spotResult = touristSpotMapper.deleteByName(chineseName);

        boolean overallSuccess = sightResult || spotResult > 0;

        if (overallSuccess) {
            System.out.println("双表删除操作完成 - 景点名称: " + chineseName +
                             ", a_sight删除: " + sightResult +
                             ", tourist_spot删除行数: " + spotResult);
        } else {
            System.out.println("双表删除失败 - 景点名称: " + chineseName);
        }

        return overallSuccess;
    }

    /**
     * 从混合名称中提取中文部分
     */
    private String extractChineseName(String mixedName) {
        if (mixedName == null || mixedName.trim().isEmpty()) {
            return mixedName;
        }

        // 使用正则表达式匹配中文部分
        java.util.regex.Pattern pattern = java.util.regex.Pattern.compile("^[\u4e00-\u9fa5]+\s*[\u4e00-\u9fa5]*");
        java.util.regex.Matcher matcher = pattern.matcher(mixedName);

        if (matcher.find()) {
            String chinesePart = matcher.group().trim();
            if (!chinesePart.isEmpty()) {
                return chinesePart;
            }
        }

        // 如果没有找到中文部分，返回原名称
        return mixedName;
    }

    @Override
    public int getTouristSpotCount() {
        return touristSpotMapper.count();
    }
}
