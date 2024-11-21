package services

import (
	"database/sql"
	"rtsp_streamer/models"
)

func GetCamera(id int, db *sql.DB) (models.Camera, error) {
	query := "SELECT id, name, stream_url, location FROM cameras WHERE id = $1"

	row := db.QueryRow(query, id)

	var camera models.Camera

	err := row.Scan(&camera.ID, &camera.Name, &camera.StreamURL, &camera.Location)
	if err != nil {
		return models.Camera{}, err
	}

	return camera, nil
}

func CheckUserCamera(camera_id int, user_id string, db *sql.DB) (bool, error) {
	query := "SELECT camera_id FROM user_cameras WHERE camera_id = $1 AND user_id = $2"

	row := db.QueryRow(query, camera_id, user_id)

	err := row.Scan(&camera_id)
	if err != nil {
		return false, err
	}

	return true, nil
}
