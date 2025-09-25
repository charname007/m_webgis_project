package com.backend.be.model;

public class SpatialTableRequest {
    private String table;
    private String name;
    private String categories;
    private String geom;  // 存储实际的几何对象（WKT格式），可以是点或范围

    // 默认构造函数
    public SpatialTableRequest() {
    }

    // 带参数的构造函数
    public SpatialTableRequest(String table, String name, String categories, String geom) {
        this.table = table;
        this.name = name;
        this.categories = categories;
        this.geom = geom;
    }

    // Getter 和 Setter 方法
    public String getTable() {
        return table;
    }

    public void setTable(String table) {
        this.table = table;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getCategories() {
        return categories;
    }

    public void setCategories(String categories) {
        this.categories = categories;
    }

    public String getGeom() {
        return geom;
    }

    public void setGeom(String geom) {
        this.geom = geom;
    }

    @Override
    public String toString() {
        return "SpatialTableRequest{" +
                "table='" + table + '\'' +
                ", name='" + name + '\'' +
                ", categories='" + categories + '\'' +
                ", geom='" + geom + '\'' +
                '}';
    }
}
