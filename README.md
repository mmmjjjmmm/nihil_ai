

step 1 :
install wsl
PS > wsl --install

step 2 :
install nvm puis node.js on wsl  
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20

step 3 :
install claude code
npm install -g @anthropic-ai/claude-code  

step 4 : 
configure github
add github repo to the list of repos for apt
sudo mkdir -p -m 755 /etc/apt/keyrings && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg

apt update

apt install gh -y

gh auth login
