#!/usr/bin/env bash

setup_hooks(){
    mkdir -p ditdir/HOOKS

    for f in before after; do
        for s in "" _read _write; do
            touch ditdir/HOOKS/$f$s
            echo '#!/usr/bin/env bash' > ditdir/HOOKS/$f$s
            echo 'echo '$f$s': $@' >> ditdir/HOOKS/$f$s
            echo 'exit 1' >> ditdir/HOOKS/$f$s
            chmod +x ditdir/HOOKS/$f$s
        done
    done
}

echo '---------------------------------------------------'
echo "$ setup_hooks"
setup_hooks

./ditcmd workon ././t1

./ditcmd list ././t1

./ditcmd --no-hooks list ././t1

./ditcmd --check-hooks list ././t1