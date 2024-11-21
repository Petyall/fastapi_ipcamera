package services

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"sync"
	"time"
)

type streamInfo struct {
	process *exec.Cmd
	viewers map[string]bool // Уникальные ID зрителей
	mux     sync.Mutex      // Защита данных о процессе и зрителях
}

var (
	streams       = make(map[string]*streamInfo)
	mux           sync.RWMutex
	activeViewers = make(map[string]int) // viewerID -> cameraID
)

func StartFFMPEG(cameraID int, streamURL, viewerID string) error {
	mux.Lock()

	// Проверяем, смотрит ли пользователь другой поток
	if oldCameraID, watching := activeViewers[viewerID]; watching && oldCameraID != cameraID {
		log.Printf("StartFFMPEG - Пользователь %s уже смотрит поток камеры %d, отключаем...\n", viewerID, oldCameraID)
		mux.Unlock() // Освобождаем мьютекс для вызова stopFFMPEG
		if err := StopFFMPEG(oldCameraID, viewerID); err != nil {
			log.Printf("StartFFMPEG - Не удалось отключить пользователя %s от камеры %d: %v", viewerID, oldCameraID, err)
			return fmt.Errorf("ошибка отключения зрителя %s от камеры %d: %v", viewerID, oldCameraID, err)
		}
		mux.Lock() // Возвращаем блокировку для продолжения
	}

	info, exists := streams[strconv.Itoa(cameraID)]
	if exists {
		info.mux.Lock()
		defer info.mux.Unlock()

		// Проверяем, запущен ли процесс
		if info.process != nil && info.process.ProcessState == nil {
			if _, alreadyViewing := info.viewers[viewerID]; !alreadyViewing {
				info.viewers[viewerID] = true
				log.Printf("StartFFMPEG - Пользователь %s присоединился к просмотру RTSP потока %d\n", viewerID, cameraID)
				activeViewers[viewerID] = cameraID
			} else {
				log.Printf("StartFFMPEG - Пользователь %s уже подключен к RTSP потоку %d\n", viewerID, cameraID)
			}
			mux.Unlock()
			return nil
		}

		// Процесс завершился или неактивен
		log.Printf("StartFFMPEG - Перезапуск трансляции RTSP потока камеры %d\n", cameraID)
		info.viewers = make(map[string]bool) // Очистка списка зрителей
	}

	log.Printf("StartFFMPEG - Начало трансляции RTSP потока камеры %d\n", cameraID)

	dirPath := filepath.Join("streams", "camera_"+strconv.Itoa(cameraID))
	if err := os.MkdirAll(dirPath, os.ModePerm); err != nil {
		log.Printf("StartFFMPEG - Ошибка при работе с директориями %v", err)
		mux.Unlock()
		return err
	}

	cmd := exec.Command("ffmpeg", "-i", streamURL, "-c:v", "libx264", "-preset",
		"ultrafast", "-b:v", "500k", "-s", "640x360", "-f", "hls", "-hls_time",
		"2", "-hls_list_size", "10", "-hls_flags", "delete_segments",
		"./streams/camera_"+strconv.Itoa(cameraID)+"/index.m3u8")

	if err := cmd.Start(); err != nil {
		log.Printf("StartFFMPEG - Ошибка при запуске потока %v", err)
		mux.Unlock()
		return err
	}

	if !exists {
		streams[strconv.Itoa(cameraID)] = &streamInfo{
			process: cmd,
			viewers: map[string]bool{viewerID: true},
		}
	} else {
		info.process = cmd
		info.viewers = map[string]bool{viewerID: true}
	}

	activeViewers[viewerID] = cameraID
	mux.Unlock()

	filePath := "./streams/camera_" + strconv.Itoa(cameraID) + "/index.m3u8"
	log.Printf("StartFFMPEG - Начало ожидания создания файла ./streams/camera_%s/index.m3u8", strconv.Itoa(cameraID))
	for i := 0; i < 30; i++ {
		log.Printf("StartFFMPEG - Для файла ./streams/camera_%s/index.m3u8 прошло %d секунд", strconv.Itoa(cameraID), i)
		if _, err := os.Stat(filePath); err == nil {
			break
		}
		time.Sleep(time.Second)
	}

	if _, err := os.Stat(filePath); err != nil {
		log.Printf("StartFFMPEG - Для файла ./streams/camera_%s/index.m3u8 превышено время ожидания", strconv.Itoa(cameraID))
		return fmt.Errorf("время ожидания для файла %s превышено", filePath)
	}

	return nil
}

func StopFFMPEG(cameraID int, viewerID string) error {
	mux.Lock()
	defer mux.Unlock()

	info, exists := streams[strconv.Itoa(cameraID)]
	if !exists {
		log.Printf("StopFFMPEG - Камера %d не активна", cameraID)
		return fmt.Errorf("камера %d не активна", cameraID)
	}

	info.mux.Lock()
	defer info.mux.Unlock()

	// Удаляем зрителя
	if _, viewerExists := info.viewers[viewerID]; viewerExists {
		delete(info.viewers, viewerID)
		delete(activeViewers, viewerID)
		log.Printf("StopFFMPEG - Пользователь %s отключился от камеры %d\n", viewerID, cameraID)
	} else {
		log.Printf("StopFFMPEG - Пользователь %s не найден в списке зрителей для камеры %d", viewerID, cameraID)
		return fmt.Errorf("пользователь %s не найден в списке для камеры %d", viewerID, cameraID)
	}

	// Проверяем количество оставшихся зрителей
	if len(info.viewers) == 0 {
		log.Printf("StopFFMPEG - Остановка трансляции RTSP потока для камеры %d (нет зрителей)\n", cameraID)
		if err := info.process.Process.Kill(); err != nil {
			return err
		}
		delete(streams, strconv.Itoa(cameraID))

		// Удаляем временные файлы трансляции
		err := os.RemoveAll(filepath.Join("streams", "camera_"+strconv.Itoa(cameraID)))
		if err != nil {
			return err
		}
	} else {
		log.Printf("StopFFMPEG - Количество зрителей камеры %d уменьшено до %d\n", cameraID, len(info.viewers))
	}

	return nil
}
