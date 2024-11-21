package middleware

import (
	"errors"
	"log"
	"net/http"
	"rtsp_streamer/config"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v4"
)

var SECRET_KEY = []byte(config.GetEnv("SECRET_KEY"))

func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		log.Println("AuthMiddleware - Пользователь начал авторизацию")
		// Извлечение токена из заголовка Authorization
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
			log.Println("AuthMiddleware - Токен отсутствует либо неверный")
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Токен отсутствует или неверен"})
			return
		}
		log.Println("AuthMiddleware - Найден JWT токен")

		tokenString := strings.TrimPrefix(authHeader, "Bearer ")
		token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
			// Проверка алгоритма подписи
			if token.Method != jwt.SigningMethodHS256 {
				log.Println("AuthMiddleware - В токене неподдерживаемый метод подписи")
				return nil, errors.New("неподдерживаемый метод подписи")
			}
			log.Println("AuthMiddleware - В токене подходящая подпись")
			return SECRET_KEY, nil
		})

		if err != nil || !token.Valid {
			log.Printf("AuthMiddleware - Ошибка при проверке токена %s", err)
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Недействительный токен"})
			return
		}
		log.Println("AuthMiddleware - Токен проверен успешно")

		// Проверка срока действия токена
		if claims, ok := token.Claims.(jwt.MapClaims); ok {
			exp, ok := claims["exp"].(float64)
			if !ok || time.Now().Unix() > int64(exp) {
				log.Println("AuthMiddleware - Срок действия токена истёк")
				c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Токен истёк"})
				return
			}

			// Сохранение user_id в контексте для дальнейшего использования
			c.Set("user_id", claims["sub"])
			log.Printf("AuthMiddleware - Успешно авторизирован пользователь %d", claims["sub"])
		} else {
			log.Println("AuthMiddleware - Неверный формат токена")
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Неверный формат токена"})
			return
		}

		c.Next()
	}
}
