g++ -c -fPIC fiveswapminer.cpp -Wall -O2 -march=skylake -o fiveswapminer.o
g++ -shared -Wl,-soname,libfiveswapminer.so -o libfiveswapminer.so fiveswapminer.o
