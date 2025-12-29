package com.backend.be.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * 旅游景点实体类
 * 对应数据库中的 tourist_spot 表
 */
@Entity
@Table(name = "tourist_spot")
public class TouristSpot {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Integer id;
    
    @Column(name = "name", nullable = false)
    private String name;
    
    @Column(name = "链接")
    private String 链接;
    
    @Column(name = "地址")
    private String 地址;
    
    @Column(name = "介绍")
    private String 介绍;
    
    @Column(name = "开放时间")
    private String 开放时间;
    
    @Column(name = "图片链接")
    private String 图片链接;
    
    @Column(name = "评分")
    private String 评分;
    
    @Column(name = "建议游玩时间")
    private String 建议游玩时间;
    
    @Column(name = "建议季节")
    private String 建议季节;
    
    @Column(name = "门票")
    private String 门票;
    
    @Column(name = "小贴士")
    private String 小贴士;
    
    @Column(name = "page")
    private Integer page;
    
    @Column(name = "城市")
    private String 城市;
    
    // 默认构造函数
    public TouristSpot() {
    }
    
    // 带参数的构造函数（不包含 createdAt 和 updatedAt）
    public TouristSpot(Integer id, String name, String 链接, String 地址, String 介绍, 
                      String 开放时间, String 图片链接, String 评分, String 建议游玩时间, 
                      String 建议季节, String 门票, String 小贴士, Integer page, String 城市) {
        this.id = id;
        this.name = name;
        this.链接 = 链接;
        this.地址 = 地址;
        this.介绍 = 介绍;
        this.开放时间 = 开放时间;
        this.图片链接 = 图片链接;
        this.评分 = 评分;
        this.建议游玩时间 = 建议游玩时间;
        this.建议季节 = 建议季节;
        this.门票 = 门票;
        this.小贴士 = 小贴士;
        this.page = page;
        this.城市 = 城市;
    }
    
    // Getter 和 Setter 方法
    
    public Integer getId() {
        return id;
    }
    
    public void setId(Integer id) {
        this.id = id;
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public String get链接() {
        return 链接;
    }
    
    public void set链接(String 链接) {
        this.链接 = 链接;
    }
    
    public String get地址() {
        return 地址;
    }
    
    public void set地址(String 地址) {
        this.地址 = 地址;
    }
    
    public String get介绍() {
        return 介绍;
    }
    
    public void set介绍(String 介绍) {
        this.介绍 = 介绍;
    }
    
    public String get开放时间() {
        return 开放时间;
    }
    
    public void set开放时间(String 开放时间) {
        this.开放时间 = 开放时间;
    }
    
    public String get图片链接() {
        return 图片链接;
    }
    
    public void set图片链接(String 图片链接) {
        this.图片链接 = 图片链接;
    }
    
    public String get评分() {
        return 评分;
    }
    
    public void set评分(String 评分) {
        this.评分 = 评分;
    }
    
    public String get建议游玩时间() {
        return 建议游玩时间;
    }
    
    public void set建议游玩时间(String 建议游玩时间) {
        this.建议游玩时间 = 建议游玩时间;
    }
    
    public String get建议季节() {
        return 建议季节;
    }
    
    public void set建议季节(String 建议季节) {
        this.建议季节 = 建议季节;
    }
    
    public String get门票() {
        return 门票;
    }
    
    public void set门票(String 门票) {
        this.门票 = 门票;
    }
    
    public String get小贴士() {
        return 小贴士;
    }
    
    public void set小贴士(String 小贴士) {
        this.小贴士 = 小贴士;
    }
    
    public Integer getPage() {
        return page;
    }
    
    public void setPage(Integer page) {
        this.page = page;
    }
    
    
    public String get城市() {
        return 城市;
    }
    
    public void set城市(String 城市) {
        this.城市 = 城市;
    }
    
    @Override
    public String toString() {
        return "TouristSpot{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", 链接='" + 链接 + '\'' +
                ", 地址='" + 地址 + '\'' +
                ", 介绍='" + 介绍 + '\'' +
                ", 开放时间='" + 开放时间 + '\'' +
                ", 图片链接='" + 图片链接 + '\'' +
                ", 评分='" + 评分 + '\'' +
                ", 建议游玩时间='" + 建议游玩时间 + '\'' +
                ", 建议季节='" + 建议季节 + '\'' +
                ", 门票='" + 门票 + '\'' +
                ", 小贴士='" + 小贴士 + '\'' +
                ", page=" + page +
                ", 城市='" + 城市 + '\'' +
                '}';
    }
}
