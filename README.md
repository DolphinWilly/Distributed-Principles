# Distributed-Principles

Project Structure:

(Note: currently I don't have a goal of what my distributed system should be used for,
so the construction of this project is not led by functional purposes (e.g. a chatroom,
a music playlist, a backup like dropbox etc.). This project is instead led through what Principles
are important in a distributed system and what are a fabulous thing to be achieved in a
distributed system. Therefore I will include all those intriguing thing, theory and practice into
this project.)

Technical Trivia:

to kill all processes listening on a specific port:

lsof -n -i4TCP:[PORT] | grep LISTEN | awk '{ print $2 }' | xargs kill
