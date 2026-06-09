package api

import "net/http"

// Two sibling response writers for the same endpoint. okResponse sets the
// X-Request-Id correlation header; errorResponse omits it, so failures can't be
// correlated in logs the way successes can. Same concept, one branch leaves the
// shared field blank — the divergence is the bug.

func okResponse(w http.ResponseWriter, requestID string, body any) {
	w.Header().Set("X-Request-Id", requestID)
	writeJSON(w, http.StatusOK, body)
}

func errorResponse(w http.ResponseWriter, requestID string, err error) {
	writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
}
