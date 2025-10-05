package com.backend.be.service.impl;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.backend.be.mapper.TouristSpotMapper;
import com.backend.be.model.TouristSpot;
import com.backend.be.service.TouristSpotService;

/**
 * TouristSpot 业务逻辑层实现
 */
@Service
public class TouristSpotServiceImpl implements TouristSpotService {

    @Autowired
    private TouristSpotMapper touristSpotMapper;

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
    public boolean deleteTouristSpot(Integer id) {
        int result = touristSpotMapper.deleteById(id);
        return result > 0;
    }

    @Override
    public int getTouristSpotCount() {
        return touristSpotMapper.count();
    }
}
