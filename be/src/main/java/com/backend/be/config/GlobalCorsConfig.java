package com.backend.be.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

@Configuration
public class GlobalCorsConfig {

    @Bean
    public CorsFilter corsFilter() {
        // 1. 配置跨域信息
        CorsConfiguration config = new CorsConfiguration();
        // 允许前端的域名（必须精确到协议+域名+端口，本地开发通常是 http://localhost:5173）
        config.addAllowedOrigin("http://localhost:5173");
        // 允许所有请求方法（GET、POST、PUT、DELETE 等）
        config.addAllowedMethod("*");
        // 允许所有请求头（如 Content-Type、Authorization 等）
        config.addAllowedHeader("*");
        // 允许前端携带 Cookie（如果需要身份验证）
        config.setAllowCredentials(true);
        // 预检请求的有效期（秒），减少重复验证
        config.setMaxAge(3600L);

        // 2. 配置需要跨域的路径（/** 表示所有接口）
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);

        // 3. 返回跨域过滤器
        return new CorsFilter(source);
    }
}
