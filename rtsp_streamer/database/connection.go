package database

import (
	"database/sql"
	"fmt"
	"rtsp_streamer/config"

	_ "github.com/lib/pq"
)

func Connect() (*sql.DB, error) {
	dbHost := config.GetEnv("DB_HOST")
	dbPort := config.GetEnv("DB_PORT")
	dbUser := config.GetEnv("DB_USER")
	dbPassword := config.GetEnv("DB_PASS")
	dbName := config.GetEnv("DB_NAME")
	dbSSLMode := config.GetEnv("DB_SSLMODE")

	connStr := fmt.Sprintf(
		"host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
		dbHost, dbPort, dbUser, dbPassword, dbName, dbSSLMode,
	)

	return sql.Open("postgres", connStr)
}
