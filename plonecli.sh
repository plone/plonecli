_plonecli_completion() {
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   _PLONECLI_COMPLETE=complete $1 ) )
    return 0
}

complete -F _plonecli_completion -o default plonecli;
