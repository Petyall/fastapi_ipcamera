package models

type Camera struct {
	ID        int    `json:"id"`
	Name      string `json:"name"`
	StreamURL string `json:"streamurl"`
	Location  string `json:"location"`
}
