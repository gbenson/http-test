package main

import (
	"log"
	"net/http"
	"os"
)

const defaultServerHeader = "gbenson-httptest-golang/1.0"

func main() {
	http.Handle("/", ServerHeaderSetter(http.FileServer(http.Dir("/"))))
	err := http.ListenAndServe("", nil)
	log.Println(err)
	if err != http.ErrServerClosed {
		os.Exit(1)
	}
}

func ServerHeaderSetter(handler http.Handler) http.Handler {
	return HeaderSetter("Server", defaultServerHeader, handler)
}

func HeaderSetter(key, value string, handler http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		h := w.Header()
		if h.Get(key) == "" {
			h.Set(key, value)
		}
		handler.ServeHTTP(w, r)
	})
}
