package main

import (
	"log"
	"net/http"
	"os"
)

func main() {
	http.Handle("/", http.FileServer(http.Dir("/")))
	err := http.ListenAndServe("", nil)
	log.Println(err)
	if err != http.ErrServerClosed {
		os.Exit(1)
	}
}
