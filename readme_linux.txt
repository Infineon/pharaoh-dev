- Install firefox: sudo apt install firefox

    If problems arise:
        https://askubuntu.com/questions/1444962/how-do-i-install-firefox-in-wsl-when-it-requires-snap-but-snap-doesnt-work/1444967#1444967

        sudo snap remove firefox
        sudo apt remove firefox
        sudo add-apt-repository ppa:mozillateam/ppa
        # Create a new file, it should be empty as it opens:
        sudo nano /etc/apt/preferences.d/mozillateamppa
        # Insert these lines, then save and exit
        Package: firefox*
        Pin: release o=LP-PPA-mozillateam
        Pin-Priority: 501
        # after saving, do
        sudo apt update
        sudo apt install firefox # or firefox-esr


- Install geckodriver:
    -   Download lastest geckodriver-*-linux64.tar.gz from
        https://github.com/mozilla/geckodriver/releases
    -   Unzip: tar -xzf geckodriver-v...tar-gz
    -   Move to bin: mv geckodriver /usr/bin
