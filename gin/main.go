package main

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

type streamInfo struct {
	process   *exec.Cmd
	viewCount int
	mux       sync.Mutex
}

var (
	streams = make(map[string]*streamInfo)
	mux     sync.RWMutex
)

func startFFMPEG(cameraIP string) error {
	mux.RLock()
	info, exists := streams[cameraIP]
	mux.RUnlock()

	if exists && info.viewCount > 0 {
		info.mux.Lock()
		info.viewCount++
		info.mux.Unlock()
		fmt.Printf("К просмотру RTSP потока %s присоединился новый человек\n", cameraIP)
		return nil
	}

	if exists {
		fmt.Printf("Перезапуск трансляции RTSP потока камеры %s\n", cameraIP)
	} else {
		fmt.Printf("Начало трансляции RTSP потока камеры %s\n", cameraIP)
	}

	dirPath := filepath.Join("streams", "camera_"+cameraIP)
	if err := os.MkdirAll(dirPath, os.ModePerm); err != nil {
		return err
	}

	cmd := exec.Command("ffmpeg", "-i", "rtsp://user:password@"+cameraIP+":554/RVi/1/2", "-c:v", "libx264", "-preset",
		"ultrafast", "-b:v", "500k", "-s", "640x360", "-f", "hls", "-hls_time",
		"2", "-hls_list_size", "10", "-hls_flags", "delete_segments",
		"./streams/camera_"+cameraIP+"/index.m3u8")

	if err := cmd.Start(); err != nil {
		return err
	}

	mux.Lock()
	if !exists {
		streams[cameraIP] = &streamInfo{
			process:   cmd,
			viewCount: 1,
		}
	} else {
		info.process = cmd
		info.viewCount = 1
	}
	mux.Unlock()

	filePath := "./streams/camera_" + cameraIP + "/index.m3u8"
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

func stopFFMPEG(cameraIP string) error {
	mux.Lock()
	defer mux.Unlock()

	info, exists := streams[cameraIP]
	if !exists || info.viewCount <= 0 {
		return fmt.Errorf("в данный момент никто не просматривает камеру %s", cameraIP)
	}

	info.mux.Lock()
	info.viewCount--
	info.mux.Unlock()

	if info.viewCount == 0 {
		fmt.Printf("Остановка трансляции RTSP потока для камеры %s\n", cameraIP)
		if err := info.process.Process.Kill(); err != nil {
			return err
		}
		delete(streams, cameraIP)

		err := os.RemoveAll(filepath.Join("streams", "camera_"+cameraIP))
		if err != nil {
			return err
		}
	} else {
		fmt.Printf("Уменьшено количество просматривающих трансляцию RTSP потока для камеры %s до %d\n", cameraIP, info.viewCount)
	}

	return nil
}

func main() {
	r := gin.Default()

	r.StaticFile("/", "./index.html")
	r.StaticFS("/streams", http.Dir("./streams"))

	r.POST("/start/:cameraIP", func(c *gin.Context) {
		cameraIP := c.Param("cameraIP")
		if err := startFFMPEG(cameraIP); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"message": "Запущена трансляция RTSP потока камеры " + cameraIP})
	})

	r.POST("/stop/:cameraIP", func(c *gin.Context) {
		cameraIP := c.Param("cameraIP")
		if err := stopFFMPEG(cameraIP); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"message": "Остановлена трансляция RTSP потока камеры " + cameraIP})
	})

	r.Run(":8080")
}
