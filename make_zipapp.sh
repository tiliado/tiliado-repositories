#!/bin/sh
set -eux
ZIPAPP_NAME=tiliado-repositories.pyz
rm -f app.zip __main__.py
cp tiliado-repositories __main__.py
zip app.zip -9 -r tiliadoweb __main__.py
echo '#!/usr/bin/env python3' | cat - app.zip > ../"$ZIPAPP_NAME"
chmod 755 ../"$ZIPAPP_NAME"
rm -f app.zip __main__.py
