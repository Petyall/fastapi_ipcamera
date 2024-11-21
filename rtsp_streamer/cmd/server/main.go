package main

import (
	"log"
	"rtsp_streamer/config"
	"rtsp_streamer/database"
	"rtsp_streamer/routes"

	"github.com/gin-gonic/gin"
)

func main() {
	// Загружаем конфигурацию
	err := config.LoadEnv()
	if err != nil {
		log.Fatalf("Ошибка загрузки файла .env: %v", err)
	}

	// Устанавливаем соединение с базой данных
	db, err := database.Connect()
	if err != nil {
		log.Fatalf("Ошибка подключения к базе данных: %v", err)
	}
	defer db.Close()

	// Проверяем соединение
	err = db.Ping()
	if err != nil {
		log.Fatalf("Не удалось подключиться к базе данных: %v", err)
	}
	log.Println("Успешное подключение к базе данных")

	// Настраиваем маршруты
	r := gin.Default()
	routes.RegisterRoutes(r, db)

	// Запускаем сервер
	log.Fatal(r.Run("localhost:8080"))
}
