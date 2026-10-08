_cfdns_completion() {
  local current previous command types
  COMPREPLY=()
  current=${COMP_WORDS[COMP_CWORD]}
  previous=${COMP_WORDS[COMP_CWORD-1]}
  command=${COMP_WORDS[1]:-}
  types='A AAAA CAA CNAME MX NS PTR SRV TXT'

  if (( COMP_CWORD == 1 )); then
    mapfile -t COMPREPLY < <(compgen -W 'help list get add set rm' -- "$current")
    return
  fi
  if [[ $previous == --ttl ]]; then
    mapfile -t COMPREPLY < <(compgen -W '1 60 120 300 600 3600' -- "$current")
    return
  fi
  case $command in
    list)
      if (( COMP_CWORD == 2 )); then
        mapfile -t COMPREPLY < <(compgen -W "$types --plain" -- "$current")
      else
        mapfile -t COMPREPLY < <(compgen -W '--plain' -- "$current")
      fi ;;
    get)
      if (( COMP_CWORD >= 3 )); then
        mapfile -t COMPREPLY < <(compgen -W '--plain' -- "$current")
      fi ;;
    add|set|rm)
      if (( COMP_CWORD == 2 )); then
        mapfile -t COMPREPLY < <(compgen -W "$types" -- "$current")
      elif [[ $command == rm ]] && (( COMP_CWORD >= 4 )); then
        mapfile -t COMPREPLY < <(compgen -W '--yes' -- "$current")
      elif [[ $command != rm ]] && (( COMP_CWORD >= 5 )); then
        mapfile -t COMPREPLY < <(compgen -W '--proxy --ttl' -- "$current")
      fi ;;
  esac
}

complete -F _cfdns_completion cfdns
