package com.backend.be.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * 景区实体类
 * 对应数据库中的 a_sight 表
 */
@Entity
@Table(name = "a_sight")
public class ASight {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "gid")
    private Integer gid;
    
    @Column(name = "name")
    private String name;
    
    @Column(name = "level")
    private String level;
    
    @Column(name = "所属省")
    private String 所属省;
    
    @Column(name = "所属城市")
    private String 所属城市;
    
    @Column(name = "所属区县")
    private String 所属区县;
    
    @Column(name = "address")
    private String address;
    
    @Column(name = "评定时间")
    private String 评定时间;
    
    @Column(name = "发布时间")
    private String 发布时间;
    
    @Column(name = "发布链接")
    private String 发布链接;
    
    @Column(name = "lng_gcj02")
    private Double lngGcj02;
    
    @Column(name = "lat_gcj02")
    private Double latGcj02;
    
    @Column(name = "lng_bd09")
    private Double lngBd09;
    
    @Column(name = "lat_bd09")
    private Double latBd09;
    
    @Column(name = "lng_wgs84")
    private Double lngWgs84;
    
    @Column(name = "lat_wgs84")
    private Double latWgs84;
    
    // 默认构造函数
    public ASight() {
    }
    
    // Getter 和 Setter 方法
    
    public Integer getGid() {
        return gid;
    }
    
    public void setGid(Integer gid) {
        this.gid = gid;
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public String getLevel() {
        return level;
    }
    
    public void setLevel(String level) {
        this.level = level;
    }
    
    public String get所属省() {
        return 所属省;
    }
    
    public void set所属省(String 所属省) {
        this.所属省 = 所属省;
    }
    
    public String get所属城市() {
        return 所属城市;
    }
    
    public void set所属城市(String 所属城市) {
        this.所属城市 = 所属城市;
    }
    
    public String get所属区县() {
        return 所属区县;
    }
    
    public void set所属区县(String 所属区县) {
        this.所属区县 = 所属区县;
    }
    
    public String getAddress() {
        return address;
    }
    
    public void setAddress(String address) {
        this.address = address;
    }
    
    public String get评定时间() {
        return 评定时间;
    }
    
    public void set评定时间(String 评定时间) {
        this.评定时间 = 评定时间;
    }
    
    public String get发布时间() {
        return 发布时间;
    }
    
    public void set发布时间(String 发布时间) {
        this.发布时间 = 发布时间;
    }
    
    public String get发布链接() {
        return 发布链接;
    }
    
    public void set发布链接(String 发布链接) {
        this.发布链接 = 发布链接;
    }
    
    public Double getLngGcj02() {
        return lngGcj02;
    }
    
    public void setLngGcj02(Double lngGcj02) {
        this.lngGcj02 = lngGcj02;
    }
    
    public Double getLatGcj02() {
        return latGcj02;
    }
    
    public void setLatGcj02(Double latGcj02) {
        this.latGcj02 = latGcj02;
    }
    
    public Double getLngBd09() {
        return lngBd09;
    }
    
    public void setLngBd09(Double lngBd09) {
        this.lngBd09 = lngBd09;
    }
    
    public Double getLatBd09() {
        return latBd09;
    }
    
    public void setLatBd09(Double latBd09) {
        this.latBd09 = latBd09;
    }
    
    public Double getLngWgs84() {
        return lngWgs84;
    }
    
    public void setLngWgs84(Double lngWgs84) {
        this.lngWgs84 = lngWgs84;
    }
    
    public Double getLatWgs84() {
        return latWgs84;
    }
    
    public void setLatWgs84(Double latWgs84) {
        this.latWgs84 = latWgs84;
    }
    
    @Override
    public String toString() {
        return "ASight{" +
                "gid=" + gid +
                ", name='" + name + '\'' +
                ", level='" + level + '\'' +
                ", 所属省='" + 所属省 + '\'' +
                ", 所属城市='" + 所属城市 + '\'' +
                ", 所属区县='" + 所属区县 + '\'' +
                ", address='" + address + '\'' +
                ", 评定时间='" + 评定时间 + '\'' +
                ", 发布时间='" + 发布时间 + '\'' +
                ", 发布链接='" + 发布链接 + '\'' +
                ", lngGcj02=" + lngGcj02 +
                ", latGcj02=" + latGcj02 +
                ", lngBd09=" + lngBd09 +
                ", latBd09=" + latBd09 +
                ", lngWgs84=" + lngWgs84 +
                ", latWgs84=" + latWgs84 +
                '}';
    }
}