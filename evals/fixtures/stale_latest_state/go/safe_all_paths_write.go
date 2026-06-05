package session

// Both branches update s.latest (an explicit empty result on failure), so a
// reader always reflects the most recent Run.
func (s *Session) Run(q string) (Result, error) {
	r, err := execute(q)
	if err != nil {
		s.latest = Result{Empty: true}
		return r, err
	}
	s.latest = r
	return r, nil
}

func (s *Session) RepeatLatest(p Plan) Result {
	return apply(p, s.latest)
}
