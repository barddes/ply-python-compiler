int n = 3;

int doubleMe (int x, int y, int z) {
    return x * x;
}

void main () {
    int v = n;
    v = doubleMe (v);
    print(2, v+2);
    return;
}

