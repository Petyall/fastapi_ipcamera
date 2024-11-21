package services

import (
	"crypto/aes"
	"crypto/cipher"
	"encoding/base64"
	"errors"
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"
)

var EncryptionKey []byte

func init() {
	// Загружаем переменные из .env
	err := godotenv.Load()
	if err != nil {
		log.Fatalf("Ошибка загрузки файла .env: %v", err)
	}

	// Считываем закодированный ключ из переменной окружения
	base64Key := os.Getenv("DECRYPTION_KEY")
	if base64Key == "" {
		log.Fatal("Ключ дешифрования (DECRYPTION_KEY) не найден в .env")
	}

	// Декодируем ключ из Base64
	decodedKey, err := base64.StdEncoding.DecodeString(base64Key)
	if err != nil {
		log.Fatalf("Ошибка декодирования ключа из Base64: %v", err)
	}

	// Проверяем длину ключа
	if len(decodedKey) != 32 {
		log.Fatal("Декодированный ключ дешифрования должен быть длиной 32 байта (AES-256)")
	}

	EncryptionKey = decodedKey
}

// DecryptStreamURL - функция для дешифрования
func DecryptStreamURL(encryptedStreamURL string, key []byte) (string, error) {
	// Декодируем данные из Base64
	encryptedData, err := base64.StdEncoding.DecodeString(encryptedStreamURL)
	if err != nil {
		return "", fmt.Errorf("ошибка декодирования Base64: %v", err)
	}

	// Разделяем IV и зашифрованный URL
	if len(encryptedData) < aes.BlockSize {
		return "", errors.New("длина данных меньше размера блока AES")
	}
	iv := encryptedData[:aes.BlockSize]
	encryptedURL := encryptedData[aes.BlockSize:]

	// Инициализируем блок AES
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("ошибка создания AES блока: %v", err)
	}

	// Инициализируем режим CBC для расшифровки
	cipherBlock := cipher.NewCBCDecrypter(block, iv)

	// Расшифровываем данные
	decryptedPaddedURL := make([]byte, len(encryptedURL))
	cipherBlock.CryptBlocks(decryptedPaddedURL, encryptedURL)

	// Убираем PKCS7 паддинг
	decryptedURL, err := pkcs7Unpad(decryptedPaddedURL, aes.BlockSize)
	if err != nil {
		return "", fmt.Errorf("ошибка удаления паддинга: %v", err)
	}

	return string(decryptedURL), nil
}

func pkcs7Unpad(data []byte, blockSize int) ([]byte, error) {
	if len(data) == 0 || len(data)%blockSize != 0 {
		return nil, errors.New("некорректный размер данных для удаления паддинга")
	}

	padLen := int(data[len(data)-1])
	if padLen > blockSize || padLen == 0 {
		return nil, errors.New("некорректная длина паддинга")
	}

	return data[:len(data)-padLen], nil
}
