package com.example.app;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.CommandLineRunner;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@SpringBootApplication
public class SimpleApplication {
    
    private static final Logger logger = LoggerFactory.getLogger(SimpleApplication.class);
    
    @Autowired
    private MessageRepository messageRepository;
    
    public static void main(String[] args) {
        logger.info("Starting Spring Boot application...");
        SpringApplication.run(SimpleApplication.class, args);
    }
    
    @Bean
    CommandLineRunner init() {
        return args -> {
            logger.info("Initializing database...");
            if (messageRepository.count() == 0) {
                Message message = new Message();
                message.setText("Hello from Spring Boot with PostgreSQL!");
                messageRepository.save(message);
                logger.info("Database initialized with sample data");
            }
        };
    }
}