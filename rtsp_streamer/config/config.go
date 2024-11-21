package config

import (
	"os"

	"github.com/joho/godotenv"
)

func LoadEnv() error {
	return godotenv.Load(".env")
}

func GetEnv(key string) string {
	value := os.Getenv(key)
	return value
}
