#!/bin/bash
  
# git clone 
echo "<---git clone repo--->"
cd /home/ && git clone $GIT_ADDRESS; dir=$(echo $GIT_ADDRESS | rev | cut -d'/' -f 1 | rev | cut -d '.' -f1)

# modify Dockerfile
echo "<---modify Dockerfile--->"
cd /home/$dir && echo "RUN ls" >> Dockerfile

# config git
echo "<---config git--->"
git config --global user.email $GIT_EMAIL
git config --global user.name $GIT_USER

echo "https://$GIT_USER:$GIT_PASS@github.com" >> ~/.git-credentials
git config credential.helper store

# git push
echo "<---git push--->"
git add .
git commit -m "update"
git push
