package com.backend.be.mapper;

import java.util.List;

import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import com.backend.be.model.TouristSpot;

/**
 * TouristSpot 数据访问层
 */
@Mapper
public interface TouristSpotMapper {

    /**
     * 查询所有旅游景点
     */
    @Select("SELECT * FROM tourist_spot")
    List<TouristSpot> findAll();

    /**
     * 根据ID查询旅游景点
     */
    @Select("SELECT * FROM tourist_spot WHERE id = #{id}")
    TouristSpot findById(@Param("id") Integer id);

    /**
     * 根据城市查询旅游景点
     */
    @Select("SELECT * FROM tourist_spot WHERE 城市 = #{city}")
    List<TouristSpot> findByCity(@Param("city") String city);

    /**
     * 根据名称模糊查询旅游景点
     */
    @Select("SELECT * FROM tourist_spot WHERE name LIKE CONCAT('%', #{name}, '%')")
    List<TouristSpot> findByName(@Param("name") String name);

    /**
     * 插入旅游景点
     */
    @Insert("INSERT INTO tourist_spot (name, 链接, 地址, 介绍, 开放时间, 图片链接, 评分, 建议游玩时间, 建议季节, 门票, 小贴士, page, 城市) " +
            "VALUES (#{name}, #{链接}, #{地址}, #{介绍}, #{开放时间}, #{图片链接}, #{评分}, #{建议游玩时间}, #{建议季节}, #{门票}, #{小贴士}, #{page}, #{城市})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(TouristSpot touristSpot);

    /**
     * 更新旅游景点
     */
    @Update("UPDATE tourist_spot SET " +
            "name = #{name}, " +
            "链接 = #{链接}, " +
            "地址 = #{地址}, " +
            "介绍 = #{介绍}, " +
            "开放时间 = #{开放时间}, " +
            "图片链接 = #{图片链接}, " +
            "评分 = #{评分}, " +
            "建议游玩时间 = #{建议游玩时间}, " +
            "建议季节 = #{建议季节}, " +
            "门票 = #{门票}, " +
            "小贴士 = #{小贴士}, " +
            "page = #{page}, " +
            "城市 = #{城市} " +
            "WHERE id = #{id}")
    int update(TouristSpot touristSpot);

    /**
     * 根据ID删除旅游景点
     */
    @Delete("DELETE FROM tourist_spot WHERE id = #{id}")
    int deleteById(@Param("id") Integer id);

    /**
     * 根据名称更新旅游景点（部分更新，只更新非null字段）
     */
    @Update({
        "<script>",
        "UPDATE tourist_spot",
        "<set>",
        "  <if test='name != null'>name = #{name},</if>",
        "  <if test='链接 != null'>链接 = #{链接},</if>",
        "  <if test='地址 != null'>地址 = #{地址},</if>",
        "  <if test='介绍 != null'>介绍 = #{介绍},</if>",
        "  <if test='开放时间 != null'>开放时间 = #{开放时间},</if>",
        "  <if test='图片链接 != null'>图片链接 = #{图片链接},</if>",
        "  <if test='评分 != null'>评分 = #{评分},</if>",
        "  <if test='建议游玩时间 != null'>建议游玩时间 = #{建议游玩时间},</if>",
        "  <if test='建议季节 != null'>建议季节 = #{建议季节},</if>",
        "  <if test='门票 != null'>门票 = #{门票},</if>",
        "  <if test='小贴士 != null'>小贴士 = #{小贴士},</if>",
        "  <if test='page != null'>page = #{page},</if>",
        "  <if test='城市 != null'>城市 = #{城市},</if>",
        "</set>",
        "WHERE name = #{name}",
        "</script>"
    })
    int updateByNameSelective(TouristSpot touristSpot);

    /**
     * 根据ID更新旅游景点（部分更新，只更新非null字段）
     */
    @Update({
        "<script>",
        "UPDATE tourist_spot",
        "<set>",
        "  <if test='name != null'>name = #{name},</if>",
        "  <if test='链接 != null'>链接 = #{链接},</if>",
        "  <if test='地址 != null'>地址 = #{地址},</if>",
        "  <if test='介绍 != null'>介绍 = #{介绍},</if>",
        "  <if test='开放时间 != null'>开放时间 = #{开放时间},</if>",
        "  <if test='图片链接 != null'>图片链接 = #{图片链接},</if>",
        "  <if test='评分 != null'>评分 = #{评分},</if>",
        "  <if test='建议游玩时间 != null'>建议游玩时间 = #{建议游玩时间},</if>",
        "  <if test='建议季节 != null'>建议季节 = #{建议季节},</if>",
        "  <if test='门票 != null'>门票 = #{门票},</if>",
        "  <if test='小贴士 != null'>小贴士 = #{小贴士},</if>",
        "  <if test='page != null'>page = #{page},</if>",
        "  <if test='城市 != null'>城市 = #{城市},</if>",
        "</set>",
        "WHERE id = #{id}",
        "</script>"
    })
    int updateByIdSelective(TouristSpot touristSpot);

    /**
     * 统计旅游景点数量
     */
    @Select("SELECT COUNT(*) FROM tourist_spot")
    int count();
}
