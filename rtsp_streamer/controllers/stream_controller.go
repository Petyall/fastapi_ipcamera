package controllers

import (
	"database/sql"
	"log"
	"net/http"
	"rtsp_streamer/services"
	"strconv"

	"github.com/gin-gonic/gin"
)

func StartCameraStream(c *gin.Context, db *sql.DB) {
	userID, _ := c.Get("user_id")
	cameraIDStr := c.Param("cameraID")
	cameraID, err := strconv.Atoi(cameraIDStr)
	if err != nil {
		log.Printf("StartCameraStream - Пользователь %s отправил неверный ID камеры (%d)", userID, cameraID)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Неверный ID камеры"})
		return
	}

	// Проверка пользователя и запуск камеры
	if userCheck, err := services.CheckUserCamera(cameraID, userID.(string), db); err != nil || !userCheck {
		log.Printf("StartCameraStream - У пользователя %s нет доступа к камере %d", userID, cameraID)
		c.JSON(http.StatusForbidden, gin.H{"error": "Недостаточно прав"})
		return
	}

	camera, err := services.GetCamera(cameraID, db)
	if err != nil {
		log.Printf("StartCameraStream - Ошибка получения данных о камере %d", cameraID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка получения данных камеры"})
		return
	}

	streamURL, err := services.DecryptStreamURL(camera.StreamURL, services.EncryptionKey)
	if err != nil {
		log.Printf("StartCameraStream - Ошибка при дешифровании потока камеры %d", cameraID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка дешифрования потока"})
		return
	}

	if err := services.StartFFMPEG(camera.ID, streamURL, userID.(string)); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	log.Printf("StartCameraStream - Запущена трансляция RTSP потока камеры %d", cameraID)
	c.JSON(http.StatusOK, gin.H{"message": "Запущена трансляция RTSP потока камеры " + camera.Location})
}

func StopCameraStream(c *gin.Context, db *sql.DB) {
	userID, _ := c.Get("user_id")
	cameraIDStr := c.Param("cameraID")
	cameraID, err := strconv.Atoi(cameraIDStr)
	if err != nil {
		log.Printf("StopCameraStream - Пользователь %s отправил неверный ID камеры (%d)", userID, cameraID)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Неверный ID камеры"})
		return
	}

	if err := services.StopFFMPEG(cameraID, userID.(string)); err != nil {
		log.Printf("StopCameraStream - %s", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// log.Printf("StopCameraStream - Остановлена трансляция RTSP потока камеры %d", cameraID)
	c.JSON(http.StatusOK, gin.H{"message": "Остановлена трансляция RTSP потока камеры " + strconv.Itoa(cameraID)})
}
