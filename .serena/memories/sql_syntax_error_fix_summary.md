# SQL语法错误修复总结

## 问题描述
景区upsert操作失败，出现SQL语法错误：
- 错误信息：`语法错误 在 "<" 或附近的`
- 位置：第20个字符
- 影响景点：清华大学

## 问题根源
MyBatis动态SQL标签`<set>`在PostgreSQL中被当作比较操作符`<`，导致SQL语法错误。

## 修复方案

### 修复文件
- `be/src/main/resources/mapper/ASightMapper.xml`

### 修复内容
**问题SQL（修复前）**:
```xml
<update id="updateByNameSelective" parameterType="com.backend.be.model.ASight">
    <![CDATA[
    UPDATE a_sight
    <set>
        ...
    </set>
    WHERE name = #{name}
    ]]>
</update>
```

**修复后SQL**:
```xml
<update id="updateByNameSelective" parameterType="com.backend.be.model.ASight">
    UPDATE a_sight
    <set>
        ...
    </set>
    WHERE name = #{name}
</update>
```

### 关键修复点
- 移除了`<![CDATA[ ... ]]>`包装，让MyBatis能够正确解析动态SQL标签
- 确保`<set>`标签被MyBatis正确识别和处理
- 保持部分更新的功能完整性

## 修复效果
- 解决了SQL语法错误问题
- 确保景区upsert操作能够正常执行
- 支持"清华大学"等景区的更新和插入操作

## 技术要点
- MyBatis动态SQL标签需要正确的XML解析环境
- `<![CDATA[ ... ]]>`在某些情况下会阻止MyBatis解析动态标签
- 正确的MyBatis配置应该能够处理动态SQL标签而无需CDATA包装