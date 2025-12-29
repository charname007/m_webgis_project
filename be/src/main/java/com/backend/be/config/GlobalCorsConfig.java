package com.backend.be.config;

import java.util.Arrays;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

@Configuration
public class GlobalCorsConfig {
    
    @Value("${spring.web.cors.allowed-origins:*}")
    private String allowedOrigins;
    
    @Value("${spring.web.cors.allowed-methods:*}")
    private String allowedMethods;
    
    @Value("${spring.web.cors.allowed-headers:*}")
    private String allowedHeaders;
    
    @Value("${spring.web.cors.allow-credentials:true}")
    private boolean allowCredentials;
    
    @Value("${spring.web.cors.max-age:3600}")
    private long maxAge;

    @Bean
    public CorsFilter corsFilter() {
        // 1. 配置跨域信息
        CorsConfiguration config = new CorsConfiguration();
        
        // 动态配置允许的源
        if (!"*".equals(allowedOrigins)) {
            Arrays.stream(allowedOrigins.split(","))
                  .forEach(origin -> config.addAllowedOriginPattern(origin.trim()));
        } else {
            config.addAllowedOriginPattern("*");
        }
        
        // 动态配置允许的方法
        if (!"*".equals(allowedMethods)) {
            Arrays.stream(allowedMethods.split(","))
                  .forEach(method -> config.addAllowedMethod(method.trim()));
        } else {
            config.addAllowedMethod("*");
        }
        
        // 动态配置允许的请求头
        if (!"*".equals(allowedHeaders)) {
            Arrays.stream(allowedHeaders.split(","))
                  .forEach(header -> config.addAllowedHeader(header.trim()));
        } else {
            config.addAllowedHeader("*");
        }
        
        // 允许前端携带 Cookie（如果需要身份验证）
        config.setAllowCredentials(allowCredentials);
        // 预检请求的有效期（秒），减少重复验证
        config.setMaxAge(maxAge);

        // 2. 配置需要跨域的路径（/** 表示所有接口）
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);

        // 3. 返回跨域过滤器
        return new CorsFilter(source);
    }
}
