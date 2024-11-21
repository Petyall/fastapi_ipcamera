package routes

import (
	"database/sql"
	"net/http"
	"rtsp_streamer/controllers"
	"rtsp_streamer/middleware"

	"github.com/gin-gonic/gin"
)

func RegisterRoutes(r *gin.Engine, db *sql.DB) {
	r.StaticFS("/streams", http.Dir("./streams"))

	cameraRoutes := r.Group("/")
	{
		cameraRoutes.POST("/start/:cameraID", middleware.AuthMiddleware(), func(c *gin.Context) {
			controllers.StartCameraStream(c, db)
		})
		cameraRoutes.POST("/stop/:cameraID", middleware.AuthMiddleware(), func(c *gin.Context) {
			controllers.StopCameraStream(c, db)
		})
	}
}
