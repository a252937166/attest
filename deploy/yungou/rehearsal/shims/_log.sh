# Sourced by every shim: append the call to the rehearsal call log (REHEARSAL_DIR/logs/shim-calls.log).
shim_log() {
  if [ -n "${REHEARSAL_DIR:-}" ]; then
    mkdir -p "$REHEARSAL_DIR/logs"
    printf '%s %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" >> "$REHEARSAL_DIR/logs/shim-calls.log"
  fi
}
