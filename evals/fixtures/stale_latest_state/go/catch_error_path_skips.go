package session

// Run updates s.latest on success, but the error early-return skips it. A reader
// using s.latest after a failed Run replays the previous successful result.
func (s *Session) Run(q string) (Result, error) {
	r, err := execute(q)
	if err != nil {
		return Result{}, err // returns without updating s.latest
	}
	s.latest = r
	return r, nil
}

func (s *Session) RepeatLatest(p Plan) Result {
	return apply(p, s.latest) // stale after a failed Run
}
