adb forward tcp:8080 tcp:8080
screen -S gnirehtet -dm bash -c 'gnirehtet run; exec sh'
screen -S socat -dm socat tcp-listen:8081,reuseaddr,fork tcp:localhost:8080
