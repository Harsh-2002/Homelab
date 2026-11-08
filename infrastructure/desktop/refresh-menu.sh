#!/bin/sh
export XDG_RUNTIME_DIR=/run/user/0
/usr/bin/kbuildsycoca6 --noincremental >/dev/null 2>&1
exit 0
