package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"gorm.io/gorm"

	"database/sql"

	_ "github.com/lib/pq"
)

type streamInfo struct {
	process   *exec.Cmd
	viewCount int
	mux       sync.Mutex
}

var Database *gorm.DB

var (
	streams = make(map[string]*streamInfo)
	mux     sync.RWMutex
)

func startFFMPEG(cameraID int, streamURL string) error {

	mux.RLock()
	info, exists := streams[strconv.Itoa(cameraID)]
	mux.RUnlock()

	if exists && info.viewCount > 0 {
		info.mux.Lock()
		info.viewCount++
		info.mux.Unlock()
		fmt.Printf("К просмотру RTSP потока %d присоединился новый человек\n", cameraID)
		return nil
	}

	if exists {
		fmt.Printf("Перезапуск трансляции RTSP потока камеры %d\n", cameraID)
	} else {
		fmt.Printf("Начало трансляции RTSP потока камеры %d\n", cameraID)
	}

	dirPath := filepath.Join("streams", "camera_"+strconv.Itoa(cameraID))
	if err := os.MkdirAll(dirPath, os.ModePerm); err != nil {
		return err
	}

	cmd := exec.Command("ffmpeg", "-i", streamURL, "-c:v", "libx264", "-preset",
		"ultrafast", "-b:v", "500k", "-s", "640x360", "-f", "hls", "-hls_time",
		"2", "-hls_list_size", "10", "-hls_flags", "delete_segments",
		"./streams/camera_"+strconv.Itoa(cameraID)+"/index.m3u8")

	if err := cmd.Start(); err != nil {
		return err
	}

	mux.Lock()
	if !exists {
		streams[strconv.Itoa(cameraID)] = &streamInfo{
			process:   cmd,
			viewCount: 1,
		}
	} else {
		info.process = cmd
		info.viewCount = 1
	}
	mux.Unlock()

	filePath := "./streams/camera_" + strconv.Itoa(cameraID) + "/index.m3u8"
	for i := 0; i < 30; i++ {
		if _, err := os.Stat(filePath); err == nil {
			break
		}
		time.Sleep(time.Second)
	}

	if _, err := os.Stat(filePath); err != nil {
		return fmt.Errorf("время ожидания для файла %s превышено", filePath)
	}

	return nil
}

func stopFFMPEG(cameraID int) error {
	mux.Lock()
	defer mux.Unlock()

	info, exists := streams[strconv.Itoa(cameraID)]
	if !exists || info.viewCount <= 0 {
		return fmt.Errorf("в данный момент никто не просматривает камеру %d", cameraID)
	}

	info.mux.Lock()
	info.viewCount--
	info.mux.Unlock()

	if info.viewCount == 0 {
		fmt.Printf("Остановка трансляции RTSP потока для камеры %d\n", cameraID)
		if err := info.process.Process.Kill(); err != nil {
			return err
		}
		delete(streams, strconv.Itoa(cameraID))

		err := os.RemoveAll(filepath.Join("streams", "camera_"+strconv.Itoa(cameraID)))
		if err != nil {
			return err
		}
	} else {
		fmt.Printf("Уменьшено количество просматривающих трансляцию RTSP потока для камеры %d до %d\n", cameraID, info.viewCount)
	}

	return nil
}

type Camera struct {
	ID        int    `json:"id"`
	Name      string `json:"name"`
	StreamURL string `json:"streamurl"`
	Location  string `json:"location"`
}

func get_camera(id int, db *sql.DB) (Camera, error) {
	query := "SELECT id, name, stream_url, location FROM cameras WHERE id = $1"

	row := db.QueryRow(query, id)

	var camera Camera

	err := row.Scan(&camera.ID, &camera.Name, &camera.StreamURL, &camera.Location)
	if err != nil {
		return Camera{}, err
	}

	return camera, nil
}

// func AllowOnlyLocalhost(c *gin.Context) {
// 	remoteAddr := c.Request.RemoteAddr
// 	if !strings.HasPrefix(remoteAddr, "127.0.0.1:8000") && !strings.HasPrefix(remoteAddr, "[::1]:8000") {
// 		c.JSON(http.StatusForbidden, gin.H{"error": "Доступ разрешён только с localhost:8000"})
// 		c.Abort()
// 		return
// 	}

// 	c.Next()
// }

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatalf("Ошибка загрузки файла .env: %v", err)
	}

	dbHost := os.Getenv("DB_HOST")
	dbPort := os.Getenv("DB_PORT")
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASS")
	dbName := os.Getenv("DB_NAME")
	dbSSLMode := os.Getenv("DB_SSLMODE")

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
		dbHost, dbPort, dbUser, dbPassword, dbName, dbSSLMode)

	db, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatalf("Ошибка подключения к базе данных: %v", err)
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		log.Fatalf("Не удалось подключиться к базе данных: %v", err)
	}
	fmt.Println("Успешное подключение к базе данных")

	r := gin.Default()

	// r.Use(AllowOnlyLocalhost)
	r.StaticFile("/", "./index.html")
	r.StaticFS("/streams", http.Dir("./streams"))

	r.POST("/start/:cameraID", func(c *gin.Context) {
		cameraIDStr := c.Param("cameraID")
		cameraID, err := strconv.Atoi(cameraIDStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Неверный ID камеры"})
			return
		}

		camera, err := get_camera(cameraID, db)
		if err != nil {
			if err == sql.ErrNoRows {
				c.JSON(http.StatusNotFound, gin.H{"error": "Камера не найдена"})
			} else {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "Ошибка при получении камеры"})
			}
			return
		}

		stream_url, err := DecryptStreamURL(camera.StreamURL, EncryptionKey)
		if err != nil {
			log.Fatalf("Ошибка при дешифровании ссылки на rtsp поток %v", err)
		}
		if err := startFFMPEG(camera.ID, stream_url); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"message": "Запущена трансляция RTSP потока камеры " + camera.Location})
	})

	r.POST("/stop/:cameraID", func(c *gin.Context) {
		cameraIDStr := c.Param("cameraID")
		cameraID, err := strconv.Atoi(cameraIDStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Неверный ID камеры"})
			return
		}
		if err := stopFFMPEG(cameraID); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"message": "Остановлена трансляция RTSP потока камеры " + strconv.Itoa(cameraID)})
	})

	r.Run("localhost:8080")
}
