package main

import (
	"errors"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v4"
)

var SECRET_KEY = []byte(os.Getenv("SECRET_KEY"))

func AuthMiddleware() gin.HandlerFunc {
	fmt.Println("Используем секретный ключ:", SECRET_KEY)
	return func(c *gin.Context) {
		// Извлечение токена из заголовка Authorization
		authHeader := c.GetHeader("Authorization")
		fmt.Println("Заголовок авторизации:", authHeader)
		if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Токен отсутствует или неверен"})
			return
		}

		tokenString := strings.TrimPrefix(authHeader, "Bearer ")
		fmt.Println("Токен:", tokenString)
		token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
			// Проверка алгоритма подписи
			if token.Method != jwt.SigningMethodHS256 {
				return nil, errors.New("неподдерживаемый метод подписи")
			}
			return SECRET_KEY, nil
		})

		if err != nil || !token.Valid {
			fmt.Println("Ошибка при проверке токена:", err)
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Недействительный токен"})
			return
		}
		fmt.Println("Токен проверен успешно")

		// Проверка срока действия токена
		if claims, ok := token.Claims.(jwt.MapClaims); ok {
			exp, ok := claims["exp"].(float64)
			if !ok || time.Now().Unix() > int64(exp) {
				c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Токен истёк"})
				return
			}

			// Сохранение user_id в контексте для дальнейшего использования
			c.Set("user_id", claims["sub"])
			fmt.Println("Пользователь записан в контекст")
		} else {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Неверный формат токена"})
			return
		}

		c.Next()
	}
}
